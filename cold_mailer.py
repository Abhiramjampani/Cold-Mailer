"""
Cold Email Sender for SDE-1 Opportunities
Reads contacts from Google Sheets and sends personalized cold emails via Gmail.
"""

import smtplib
import os
import time
import argparse
import requests
import pandas as pd
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gmail credentials from .env
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# Email template - CUSTOMIZE THIS
EMAIL_SUBJECT = "Application for SDE-1 Position at {company_name}"

EMAIL_BODY_TEMPLATE = """Dear {hr_name},

I hope this email finds you well. I am writing to express my interest in the Software Developer Engineer (SDE-1) position at {company_name}.

I am a passionate software developer with strong problem-solving skills and experience in:
• Data Structures & Algorithms
• Python, Java, JavaScript
• Web Development (React, Node.js)
• Database Management (SQL, MongoDB)
• Git and Version Control

I am eager to contribute to {company_name}'s innovative projects and would be grateful for the opportunity to discuss how my skills align with your team's needs.

I have attached my resume for your reference. I would appreciate the opportunity to discuss my candidacy further.

Thank you for your time and consideration.

Best regards,
[Your Name]
Email: {sender_email}
Phone: [Your Phone Number]
LinkedIn: [Your LinkedIn Profile]
GitHub: [Your GitHub Profile]
"""


def fetch_google_sheet(sheet_url):
    """
    Fetch data from a Google Sheet URL.
    Converts the sheet to CSV format for download.
    """
    # Extract sheet ID from URL
    if '/d/' in sheet_url:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    else:
        sheet_id = sheet_url
    
    # Get gid (sheet tab) from URL if present
    gid = '0'
    if 'gid=' in sheet_url:
        gid = sheet_url.split('gid=')[1].split('#')[0].split('&')[0]
    
    # Construct export URL
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    print(f"Fetching data from Google Sheet...")
    response = requests.get(export_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Google Sheet. Status code: {response.status_code}")
    
    return response.text


def parse_contacts(csv_data):
    """
    Parse CSV data and extract contacts.
    Expected format: Company, (empty cols), Email, (empty cols), Name
    """
    df = pd.read_csv(StringIO(csv_data), header=None)
    
    contacts = []
    for _, row in df.iterrows():
        # Find non-empty values
        values = [str(val).strip() for val in row if pd.notna(val) and str(val).strip()]
        
        if len(values) >= 2:
            # Assume format: Company, Email, Name (adjust based on your sheet)
            company = values[0] if len(values) > 0 else "Your Company"
            
            # Find email (contains @)
            email = None
            for val in values:
                if '@' in val:
                    email = val
                    break
            
            # Find name (last non-email value)
            name = values[-1] if values[-1] != email else "Hiring Manager"
            
            if email:
                contacts.append({
                    'email': email,
                    'hr_name': name,
                    'company_name': company
                })
    
    return contacts


def send_email(to_email, hr_name, company_name, preview_only=False):
    """
    Send a personalized email to the specified recipient.
    """
    subject = EMAIL_SUBJECT.format(company_name=company_name)
    body = EMAIL_BODY_TEMPLATE.format(
        hr_name=hr_name,
        company_name=company_name,
        sender_email=GMAIL_ADDRESS
    )
    
    if preview_only:
        print("\n" + "="*60)
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print("-"*60)
        print(body)
        print("="*60)
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ Email sent to {hr_name} at {company_name} ({to_email})")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send to {to_email}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Send cold emails from Google Sheets data')
    parser.add_argument('sheet_url', nargs='?', 
                        default='https://docs.google.com/spreadsheets/d/1ra39K0vlwIHH1QOfIdB_-erbXF6fM9kx-DVoqPbYKQw/edit?gid=0#gid=0',
                        help='Google Sheet URL (must be publicly accessible or shared)')
    parser.add_argument('--preview', action='store_true', help='Preview emails without sending')
    parser.add_argument('--delay', type=int, default=30, help='Delay between emails in seconds (default: 30)')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Validate credentials
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("Error: Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env file")
        return
    
    print(f"Gmail Account: {GMAIL_ADDRESS}")
    print(f"Mode: {'PREVIEW' if args.preview else 'SEND'}")
    print(f"Delay: {args.delay} seconds between emails\n")
    
    # Fetch and parse contacts
    try:
        csv_data = fetch_google_sheet(args.sheet_url)
        contacts = parse_contacts(csv_data)
    except Exception as e:
        print(f"Error fetching/parsing sheet: {e}")
        return
    
    if not contacts:
        print("No contacts found in the sheet!")
        return
    
    print(f"Found {len(contacts)} contact(s):\n")
    for i, contact in enumerate(contacts, 1):
        print(f"  {i}. {contact['hr_name']} ({contact['company_name']}) - {contact['email']}")
    
    if not args.preview:
        print("\n" + "-"*40)
        if not args.confirm:
            confirm = input("Do you want to send emails to these contacts? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return
    
    print("\n" + "="*40)
    
    # Send emails
    success_count = 0
    fail_count = 0
    
    for i, contact in enumerate(contacts):
        if i > 0 and not args.preview:
            print(f"Waiting {args.delay} seconds...")
            time.sleep(args.delay)
        
        result = send_email(
            contact['email'],
            contact['hr_name'],
            contact['company_name'],
            preview_only=args.preview
        )
        
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "="*40)
    print(f"Summary: {success_count} successful, {fail_count} failed")
    

if __name__ == "__main__":
    main()
