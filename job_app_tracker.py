#!/usr/bin/env python3
"""
Job Application Email Tracker

This Python script integrates with the Gmail API and Google Sheets API to:
- Fetch emails related to job applications using specific keywords.
- Parse emails to extract the job title, rejection stage, and next steps.
- Log the details in a Google Sheet.

Dependencies:
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

To install dependencies:
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Setup:
1. Enable Gmail API and Google Sheets API on Google Cloud Console.
2. Download your OAuth credentials (credentials.json) and place it in the same directory.
3. The first run will prompt for OAuth authentication in your browser.
"""

import os
import re
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define the scopes required for the application
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials():
    """Obtains valid user credentials from storage or runs the OAuth flow."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If no valid credentials are available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print("Error refreshing credentials:", e)
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_gmail_service(creds):
    """Builds and returns the Gmail API service."""
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print("Error creating Gmail service:", e)
        return None


def get_sheets_service(creds):
    """Builds and returns the Google Sheets API service."""
    try:
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as e:
        print("Error creating Sheets service:", e)
        return None


def fetch_job_emails(service):
    """
    Fetches emails from Gmail that are related to job applications based on specific keywords.
    Returns a list of email data dictionaries.
    """
    query = "application OR job OR 'software engineering'"
    email_data = []
    try:
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        for msg in messages:
            msg_detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="full")
                .execute()
            )
            headers = msg_detail.get("payload", {}).get("headers", [])
            subject = ""
            sender = ""
            date = ""
            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Date":
                    date = header["value"]
            body = ""
            # Check if the email body is directly available
            if "data" in msg_detail.get("payload", {}).get("body", {}):
                try:
                    body = base64.urlsafe_b64decode(
                        msg_detail["payload"]["body"]["data"].encode("ASCII")
                    ).decode("utf-8")
                except Exception as e:
                    print("Error decoding email body:", e)
            else:
                # If the email has multiple parts, try to extract the plain text part
                parts = msg_detail.get("payload", {}).get("parts", [])
                for part in parts:
                    if part.get("mimeType") == "text/plain" and "data" in part.get(
                        "body", {}
                    ):
                        try:
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"].encode("ASCII")
                            ).decode("utf-8")
                            break
                        except Exception as e:
                            print("Error decoding part of email body:", e)
            email_data.append(
                {
                    "id": msg["id"],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "body": body,
                }
            )
    except Exception as e:
        print("Error fetching emails:", e)
    return email_data


def parse_email(email):
    """
    Parses the email content to extract:
    - Job title (by matching common job title keywords)
    - Rejection stage (if applicable)
    - Next steps / reply status
    Returns a dictionary with the parsed details.
    """
    # Combine subject and body for parsing and convert to lowercase for matching
    text = (email["subject"] + " " + email["body"]).lower()

    # Extract job title using simple keyword matching
    job_keywords = [
        "software engineer",
        "developer",
        "engineer",
        "data scientist",
        "manager",
        "designer",
        "qa",
    ]
    job_title = None
    for keyword in job_keywords:
        if keyword in text:
            job_title = keyword.title()
            break

    # Determine rejection stage by checking for negative keywords
    rejection_keywords = ["rejected", "not selected", "declined", "unfortunately"]
    rejection_stage = ""
    if any(word in text for word in rejection_keywords):
        rejection_stage = "Rejected"

    # Check for next steps or reply status keywords
    next_steps_keywords = ["next steps", "interview", "schedule", "call"]
    next_steps = "Pending"
    if any(word in text for word in next_steps_keywords):
        next_steps = "Next Steps Provided"

    return {
        "job_title": job_title if job_title else "Unknown",
        "rejection_stage": rejection_stage,
        "next_steps": next_steps,
    }


def extract_company(sender):
    """
    Extracts the company name from the sender's email address.
    For example, from 'noreply@company.com', it extracts 'Company'.
    """
    match = re.search(r"@([\w.-]+)", sender)
    if match:
        domain = match.group(1)
        company = domain.split(".")[0].title()
        return company
    return "Unknown"


def create_spreadsheet(sheets_service, title="Job Applications Log"):
    """
    Creates a new Google Spreadsheet with a given title.
    Returns the spreadsheet ID.
    """
    spreadsheet_body = {
        "properties": {"title": title},
        "sheets": [{"properties": {"title": "Sheet1"}}],
    }
    try:
        spreadsheet = (
            sheets_service.spreadsheets()
            .create(body=spreadsheet_body, fields="spreadsheetId")
            .execute()
        )
        spreadsheet_id = spreadsheet.get("spreadsheetId")
        print(f"Spreadsheet created with ID: {spreadsheet_id}")
        return spreadsheet_id
    except Exception as e:
        print("Error creating spreadsheet:", e)
        return None


def update_sheet(sheets_service, spreadsheet_id, data):
    """
    Appends data rows to the Google Sheet.
    'data' should be a list of lists, where each inner list represents a row.
    """
    body = {"values": data}
    try:
        result = (
            sheets_service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        updated_cells = result.get("updates", {}).get("updatedCells")
        print(f"{updated_cells} cells appended.")
    except Exception as e:
        print("Error updating spreadsheet:", e)


def main():
    """Main function to run the application."""
    # Get OAuth2 credentials
    creds = get_credentials()
    gmail_service = get_gmail_service(creds)
    sheets_service = get_sheets_service(creds)

    if not gmail_service or not sheets_service:
        print("Failed to create service connections. Exiting.")
        return

    # Create a new spreadsheet (or use an existing spreadsheet by providing its ID)
    spreadsheet_id = create_spreadsheet(sheets_service)
    if not spreadsheet_id:
        print("Failed to create or access spreadsheet. Exiting.")
        return

    # Prepare header row for the Google Sheet
    headers = [
        "Company",
        "Job Title",
        "Date of Application",
        "Rejection Stage",
        "Next Steps/Reply Status",
        "Notes",
    ]
    update_sheet(sheets_service, spreadsheet_id, [headers])

    # Fetch emails related to job applications
    emails = fetch_job_emails(gmail_service)
    if not emails:
        print("No job application emails found.")
        return

    # Process each email and append the parsed data to the Google Sheet
    for email in emails:
        parsed = parse_email(email)
        company = extract_company(email["sender"])
        job_title = parsed["job_title"]
        date = email["date"]
        rejection_stage = parsed["rejection_stage"]
        next_steps = parsed["next_steps"]
        # Use the email subject as additional notes
        notes = email["subject"]
        row = [company, job_title, date, rejection_stage, next_steps, notes]
        update_sheet(sheets_service, spreadsheet_id, [row])

    print("Job application data has been logged to the Google Sheet.")


if __name__ == "__main__":
    main()
