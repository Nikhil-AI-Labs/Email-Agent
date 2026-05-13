import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig

@tool
def send_email(recipient: str, subject: str, body: str, config: RunnableConfig) -> str:
    """Sends a single email to the recipient with the given subject and body. 
    It automatically attaches any files the user uploaded.
    """
    conf = config.get("configurable", {})
    email = conf.get("smtp_email")
    password = conf.get("smtp_password")
    attachments = conf.get("attachments", [])
    
    if not email or not password:
        return "Error: SMTP credentials not provided by the user. Ask the user to enter them in the sidebar."
        
    try:
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        for att in attachments:
            mime_type = att.get("mime_type", "application/octet-stream")
            maintype, _, subtype = mime_type.partition('/')
            if not subtype: subtype = "octet-stream"
                
            part = MIMEBase(maintype, subtype)
            part.set_payload(att.get("bytes", b""))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{att.get("filename", "attachment")}"')
            msg.attach(part)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        return f"Successfully sent email to {recipient}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@tool
def send_bulk_emails(recipients: list[str], subjects: list[str], bodies: list[str], config: RunnableConfig) -> str:
    """Sends emails to multiple recipients in one batch. 
    Use this instead of send_email when you need to send to more than 3 people to save time.
    recipients, subjects, and bodies must be lists of strings of the exact same length.
    """
    conf = config.get("configurable", {})
    email = conf.get("smtp_email")
    password = conf.get("smtp_password")
    attachments = conf.get("attachments", [])
    
    if not email or not password:
        return "Error: SMTP credentials not provided by the user."
        
    if len(recipients) != len(subjects) or len(recipients) != len(bodies):
        return "Error: input lists (recipients, subjects, bodies) must be the same length."

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        
        success_count = 0
        for i in range(len(recipients)):
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = recipients[i]
            msg['Subject'] = subjects[i]
            msg.attach(MIMEText(bodies[i], 'plain'))
            
            for att in attachments:
                mime_type = att.get("mime_type", "application/octet-stream")
                maintype, _, subtype = mime_type.partition('/')
                if not subtype: subtype = "octet-stream"
                    
                part = MIMEBase(maintype, subtype)
                part.set_payload(att.get("bytes", b""))
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{att.get("filename", "attachment")}"')
                msg.attach(part)
                
            server.send_message(msg)
            success_count += 1
            
        server.quit()
        return f"Successfully sent {success_count} emails out of {len(recipients)}."
    except Exception as e:
        return f"Failed during bulk send. Sent {success_count}. Error: {str(e)}"
