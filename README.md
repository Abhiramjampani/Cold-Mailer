# Cold Email Sender for SDE-1 Opportunities

A Python application that reads HR contacts from an Excel file and sends personalized cold emails for SDE-1 job opportunities via Gmail.

## Features

- 📧 Reads HR contacts from Excel file (Email, HR Name, Company Name)
- ✉️ Sends personalized emails with HR name and company name
- 🔒 Uses Gmail App Password for secure authentication
- ⏱️ Configurable delay between emails to avoid spam filters
- 👀 Preview mode to review emails before sending
- 📊 Summary report after sending

## Setup Instructions

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. At the bottom, click on **App passwords**
4. Select "Mail" and "Windows Computer" (or your device)
5. Click **Generate**
6. Copy the 16-character password (no spaces)

### Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   GMAIL_ADDRESS=your.email@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```

### Step 4: Prepare Your Excel File

Create an Excel file (`.xlsx`) with these columns:
| Email | HR Name | Company Name |
|-------|---------|--------------|
| hr@google.com | Priya Sharma | Google |
| hr@microsoft.com | John Smith | Microsoft |

See `sample_contacts.xlsx` for reference.

### Step 5: Customize Email Template

Edit the `EMAIL_BODY_TEMPLATE` in `cold_mailer.py` to personalize your message:
- Add your name
- Add your phone number
- Add your LinkedIn profile
- Add your GitHub/Portfolio link
- Modify the content as needed

## Usage

### Preview Emails (Recommended First Step)

```bash
python cold_mailer.py your_contacts.xlsx --preview
```

### Send Emails

```bash
python cold_mailer.py your_contacts.xlsx
```

### Send with Custom Delay (in seconds)

```bash
python cold_mailer.py your_contacts.xlsx --delay 60
```

## Important Notes

⚠️ **Gmail Sending Limits:**
- Free Gmail: ~500 emails/day
- Google Workspace: ~2,000 emails/day

⚠️ **Best Practices:**
- Use a delay of at least 30 seconds between emails
- Don't send too many emails at once (start with 10-20)
- Make sure your email content is genuine and personalized
- Don't spam! Only contact relevant HRs

⚠️ **Security:**
- Never share your `.env` file
- Add `.env` to `.gitignore` if using Git
- Revoke App Password after you're done

## File Structure

```
Cold+mail/
├── cold_mailer.py          # Main application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .env                   # Your credentials (create this)
├── sample_contacts.xlsx   # Sample Excel template
└── README.md              # This file
```

## Troubleshooting

**Error: Authentication failed**
- Make sure 2-Step Verification is enabled
- Generate a new App Password
- Copy the password without spaces

**Error: Missing required column**
- Ensure your Excel has columns: `Email`, `HR Name`, `Company Name`
- Column names are case-sensitive

**Emails going to spam**
- Add a professional signature
- Don't use spam trigger words
- Keep email content genuine
- Use longer delays between emails

## License

Free to use for personal job searching purposes.
