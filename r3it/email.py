import smtplib
from email.message import EmailMessage
from config import all

def sendEmail(recipient, subject, body=''):
    '''Sends an email with creds in config.py'''
    # Compose email.
    msg = EmailMessage()
    msg['From'] = r3itEmailAddress
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)
    # Send email.
    s = smtplib.SMTP(smtpServer)
    s.SMTP.login(emailUser, emailPassword)
    s.send_message(msg)
    s.quit()
