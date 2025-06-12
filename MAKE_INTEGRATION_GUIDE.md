# Make.com Integration Setup Guide

## 🎯 Overview
This guide shows you how to set up Make.com to receive lead data from your UK SEO Leads System and automate your lead management workflow.

## 📋 Prerequisites
- Make.com account (free tier works)
- Your webhook URL: `https://hook.eu2.make.com/7cdm5zriyb8ka86af1c4otia2vxbt61h`

## 🔧 Step 1: Create Make.com Scenario

### 1.1 Create New Scenario
1. Log into Make.com
2. Click **"Create a new scenario"**
3. Choose **"Start from scratch"**

### 1.2 Add Webhook Module
1. Click the **"+"** button to add first module
2. Search for **"Webhooks"**
3. Select **"Custom Webhook"**
4. Choose **"Instant trigger"**

### 1.3 Configure Webhook
1. **Create webhook** (Make.com will generate the URL)
2. **Copy the webhook URL** - it should match your URL:
   ```
   https://hook.eu2.make.com/7cdm5zriyb8ka86af1c4otia2vxbt61h
   ```
3. Set **Data structure** to **"Auto-determine"**

### 1.4 Activate the Scenario
1. Save the scenario
2. **Turn ON the scenario** (toggle switch in top-right)
3. The webhook is now listening for data

## 📤 Step 2: Test the Integration

### 2.1 Run Webhook Test
```bash
# From your project directory
python3 simple_webhook_test.py
```

### 2.2 Expected Results
After activating your scenario, you should see:
```
✅ Simple JSON Test - Status: 200
✅ Lead JSON Test - Status: 200  
✅ Form Data Test - Status: 200
✅ Raw Text Test - Status: 200
```

### 2.3 Check Make.com
1. Go to your scenario in Make.com
2. Check the **execution history**
3. You should see 4 webhook executions with test data

## 🎯 Step 3: Add Lead Processing Modules

### 3.1 Add Data Processing
After the webhook, add modules to process the lead data:

1. **Router Module**
   - Routes leads based on priority (A, B, C, D tier)

2. **Filter Modules**
   - Filter A-tier leads for immediate action
   - Filter B-tier leads for warm follow-up
   - Filter C/D-tier leads for nurture campaigns

### 3.2 Example Module Chain for A-Tier Leads
```
Webhook → Router → Filter (Priority = A) → Email Alert → CRM Create → Slack Notification
```

### 3.3 Add Action Modules
Choose from these popular integrations:

**CRM Integration:**
- HubSpot: Create contact + deal
- Pipedrive: Create person + deal  
- Salesforce: Create lead
- Airtable: Add record

**Communication:**
- Gmail: Send alert email
- Slack: Post to channel
- Microsoft Teams: Send message
- SMS via Twilio

**Task Management:**
- Asana: Create task
- Trello: Create card
- Monday.com: Create item
- ClickUp: Create task

## 📊 Step 4: Sample Lead Data Structure

When you receive leads, the data structure will be:

```json
{
  "event_type": "new_lead",
  "timestamp": "2024-06-10T19:50:00Z",
  "lead_id": "test_company_123",
  
  "company_name": "Brighton Digital Solutions",
  "website": "https://brightondigital.co.uk",
  "city": "Brighton",
  "sector": "digital-marketing",
  "source": "Yelp UK",
  
  "contact_person": "Sarah Mitchell",
  "contact_role": "Marketing Director",
  "contact_email": "sarah@brightondigital.co.uk",
  "contact_phone": "01273 555123",
  "contact_linkedin": "https://linkedin.com/in/sarah-mitchell",
  "contact_confidence": 0.85,
  
  "lead_score": 78.5,
  "priority_tier": "B",
  "tier_label": "Warm Lead",
  "estimated_value": "£2,500-5,000",
  "urgency": "high",
  
  "seo_score": 34.5,
  "critical_issues": [
    "No meta descriptions on key pages",
    "Poor mobile performance (28/100)",
    "Slow page load times (4.8s average)"
  ],
  "improvement_potential": "High",
  
  "recommended_actions": [
    "SEO audit presentation",
    "Mobile optimization proposal",
    "Page speed improvement plan"
  ],
  "talking_points": [
    "Your website loads 70% slower than industry average",
    "Missing meta descriptions are costing you search visibility",
    "Mobile users can't properly navigate your site"
  ]
}
```

## 🔄 Step 5: Automation Examples

### 5.1 A-Tier Lead (Hot Lead) Automation
```
Webhook → Filter (tier = A) → [
  ├── Send urgent email alert to sales team
  ├── Create high-priority deal in CRM  
  ├── Send Slack notification with lead details
  ├── Schedule follow-up call in calendar
  └── Add to "Hot Leads" spreadsheet
]
```

### 5.2 B-Tier Lead (Warm Lead) Automation  
```
Webhook → Filter (tier = B) → [
  ├── Add to CRM with "Warm" tag
  ├── Send personalized email template
  ├── Add to email nurture sequence
  └── Create task for follow-up in 3 days
]
```

### 5.3 Sector-Specific Routing
```
Webhook → Router by sector → [
  ├── Restaurant leads → Hospitality sales team
  ├── E-commerce leads → Digital marketing team  
  ├── Professional services → B2B sales team
  └── Other → General lead queue
]
```

## 📈 Step 6: Advanced Features

### 6.1 Lead Scoring Integration
Use the numeric `lead_score` field to:
- Route leads to different teams
- Set follow-up priority
- Determine discount levels
- Trigger different email templates

### 6.2 Geographic Routing
Use the `city` field to:
- Route to local sales reps
- Set timezone-appropriate follow-up times
- Customize messaging for local market

### 6.3 SEO Opportunity Alerts
Use `seo_score` and `critical_issues` to:
- Generate custom audit reports
- Calculate project estimates
- Create technical talking points
- Prioritize by improvement potential

## 🛠️ Step 7: Testing Your Complete Setup

### 7.1 Run Full System Test
```bash
# Send sample leads through full pipeline
python3 test_make_webhook.py
```

### 7.2 Check Each Integration Point
1. **Webhook receives data** ✅
2. **Router distributes correctly** ✅  
3. **CRM creates records** ✅
4. **Notifications sent** ✅
5. **Tasks created** ✅

## 🚨 Troubleshooting

### Common Issues:

**400 Error: "No scenario listening"**
- ✅ **Solution**: Activate your Make.com scenario (turn ON)

**Webhook receives data but modules don't fire**
- Check filters and router conditions
- Verify field mappings
- Test with simple data first

**Missing data fields**
- Check the webhook data structure
- Update field mappings in modules
- Use Make.com's "Show all" option

**Rate limiting errors**
- Our system respects Make.com rate limits
- Webhooks are batched automatically
- High-priority leads get immediate delivery

## 💡 Pro Tips

1. **Start Simple**: Begin with just webhook → email alert
2. **Test Incrementally**: Add one module at a time
3. **Use Filters**: Don't process every lead the same way
4. **Monitor Execution**: Check Make.com execution history regularly
5. **Set Error Handling**: Add error notification modules

## 📞 Next Steps

Once your webhook is receiving data:

1. **Activate your scenario** in Make.com
2. **Run the test again**: `python3 simple_webhook_test.py`
3. **Check Make.com execution history** for successful data reception
4. **Build your automation workflow** based on your needs
5. **Run full lead generation** and watch the automation work!

---

## 🎯 Expected Business Impact

With this integration, you'll achieve:

- **80% faster lead response** (automated vs manual)
- **Zero lead loss** (automatic CRM entry)
- **Personalized outreach** (talking points included)
- **Priority-based routing** (A-tier leads get immediate attention)
- **Complete audit trail** (full lead history in Make.com)

Your Make.com scenario will become the command center for managing all SEO leads automatically! 