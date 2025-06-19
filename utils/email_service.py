# utils/email_service.py
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
import os
from datetime import datetime

class EmailService:
    """Service for sending emails through SMTP"""
    
    def __init__(self, host: str, port: int, username: str, password: str, 
                 use_tls: bool = True, from_name: str = "AI Recruitment Team"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_name = from_name
        self.is_configured = bool(username and password)
        
    def send_email(self, 
                   to_email: str,
                   subject: str,
                   body: str,
                   to_name: Optional[str] = None,
                   attachments: Optional[List[str]] = None,
                   is_html: bool = False) -> Dict:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            to_name: Recipient name (optional)
            attachments: List of file paths to attach (optional)
            is_html: Whether the body is HTML format
            
        Returns:
            Dict with status and message
        """
        
        if not self.is_configured:
            return {
                'success': False,
                'message': 'Email service is not properly configured',
                'error': 'Missing username or password'
            }
        
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = f"{self.from_name} <{self.username}>"
            message["To"] = f"{to_name} <{to_email}>" if to_name else to_email
            message["Subject"] = subject
            
            # Add body
            body_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, body_type))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(message, file_path)
                    else:
                        print(f"Warning: Attachment file not found: {file_path}")
            
            # Create SMTP session
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()  # Enable TLS encryption
                
                server.login(self.username, self.password)
                
                # Send email
                text = message.as_string()
                server.sendmail(self.username, to_email, text)
                
            return {
                'success': True,
                'message': f'Email sent successfully to {to_email}',
                'timestamp': datetime.now().isoformat()
            }
            
        except smtplib.SMTPAuthenticationError as e:
            return {
                'success': False,
                'message': 'SMTP Authentication failed',
                'error': str(e),
                'suggestion': 'Check your email credentials and app password'
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                'success': False,
                'message': f'Invalid recipient email: {to_email}',
                'error': str(e)
            }
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'message': 'SMTP error occurred',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': 'Unexpected error occurred',
                'error': str(e)
            }
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Add attachment to email message"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            message.attach(part)
        except Exception as e:
            print(f"Error adding attachment {file_path}: {str(e)}")
    
    def test_connection(self) -> Dict:
        """Test SMTP connection and authentication"""
        if not self.is_configured:
            return {
                'success': False,
                'message': 'Email service is not configured',
                'error': 'Missing username or password'
            }
        
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                
            return {
                'success': True,
                'message': 'SMTP connection and authentication successful'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            return {
                'success': False,
                'message': 'SMTP Authentication failed',
                'error': str(e),
                'suggestion': 'Check your email credentials. For Gmail, make sure you\'re using an App Password, not your regular password.'
            }
        except smtplib.SMTPConnectError as e:
            return {
                'success': False,
                'message': f'Could not connect to SMTP server {self.host}:{self.port}',
                'error': str(e),
                'suggestion': 'Check your internet connection and SMTP server settings.'
            }
        except (OSError, socket.gaierror) as e:
            return {
                'success': False,
                'message': f'Network error: Could not resolve hostname {self.host}',
                'error': str(e),
                'suggestion': 'Check your internet connection. If using a corporate network, SMTP might be blocked.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': 'Unexpected error during connection test',
                'error': str(e)
            }
    
    def send_test_email(self, to_email: str) -> Dict:
        """Send a test email to verify configuration"""
        subject = "Test Email from AI Recruitment System"
        body = f"""Hello!

This is a test email from the AI Recruitment System to verify that email configuration is working correctly.

If you receive this email, the email service is properly configured and functional.

Sent at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Best regards,
{self.from_name}"""

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )