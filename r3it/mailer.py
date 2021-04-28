import smtplib, ssl
from email.message import EmailMessage
from config import *
from logger import log

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
    try:
        with smtplib.SMTP(smtpServer, 587) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(emailUser, emailPassword)
            server.send_message(msg)

        log("Email with subject '" + subject + "' sent to " + recipient)
    except:
        log("Email with subject '" + subject + "' failed to send to " + recipient)

def mailEngineers(subject='',body=''):
    for email in roles.get('engineer',[]):
        sendEmail(email,subject,body)