import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> bool:
    """
    Send an email using SMTP
    
    Args:
        email_to: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        cc: Carbon copy recipients
        bcc: Blind carbon copy recipients
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        logger.info(f"Preparing to send email to {email_to}")
        logger.debug(f"SMTP settings: Host={settings.SMTP_HOST}, Port={settings.SMTP_PORT}, TLS={settings.SMTP_TLS}, User={settings.SMTP_USER}")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_SENDER
        message["To"] = email_to
        
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        
        logger.debug(f"Email headers set: Subject={subject}, From={settings.SMTP_SENDER}, To={email_to}")
            
        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        logger.debug("HTML content attached to email")
        
        # Create recipient list
        recipients = [email_to]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        
        logger.debug(f"Recipients list created with {len(recipients)} recipients")
            
        # Create SMTP connection - use SSL for port 465, otherwise regular SMTP with optional STARTTLS
        if settings.SMTP_PORT == 465:
            # Use SMTP_SSL for port 465
            logger.debug("Using SMTP_SSL for port 465")
            try:
                logger.debug(f"Attempting to connect to {settings.SMTP_HOST}:{settings.SMTP_PORT} with SSL")
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        logger.debug(f"Attempting to login with user: {settings.SMTP_USER}")
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        logger.debug("Login successful")
                    
                    # Send email
                    logger.debug(f"Sending email from {settings.SMTP_SENDER} to {recipients}")
                    server.sendmail(settings.SMTP_SENDER, recipients, message.as_string())
                    logger.debug("Email sent successfully via SMTP_SSL")
            except Exception as ssl_error:
                logger.error(f"SSL connection error: {str(ssl_error)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        else:
            # Use regular SMTP with optional STARTTLS for other ports (typically 587)
            logger.debug(f"Using regular SMTP for port {settings.SMTP_PORT}")
            try:
                logger.debug(f"Attempting to connect to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.SMTP_TLS:
                        logger.debug("Initiating STARTTLS")
                        server.starttls()
                    
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        logger.debug(f"Attempting to login with user: {settings.SMTP_USER}")
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        logger.debug("Login successful")
                    
                    # Send email
                    logger.debug(f"Sending email from {settings.SMTP_SENDER} to {recipients}")
                    server.sendmail(settings.SMTP_SENDER, recipients, message.as_string())
                    logger.debug("Email sent successfully via regular SMTP")
            except Exception as smtp_error:
                logger.error(f"SMTP connection error: {str(smtp_error)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        logger.info(f"Email sent successfully to {email_to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        import traceback
        logger.error(f"Email error traceback: {traceback.format_exc()}")
        return False

def send_invitation_email(
    email_to: str,
    company_name: str,
    job_title: Optional[str] = None,
    invitation_link: str = "",
    message: Optional[str] = None,
    external_company_info: Optional[dict] = None,
) -> bool:
    """
    Send an invitation email to a candidate
    
    Args:
        email_to: Candidate email address
        company_name: Name of the company sending the invitation (or external company name)
        job_title: Title of the job position (optional)
        invitation_link: Link to accept the invitation
        message: Custom message from the recruiter (optional)
        external_company_info: Additional company information for external companies (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = f"You've been invited to apply at {company_name}"
    
    # Create HTML content
    position_text = f" for the {job_title} position" if job_title else ""
    custom_message = f"<p>{message}</p>" if message else ""
    
    # Add external company information if provided
    company_info_section = ""
    if external_company_info:
        company_details = []
        if external_company_info.get('email'):
            company_details.append(f"Email: {external_company_info['email']}")
        if external_company_info.get('website'):
            company_details.append(f"Website: {external_company_info['website']}")
        if external_company_info.get('size'):
            company_details.append(f"Company Size: {external_company_info['size']}")
        if external_company_info.get('sector'):
            company_details.append(f"Industry: {external_company_info['sector']}")
        if external_company_info.get('about'):
            company_details.append(f"About: {external_company_info['about']}")
        
        if company_details:
            company_info_section = f"""
            <div style="background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h4 style="margin-top: 0;">Company Information:</h4>
                <ul style="margin-bottom: 0;">
                    {''.join([f'<li>{detail}</li>' for detail in company_details])}
                </ul>
            </div>
            """
    
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; 
                           color: #ffffff; text-decoration: none; border-radius: 5px; }}
                .footer {{ font-size: 12px; color: #6c757d; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>You've Been Invited!</h2>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>{company_name} has invited you to apply{position_text} on Karzo.</p>
                    {custom_message}
                    {company_info_section}
                    <p>Click the button below to complete your application:</p>
                    <p><a href="{invitation_link}" class="button">Apply Now</a></p>
                    <p>If you have any questions, please reply to this email.</p>
                    <p>Best regards,<br>The Karzo Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Karzo. Please do not reply directly to this email.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
    )
