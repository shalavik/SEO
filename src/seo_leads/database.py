"""
Database configuration and connection management for UK Company SEO Lead Generation System

Provides session management, migrations, and connection pooling for optimal performance.
"""

import os
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool
from .models import Base, UKCompany, ProcessingStatus

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration with connection pooling and optimization"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.environ.get(
            'DATABASE_URL', 
            'sqlite:///./uk_company_leads.db'
        )
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        # Configure SQLite with optimizations
        if self.database_url.startswith('sqlite'):
            connect_args = {
                'check_same_thread': False,
                'timeout': 60,
                'isolation_level': None  # Autocommit mode
            }
            
            self.engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                echo=False,  # Set to True for debugging
                future=True
            )
            
            # Enable SQLite optimizations
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                # Performance optimizations
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute("PRAGMA cache_size = 10000")
                cursor.execute("PRAGMA temp_store = MEMORY") 
                cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.close()
                
        else:
            # PostgreSQL/MySQL configuration with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        )
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
            # Initialize processing status tracking
            self._initialize_processing_status()
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def _initialize_processing_status(self):
        """Initialize processing status tracking table"""
        try:
            with self.get_session() as session:
                # Check if processing status records exist
                existing = session.query(ProcessingStatus).first()
                
                if not existing:
                    # Initialize status tracking for each stage
                    stages = [
                        'scraping', 'contact_extraction', 'seo_analysis', 
                        'lead_qualification', 'export'
                    ]
                    
                    for stage in stages:
                        status = ProcessingStatus(
                            stage=stage,
                            total_companies=0,
                            processed_companies=0,
                            failed_companies=0,
                            success_rate=0.0
                        )
                        session.add(status)
                    
                    session.commit()
                    logger.info("Processing status tracking initialized")
                    
        except Exception as e:
            logger.error(f"Error initializing processing status: {e}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()

# Global database instance
db_config = None

def initialize_database(database_url: Optional[str] = None) -> DatabaseConfig:
    """Initialize global database configuration"""
    global db_config
    
    if db_config is None:
        db_config = DatabaseConfig(database_url)
        db_config.create_tables()
        logger.info("Database initialized successfully")
    
    return db_config

def get_database() -> DatabaseConfig:
    """Get current database configuration"""
    global db_config
    
    if db_config is None:
        db_config = initialize_database()
    
    return db_config

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    db = get_database()
    with db.get_session() as session:
        yield session

def get_processing_metrics() -> dict:
    """Get current processing metrics from database"""
    try:
        with get_db_session() as session:
            # Get overall company counts
            total_companies = session.query(UKCompany).count()
            processed_companies = session.query(UKCompany).filter(
                UKCompany.status.in_(['qualified', 'exported'])
            ).count()
            
            # Get status breakdown
            status_breakdown = {}
            for status in ['scraped', 'contacts_extracted', 'seo_analyzed', 'qualified', 'exported', 'failed']:
                count = session.query(UKCompany).filter(UKCompany.status == status).count()
                status_breakdown[status] = count
            
            # Get stage metrics
            stage_metrics = {}
            stage_records = session.query(ProcessingStatus).all()
            for record in stage_records:
                stage_metrics[record.stage] = {
                    'total': record.total_companies,
                    'processed': record.processed_companies,
                    'failed': record.failed_companies,
                    'success_rate': record.success_rate,
                    'last_updated': record.last_updated.isoformat() if record.last_updated else None
                }
            
            return {
                'total_companies': total_companies,
                'processed_companies': processed_companies,
                'status_breakdown': status_breakdown,
                'stage_metrics': stage_metrics,
                'overall_success_rate': (processed_companies / total_companies * 100) if total_companies > 0 else 0
            }
            
    except Exception as e:
        logger.error(f"Error getting processing metrics: {e}")
        return {} 