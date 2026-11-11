#!/usr/bin/env python3
"""W73: compare only existing general ticket numbers with support mailbox subject indexes."""
import imaplib
import json
import os
import ssl
import sys

try:
    with open(os.environ["W73_LIVE_RESULT"], encoding="utf-8") as f:
        state=json.load(f)
    if state.get("matched") is not True:
        print("W73_LIVE_VS_GH_MAIL_CONFIG_DIFFER")
        sys.exit(2)
    print("W73_LIVE_VS_GH_MAIL_CONFIG_MATCH")
    ids=state.get("tickets")
    if not isinstance(ids,list) or any(not isinstance(i,int) or i<1 for i in ids):
        print("W73_BAD_TICKET_ID_FORMAT")
        sys.exit(3)
    print("W73_LIVE_GENERAL_NOTIFICATION_COUNT="+str(len(ids)))
    if not ids:
        print("W73_NO_RECENT_TICKETS_TO_MATCH")
        sys.exit(4)
    inbox_count=spam_count=not_found=0
    with imaplib.IMAP4_SSL("imap.gmail.com",993,
        ssl_context=ssl.create_default_context(),timeout=15) as box:
        box.login(os.environ["CELIKOM_SMTP_USER"],os.environ["CELIKOM_SMTP_PASSWORD"])
        for ticket in ids:
            folder_seen=False
            for folder,kind in [("INBOX","inbox"),("[Gmail]/Spam","spam")]:
                try:
                    ok,_=box.select('"'+folder+'"',readonly=True)
                    if ok!="OK": continue
                    ok,hits=box.search(None,"SUBJECT",str(ticket))
                    if ok=="OK" and hits and hits[0].strip():
                        if kind=="inbox":inbox_count+=1
                        else:spam_count+=1
                        folder_seen=True
                        break
                except imaplib.IMAP4.error:
                    continue
            if not folder_seen:not_found+=1
    print("W73_LIVE_GENERAL_INBOX_MATCHED="+str(inbox_count))
    print("W73_LIVE_GENERAL_SPAM_MATCHED="+str(spam_count))
    print("W73_LIVE_GENERAL_MAIL_NOT_FOUND="+str(not_found))
    sys.exit(0 if not_found==0 else 5)
except (KeyError,ValueError,TypeError,OSError,imaplib.IMAP4.error):
    print("W73_MAILBOX_LOOKUP_FAILED_NO_PRIVATE_DETAILS")
    sys.exit(6)
