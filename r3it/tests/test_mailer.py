import imaplib, email, time, os
from email.header import decode_header

from config import smtpServer
from mailer import *

userEmail = 'testing@r3it.ghw.io'
userPass = 'tTSvwucnuw5J'#os.environ['EMAIL_PASS_TESTING_AT_R3IT_GHW_IO']

emailToSend = ('test', 'test message')

def test_sendEmail():

    # send an email 
    sendEmail(userEmail, subject=emailToSend[0], body=emailToSend[1])
    time.sleep(1)

    # connect to server
    with imaplib.IMAP4_SSL(smtpServer,port=993) as mail:
        
        # login and check most recent email in inbox
        mail.login(userEmail, userPass)
        status, messageIDs = mail.select("INBOX")
        status, requested = mail.fetch(messageIDs[0], "(RFC822)")

        # extract email subject and body
        for response in requested:
            if isinstance(response, tuple):
                message = email.message_from_bytes(response[1])
                subject, encoding = decode_header(message["Subject"])[0] 
                body = message.get_payload(decode=True).decode()
                body = body.replace('\r\n','')

        # delete email and close connection            
        mail.store(messageIDs[0], "+FLAGS", "\\Deleted")
        mail.close()

    assert((subject,body)==(emailToSend))