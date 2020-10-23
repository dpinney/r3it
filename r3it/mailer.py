import smtplib, ssl
from email.message import EmailMessage
from config import *

def sendEmail(recipient, subject='', body=''):
    '''Sends an email using creds in config.py'''
    # Compose email.
    msg = EmailMessage()
    msg['From'] = r3itEmailAddress
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)
    # Send email.
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(emailUser, emailPassword)
        server.send_message(msg)
