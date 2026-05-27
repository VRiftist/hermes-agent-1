#!/usr/bin/env python3
"""Send editorial reports via Gmail SMTP + app password.
Reads sender/recipient from .env, prompts for password via getpass (no echo/disk/log)."""

import smtplib
import ssl
import getpass
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

# === CONFIG — adjust for each book ===
load_dotenv(os.path.expanduser("~/.hermes/.env"))
SENDER = os.getenv("GMAIL_SENDER")
RECIPIENT = os.getenv("BOOK_REVIEW_RECIPIENT")
SUBJECT = "Review Package: Book Project"

FILES = [
    os.path.expanduser("~/Documents/editorial_report_1.docx"),
    os.path.expanduser("~/Documents/editorial_report_2.docx"),
]

BODY = """Hi,

Here is the editorial board review package.

Two reports attached. The full diff between original and refactored manuscript
is available on request.

Let me know what you think.
"""

# === SEND (no changes needed below here) ===
def main():
    if not SENDER or not RECIPIENT:
        print("ERROR: GMAIL_SENDER and BOOK_REVIEW_RECIPIENT must be set in ~/.hermes/.env")
        return 1

    password = getpass.getpass("Enter Gmail app password: ")

    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(BODY, "plain"))

    for fp in FILES:
        if not os.path.exists(fp):
            print(f"WARNING: {fp} not found, skipping")
            continue
        with open(fp, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(fp)}")
            msg.attach(part)
        print(f"  Attached: {os.path.basename(fp)}")

    print("Connecting to Gmail SMTP...")
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        server.login(SENDER, password)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())

    print(f"Sent to {RECIPIENT}")
    password = None  # ensure it's wiped from memory
    return 0

if __name__ == "__main__":
    exit(main())
