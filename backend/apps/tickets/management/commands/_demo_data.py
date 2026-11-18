"""Static demo data used by ``seed_demo``. Edit freely."""

DEMO_PASSWORD = "Demo@12345"

REQUESTERS = [
    {"username": "riya", "first_name": "Riya", "last_name": "Menon", "email": "riya.menon@example.com",
     "job_title": "Finance Executive", "role": "requester", "role_label": "Requester", "password": DEMO_PASSWORD},
    {"username": "karthik", "first_name": "Karthik", "last_name": "Raj", "email": "karthik.raj@example.com",
     "job_title": "Sales Manager", "role": "requester", "role_label": "Requester", "password": DEMO_PASSWORD},
    {"username": "emily", "first_name": "Emily", "last_name": "Carter", "email": "emily.carter@example.com",
     "job_title": "Operations Lead", "role": "requester", "role_label": "Requester", "password": DEMO_PASSWORD},
    {"username": "daniel", "first_name": "Daniel", "last_name": "Brooks", "email": "daniel.brooks@example.com",
     "job_title": "Data Analyst", "role": "requester", "role_label": "Requester", "password": DEMO_PASSWORD},
]

AGENTS = [
    {"username": "meera", "first_name": "Meera", "last_name": "Iyer", "email": "meera.iyer@example.com",
     "job_title": "Support Engineer", "role": "agent", "role_label": "Support Agent", "password": DEMO_PASSWORD},
    {"username": "sam", "first_name": "Sam", "last_name": "Wilson", "email": "sam.wilson@example.com",
     "job_title": "Senior Support Engineer", "role": "agent", "role_label": "Support Agent", "password": DEMO_PASSWORD},
]

ADMIN = {
    "username": "admin", "first_name": "Desk", "last_name": "Admin", "email": "admin@example.com",
    "job_title": "Support Lead", "role": "agent", "role_label": "Admin (agent)", "password": "Admin@12345",
    "is_staff": True, "is_superuser": True,
}

# status: open | in_progress | resolved
TICKETS = [
    {
        "title": "Cannot log in after resetting my password",
        "description": "I reset my password using the 'Forgot password' link this morning. The reset email "
                       "arrived and I set a new password, but the login page keeps saying 'Invalid credentials'.",
        "category": "login_access", "priority": "high", "status": "resolved", "requester": "riya",
        "agent": "meera", "days_ago": 41,
        "resolution": "The account was locked after five failed attempts before the reset. Unlocked the account "
                      "and confirmed the user can sign in with the new password. Lockouts now clear automatically "
                      "after a successful reset.",
    },
    {
        "title": "Charged twice for the monthly subscription",
        "description": "Our company card shows two identical charges for the Pro plan on the 1st of this month. "
                       "We only have one workspace. Please refund the duplicate payment.",
        "category": "billing", "priority": "high", "status": "resolved", "requester": "karthik",
        "agent": "sam", "days_ago": 38,
        "resolution": "The payment gateway retried a timed-out request and both attempts succeeded. Refunded the "
                      "duplicate charge; it will appear on the statement in 5-7 working days.",
    },
    {
        "title": "Dashboard takes more than a minute to load",
        "description": "Since Monday the analytics dashboard spins for over 60 seconds before showing anything. "
                       "Other pages are fine. It happens in Chrome and Edge.",
        "category": "performance", "priority": "medium", "status": "resolved", "requester": "emily",
        "agent": "meera", "days_ago": 35,
        "resolution": "A missing index on the events collection caused a full scan for large date ranges. Added "
                      "the index; the dashboard now loads in under three seconds for the default 30-day range.",
    },
    {
        "title": "Export to Excel shows wrong dates",
        "description": "When I export the monthly sales report to Excel, all the dates are shifted by one day. "
                       "The values on screen are correct.",
        "category": "data_reports", "priority": "medium", "status": "resolved", "requester": "daniel",
        "agent": "sam", "days_ago": 33,
        "resolution": "The export used UTC instead of the workspace time zone. Fixed in release 4.2.1; please "
                      "re-run the export. Old files need to be exported again.",
    },
    {
        "title": "Webhook deliveries failing with 401 Unauthorized",
        "description": "Our order webhook endpoint started returning 401 for every delivery yesterday. We did "
                       "not change anything on our side. The webhook log shows 'signature mismatch'.",
        "category": "integration", "priority": "critical", "status": "resolved", "requester": "karthik",
        "agent": "meera", "days_ago": 30,
        "resolution": "The signing secret was rotated when a teammate regenerated API keys. Shared the steps to "
                      "copy the new secret into the receiving service; deliveries are succeeding again.",
    },
    {
        "title": "Two-factor codes not accepted",
        "description": "The six digit code from my authenticator app is always rejected. I have tried several "
                       "times and waited for a new code each time.",
        "category": "login_access", "priority": "high", "status": "resolved", "requester": "emily",
        "agent": "sam", "days_ago": 28,
        "resolution": "The phone clock was about four minutes behind, so codes were already expired. Enabled "
                      "automatic time sync on the phone and codes are accepted now.",
    },
    {
        "title": "Invoice PDF is missing our GST number",
        "description": "The invoices we download do not show our GST registration number even though it is "
                       "saved in the billing settings. Our accounts team needs it for compliance.",
        "category": "billing", "priority": "medium", "status": "resolved", "requester": "riya",
        "agent": "sam", "days_ago": 26,
        "resolution": "The tax number was saved on the profile but not on the billing entity used for invoices. "
                      "Copied it across and regenerated the last three invoices.",
    },
    {
        "title": "Error 500 when uploading a profile photo",
        "description": "Uploading a PNG profile picture shows 'Something went wrong (500)'. The file is 3 MB.",
        "category": "bug", "priority": "low", "status": "resolved", "requester": "daniel",
        "agent": "meera", "days_ago": 24,
        "resolution": "Images above 2 MB were not being resized before storage. Raised the limit to 10 MB with "
                      "automatic resizing in release 4.2.3.",
    },
    {
        "title": "Unable to add new team member",
        "description": "When I invite a colleague the button greys out and nothing happens. We are on the "
                       "Business plan with 8 of 10 seats used.",
        "category": "account", "priority": "medium", "status": "resolved", "requester": "emily",
        "agent": "meera", "days_ago": 22,
        "resolution": "Two pending invitations were counted as used seats. Cancelled the expired invitations and "
                      "the invite button works again.",
    },
    {
        "title": "Reports page times out for the yearly view",
        "description": "Selecting 'Last 12 months' on the reports page ends with a gateway timeout after about "
                       "30 seconds. Quarterly view works.",
        "category": "performance", "priority": "high", "status": "resolved", "requester": "daniel",
        "agent": "sam", "days_ago": 20,
        "resolution": "Yearly reports are now generated from pre-aggregated monthly totals, which brings the "
                      "response time down to around four seconds.",
    },
    {
        "title": "Password reset email never arrives",
        "description": "I requested a password reset three times but I don't receive any email. I checked spam "
                       "as well.",
        "category": "login_access", "priority": "medium", "status": "resolved", "requester": "karthik",
        "agent": "meera", "days_ago": 18,
        "resolution": "The company mail server was rejecting our sender domain. Shared the SPF/DKIM details with "
                      "the customer's IT team and the reset emails are delivered now.",
    },
    {
        "title": "API rate limit reached too quickly",
        "description": "Our nightly sync hits 'HTTP 429 Too Many Requests' after a few minutes. We send about "
                       "50 requests per minute which should be within our plan's limit.",
        "category": "integration", "priority": "medium", "status": "resolved", "requester": "daniel",
        "agent": "sam", "days_ago": 16,
        "resolution": "The client created a new API token for every request, and limits are counted per account "
                      "including token creation. Reusing one token keeps the sync well under the limit.",
    },
    {
        "title": "Need to change the billing email address",
        "description": "Invoices are still going to a former employee. Please update the billing email to "
                       "accounts@ourcompany.com.",
        "category": "billing", "priority": "low", "status": "resolved", "requester": "riya",
        "agent": "meera", "days_ago": 14,
        "resolution": "Updated the billing contact and explained where to change it under Settings > Billing.",
    },
    {
        "title": "Search results do not include archived projects",
        "description": "Global search never returns projects we archived last quarter. We need to find old "
                       "project documents regularly.",
        "category": "feature_request", "priority": "low", "status": "resolved", "requester": "emily",
        "agent": "sam", "days_ago": 12,
        "resolution": "Archived items are excluded by default. Use the 'Include archived' toggle in the search "
                      "filters. Logged the request to make it a saved preference.",
    },
    {
        "title": "Mobile app crashes when opening notifications",
        "description": "On Android 14 the app closes immediately when I tap a notification. Opening the app "
                       "normally works.",
        "category": "bug", "priority": "high", "status": "in_progress", "requester": "karthik",
        "agent": "meera", "days_ago": 9,
    },
    {
        "title": "Single sign-on with Azure AD redirects in a loop",
        "description": "After enabling SSO, users are sent back and forth between our login page and Microsoft "
                       "without ever signing in.",
        "category": "login_access", "priority": "critical", "status": "in_progress", "requester": "emily",
        "agent": "sam", "days_ago": 7,
    },
    {
        "title": "CSV import skips rows with special characters",
        "description": "Importing our customer list skips every row that contains characters such as é or ñ. "
                       "The file is saved as CSV from Excel.",
        "category": "data_reports", "priority": "medium", "status": "in_progress", "requester": "daniel",
        "agent": "meera", "days_ago": 6,
    },
    {
        "title": "Refund not received for cancelled plan",
        "description": "We cancelled our annual plan within the 14-day window two weeks ago, but the refund has "
                       "not reached our account yet.",
        "category": "billing", "priority": "medium", "status": "in_progress", "requester": "riya",
        "agent": "sam", "days_ago": 5,
    },
    {
        "title": "Page freezes when filtering a large table",
        "description": "Filtering the orders table with more than 10,000 rows freezes the browser tab for a "
                       "long time.",
        "category": "performance", "priority": "medium", "status": "in_progress", "requester": "karthik",
        "days_ago": 4,
    },
    {
        "title": "Slack integration stopped posting updates",
        "description": "Ticket updates are no longer posted in our Slack channel. The integration still shows "
                       "as connected.",
        "category": "integration", "priority": "medium", "status": "open", "requester": "emily", "days_ago": 3,
    },
    {
        "title": "Add dark mode to the web app",
        "description": "Many of our team members work late. A dark theme option would make the app easier on "
                       "the eyes.",
        "category": "feature_request", "priority": "low", "status": "open", "requester": "daniel", "days_ago": 3,
    },
    {
        "title": "Account locked after too many sign-in attempts",
        "description": "I typed my password wrong a few times and now it says my account is locked. I need "
                       "access urgently for month-end closing.",
        "category": "login_access", "priority": "high", "status": "open", "requester": "riya", "days_ago": 2,
    },
    {
        "title": "Wrong tax amount on latest invoice",
        "description": "The latest invoice applies 18% tax on the full amount including the discount, so the "
                       "total is higher than expected.",
        "category": "billing", "priority": "medium", "status": "open", "requester": "karthik", "days_ago": 2,
    },
    {
        "title": "Charts show blank area in Safari",
        "description": "On Safari 17 the revenue chart on the dashboard is just an empty white box. It works in "
                       "Chrome.",
        "category": "bug", "priority": "low", "status": "open", "requester": "emily", "days_ago": 1,
    },
    {
        "title": "Cannot remove a former employee from the workspace",
        "description": "The remove option is disabled for one user who left the company. They still have access "
                       "to shared projects.",
        "category": "account", "priority": "high", "status": "open", "requester": "riya", "days_ago": 1,
    },
    {
        "title": "Scheduled report email arrives empty",
        "description": "The weekly KPI report email arrives on time but the attachment is a 0 KB file.",
        "category": "data_reports", "priority": "medium", "status": "open", "requester": "daniel", "days_ago": 0,
    },
    {
        "title": "Application very slow every morning",
        "description": "Between 9 and 10 AM the whole application is sluggish, pages take 10-15 seconds. It "
                       "becomes normal later in the day.",
        "category": "performance", "priority": "high", "status": "open", "requester": "karthik", "days_ago": 0,
    },
    {
        "title": "How do I generate a new API key?",
        "description": "Our developer left and we need to create a new API key for the inventory integration. "
                       "I can't find the option.",
        "category": "integration", "priority": "low", "status": "open", "requester": "riya", "days_ago": 0,
    },
]

COMMENTS = {
    "Mobile app crashes when opening notifications":
        "Reproduced on a Pixel 8 with Android 14. The crash happens when the notification payload has no "
        "project id. Working on a fix with the mobile team.",
    "Single sign-on with Azure AD redirects in a loop":
        "The reply URL configured in Azure has a trailing slash that ours does not. Could you share a "
        "screenshot of the Azure app registration's redirect URIs?",
    "Dashboard takes more than a minute to load":
        "Thanks for the details. I can see slow queries on our side for your workspace and am investigating.",
    "Webhook deliveries failing with 401 Unauthorized":
        "Signature checks fail since 14:05 yesterday, right when new API keys were generated in your workspace.",
}

# Sample attachments (added by seed_demo so the feature is visible in the demo).
WEBHOOK_LOG_TICKET = "Webhook deliveries failing with 401 Unauthorized"
WEBHOOK_LOG = """2026-10-08 09:14:02 INFO  POST /hooks/orders  event=order.created  id=evt_8841
2026-10-08 09:14:02 WARN  signature check failed: expected sha256=4be1...c09a, got sha256=91d0...7f2e
2026-10-08 09:14:02 ERROR responded 401 Unauthorized (signature mismatch)
2026-10-08 09:19:02 INFO  retry 1/5 for evt_8841
2026-10-08 09:19:02 ERROR responded 401 Unauthorized (signature mismatch)
2026-10-08 09:29:02 INFO  retry 2/5 for evt_8841
2026-10-08 09:29:02 ERROR responded 401 Unauthorized (signature mismatch)
2026-10-08 09:31:47 INFO  POST /hooks/orders  event=order.paid  id=evt_8843
2026-10-08 09:31:47 ERROR responded 401 Unauthorized (signature mismatch)
"""

INVOICE_TICKET = "Invoice PDF is missing our GST number"
INVOICE = {
    "number": "INV-2026-0142",
    "date": "1 October 2026",
    "customer": "Menon Traders Pvt Ltd",
    "lines": [("Pro plan - 12 seats", "1", "Rs 18,000.00"), ("Priority support add-on", "1", "Rs 3,000.00")],
    "total": "Rs 24,780.00 (incl. 18% GST)",
}
