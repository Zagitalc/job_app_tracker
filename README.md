# Job Application Tracker

A Python application that integrates with both the **Gmail API** and the **Google Sheets API** to automate tracking of your job applications. This tool will:

1. **Connect to your Gmail** and search for emails related to job applications using specified keywords.  
2. **Parse email content** to extract the job title, rejection stage, and next steps.  
3. **Log data to Google Sheets**, creating a new sheet (or updating an existing one) with the relevant details.

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Automated Gmail search** using keywords like “application”, “job”, or “software engineering.”  
- **Simple parsing** of email subject and body to detect job title, rejection status, and next steps.  
- **Google Sheets integration** for storing and reviewing all job application data in a single spreadsheet.  
- **OAuth2 authentication** for secure access to both Gmail and Google Sheets APIs.  

---

## Prerequisites

1. **Python 3.11+** (tested with 3.11 and above)
2. A **Google Cloud project** with the following APIs enabled:
   - [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
   - [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
3. **OAuth2 Credentials**:
   - Download your `credentials.json` from the Google Cloud Console.
   - Place it in the root directory of this repository.

---

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/job-application-tracker.git
   cd job-application-tracker
