#!/usr/bin/env python3
"""Read only the header fields of W73's own synthetic mails in Gmail INBOX."""
import email
import imaplib
import json
import os
import ssl
import sys
import time
from email.header import decode_header, make_header
from email.utils import getaddresses

def safe_run():
    with open(os.environ["W73_RESULT_FILE"], encoding="utf-8") as f:
        result = json.load(f)
    ticket = result["ticket"]
    alias = result["alias"].lower()
    support = result["support_from"].lower()
    if not isinstance(ticket, int) or ticket < 1 or not alias or not support or alias == support:
        print("W73_IMAP_INVALID_SYNTHETIC_METADATA")
        return 2
    ctx = ssl.create_default_context()
    for attempt in range(6):
        if attempt:
            time.sleep(5)
        with imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ctx, timeout=15) as box:
            box.login(os.environ["CELIKOM_SMTP_USER"], os.environ["CELIKOM_SMTP_PASSWORD"])
            if box.select("INBOX", readonly=True)[0] != "OK":
                print("W73_IMAP_INBOX_UNAVAILABLE")
                return 3
            ok, ids = box.search(None, "SUBJECT", str(ticket))
            if ok != "OK":
                print("W73_IMAP_SEARCH_FAILED")
                return 4
            seen = set()
            for ident in (ids[0].split() if ids else []):
                status, payload = box.fetch(ident, "(BODY.PEEK[HEADER.FIELDS (TO SUBJECT)])")
                if status != "OK" or not payload:
                    continue
                raw = next((entry[1] for entry in payload if isinstance(entry, tuple)), None)
                if not isinstance(raw, bytes):
                    continue
                msg = email.message_from_bytes(raw)
                subject = str(make_header(decode_header(str(msg.get("Subject", "")))))
                if "обращение" not in subject.lower() or str(ticket) not in subject:
                    continue
                recipients = {address.lower() for _, address in getaddresses(msg.get_all("To", []))}
                if support in recipients:
                    seen.add("support")
                if alias in recipients:
                    seen.add("user")
            if seen == {"support", "user"}:
                print("W73_GMAIL_REAL_SUPPORT_NOTIFICATION_INBOX_CONFIRMED")
                print("W73_GMAIL_REAL_ADMIN_REPLY_TO_USER_ALIAS_INBOX_CONFIRMED")
                return 0
    print("W73_GMAIL_NOT_BOTH_SYNTHETIC_MAILS_IN_INBOX")
    return 5

try:
    sys.exit(safe_run())
except (KeyError, ValueError, OSError, TypeError, imaplib.IMAP4.error):
    print("W73_IMAP_CHECK_FAILED_NO_EMAIL_DETAILS")
    sys.exit(6)
