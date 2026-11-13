#!/usr/bin/env python3
"""W73 mail-box proof: only a new synthetic subject is searched, no user mail is read."""
import imaplib
import os
import re
import smtplib
import socket
import ssl
import sys
import time
import uuid
from email.message import EmailMessage

def run():
    host=os.environ["CELIKOM_SMTP_HOST"].strip().lower()
    port=int(os.environ["CELIKOM_SMTP_PORT"])
    user=os.environ["CELIKOM_SMTP_USER"].strip()
    password=os.environ["CELIKOM_SMTP_PASSWORD"]
    from_addr=os.environ["CELIKOM_MAIL_FROM"].strip()
    imap_host={"smtp.hostinger.com":"imap.hostinger.com",
               "smtp.titan.email":"imap.titan.email",
               "smtp.gmail.com":"imap.gmail.com",
               "smtp.googlemail.com":"imap.gmail.com",
               "smtp-relay.gmail.com":"imap.gmail.com"}.get(host)
    if not imap_host or port not in (465,587):
        print("W73_IMAP_PROVIDER_NOT_SUPPORTED")
        return 3
    if from_addr.lower()!=user.lower() or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",from_addr):
        print("W73_IMAP_CONFIG_MISMATCH")
        return 3
    key=uuid.uuid4().hex
    note=EmailMessage()
    note["From"]=from_addr
    note["To"]=from_addr
    note["Subject"]="CELIKOM W73 mailbox receipt "+key
    note.set_content("Automated W73 synthetic mail receipt probe. No user data.")
    context=ssl.create_default_context()
    if port==465:
        with smtplib.SMTP_SSL(host,port,timeout=12,context=context) as smtp:
            smtp.login(user,password)
            refused=smtp.send_message(note)
    else:
        with smtplib.SMTP(host,port,timeout=12) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(user,password)
            refused=smtp.send_message(note)
    if refused:
        print("W73_TEST_SMTP_RECIPIENT_REJECTED")
        return 4
    print("W73_INDEPENDENT_SMTP_ACCEPTED")
    for attempt in range(5):
        if attempt:
            time.sleep(5)
        with imaplib.IMAP4_SSL(imap_host,993,ssl_context=context,timeout=12) as box:
            box.login(user,password)
            for folder,label in [("INBOX","INBOX"),("Spam","SPAM"),("Junk","SPAM"),
                                 ("Junk Email","SPAM"),("INBOX.Spam","SPAM")]:
                try:
                    status,_=box.select('"'+folder+'"',readonly=True)
                    if status!="OK":
                        continue
                    status,matches=box.search(None,"SUBJECT",'"'+key+'"')
                    if status=="OK" and matches and matches[0].strip():
                        print("W73_IMAP_RECEIPT_"+label+"_CONFIRMED")
                        return 0
                except imaplib.IMAP4.error:
                    continue
    print("W73_IMAP_NO_RECEIPT_AFTER_SMTP_ACCEPTANCE")
    return 5

try:
    sys.exit(run())
except (KeyError,ValueError,imaplib.IMAP4.error,smtplib.SMTPException,socket.timeout,
        TimeoutError,OSError,ssl.SSLError):
    # Never include raw exception messages or credentials from remote mail servers.
    print("W73_IMAP_TEST_FAILED_NO_PRIVATE_DETAILS")
    sys.exit(6)
