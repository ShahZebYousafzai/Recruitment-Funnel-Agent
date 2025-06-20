# utils/email_integration.py
"""
Email integration system for handling incoming candidate responses
Supports both IMAP monitoring and webhook-based email processing
"""

import imaplib
import email
import json
import re
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from dataclasses import dataclass
import time
import threading
from queue import Queue

@dataclass
class IncomingEmail:
    """Data structure for incoming emails"""
    sender_email: str
    sender_name: str
    subject: str
    body: str
    received_at: datetime
    message_id: str
    thread_id: Optional[str] = None
    attachments: List[str] = None

class EmailProcessor:
    """Processes incoming emails and triggers candidate response analysis"""
    
    def __init__(self, interview_agent, candidate_database=None):
        self.interview_agent = interview_agent
        self.candidate_database = candidate_database or {}
        self.email_queue = Queue()
        self.processing_active = False
        self.processed_emails = set()  # Track processed message IDs
        
    def process_incoming_email(self, email_data: IncomingEmail) -> Dict:
        """
        Process a single incoming email and trigger response analysis
        
        Args:
            email_data: IncomingEmail object containing email details
            
        Returns:
            Dict with processing results
        """
        
        # Check if already processed
        if email_data.message_id in self.processed_emails:
            return {
                'status': 'already_processed',
                'message': 'Email already processed',
                'email_id': email_data.message_id
            }
        
        # Find candidate by email
        candidate = self._find_candidate_by_email(email_data.sender_email)
        
        if not candidate:
            return {
                'status': 'candidate_not_found',
                'message': f'No candidate found for email: {email_data.sender_email}',
                'email_data': email_data
            }
        
        # Check if this is a response to screening questions
        if self._is_screening_response(email_data.subject, email_data.body):
            
            try:
                # Get job description (you might need to store this association)
                job_description = self._get_job_description_for_candidate(candidate)
                
                # Process the response
                result = self.interview_agent.process_email_response(
                    candidate=candidate,
                    email_content=email_data.body,
                    job_description=job_description,
                    email_subject=email_data.subject,
                    sender_email=email_data.sender_email
                )
                
                # Mark as processed
                self.processed_emails.add(email_data.message_id)
                
                # Log the processing
                print(f"✅ Processed response from {candidate.name}: {result['status']}")
                
                return {
                    'status': 'processed',
                    'candidate_name': candidate.name,
                    'analysis_result': result,
                    'email_data': email_data
                }
                
            except Exception as e:
                print(f"❌ Error processing email from {candidate.name}: {str(e)}")
                return {
                    'status': 'processing_error',
                    'error': str(e),
                    'candidate_name': candidate.name,
                    'email_data': email_data
                }
        
        else:
            # Not a screening response - might be a general inquiry
            return {
                'status': 'not_screening_response',
                'message': 'Email does not appear to be a screening response',
                'candidate_name': candidate.name,
                'email_data': email_data
            }
    
    def _find_candidate_by_email(self, email_address: str):
        """Find candidate by email address"""
        
        email_lower = email_address.lower()
        
        # Search in candidate database
        for candidate_id, candidate in self.candidate_database.items():
            if candidate.email.lower() == email_lower:
                return candidate
        
        return None
    
    def _is_screening_response(self, subject: str, body: str) -> bool:
        """Determine if email is a response to screening questions"""
        
        # Keywords that indicate screening responses
        screening_keywords = [
            'screening', 'questions', 'answers', 'response', 
            'follow-up', 'interview', 'application'
        ]
        
        # Check subject line
        subject_lower = subject.lower()
        for keyword in screening_keywords:
            if keyword in subject_lower:
                return True
        
        # Check for numbered answers in body (1., 2., etc.)
        if re.search(r'\b\d+\.\s', body):
            return True
        
        # Check for question response patterns
        if re.search(r'(question|Q\d+|answer|A\d+)', body, re.IGNORECASE):
            return True
        
        return True  # Default to true for now - can be refined
    
    def _get_job_description_for_candidate(self, candidate):
        """Get job description associated with candidate"""
        # This would typically involve looking up the job description
        # that the candidate applied for. For now, return None
        # In a real system, you'd have this association stored
        return None
    
    def add_candidate(self, candidate):
        """Add candidate to the database"""
        self.candidate_database[candidate.id] = candidate
    
    def start_email_monitoring(self, check_interval: int = 60):
        """Start monitoring for new emails (background thread)"""
        
        if self.processing_active:
            print("Email monitoring already active")
            return
        
        self.processing_active = True
        
        def monitor_loop():
            print(f"📧 Starting email monitoring (checking every {check_interval} seconds)")
            
            while self.processing_active:
                try:
                    # Process queued emails
                    while not self.email_queue.empty():
                        email_data = self.email_queue.get()
                        result = self.process_incoming_email(email_data)
                        print(f"Processed email: {result['status']}")
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    print(f"Error in email monitoring: {str(e)}")
                    time.sleep(check_interval)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_email_monitoring(self):
        """Stop email monitoring"""
        self.processing_active = False
        print("📧 Email monitoring stopped")
    
    def queue_email_for_processing(self, email_data: IncomingEmail):
        """Add email to processing queue"""
        self.email_queue.put(email_data)

class IMAPEmailMonitor:
    """Monitor IMAP inbox for new emails"""
    
    def __init__(self, 
                 imap_server: str,
                 email_address: str, 
                 password: str,
                 folder: str = 'INBOX',
                 use_ssl: bool = True):
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password
        self.folder = folder
        self.use_ssl = use_ssl
        self.connection = None
        self.last_check = datetime.now() - timedelta(hours=1)
    
    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.imap_server)
            else:
                self.connection = imaplib.IMAP4(self.imap_server)
            
            self.connection.login(self.email_address, self.password)
            self.connection.select(self.folder)
            
            print(f"✅ Connected to IMAP server: {self.imap_server}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to IMAP server: {str(e)}")
            return False
    
    def fetch_new_emails(self, since_date: datetime = None) -> List[IncomingEmail]:
        """Fetch new emails since last check"""
        
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Search for emails since last check
            if since_date is None:
                since_date = self.last_check
            
            date_str = since_date.strftime('%d-%b-%Y')
            search_criteria = f'(SINCE "{date_str}")'
            
            typ, message_numbers = self.connection.search(None, search_criteria)
            
            emails = []
            
            for num in message_numbers[0].split():
                try:
                    # Fetch email
                    typ, msg_data = self.connection.fetch(num, '(RFC822)')
                    raw_email = msg_data[0][1]
                    
                    # Parse email
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    incoming_email = self._parse_email_message(email_message)
                    
                    if incoming_email:
                        emails.append(incoming_email)
                
                except Exception as e:
                    print(f"Error parsing email: {str(e)}")
                    continue
            
            self.last_check = datetime.now()
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def _parse_email_message(self, email_message) -> Optional[IncomingEmail]:
        """Parse email message into IncomingEmail object"""
        
        try:
            # Extract basic info
            sender = email_message.get('From', '')
            subject = email_message.get('Subject', '')
            date_str = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            
            # Parse sender
            sender_email, sender_name = self._parse_sender(sender)
            
            # Parse date
            received_at = self._parse_date(date_str)
            
            # Extract body
            body = self._extract_body(email_message)
            
            return IncomingEmail(
                sender_email=sender_email,
                sender_name=sender_name,
                subject=subject,
                body=body,
                received_at=received_at,
                message_id=message_id
            )
            
        except Exception as e:
            print(f"Error parsing email message: {str(e)}")
            return None
    
    def _parse_sender(self, sender_str: str) -> tuple:
        """Parse sender string to extract email and name"""
        
        # Handle formats like "John Doe <john@example.com>" or "john@example.com"
        email_match = re.search(r'<([^>]+)>', sender_str)
        if email_match:
            email_addr = email_match.group(1)
            name = sender_str.replace(f'<{email_addr}>', '').strip()
            name = name.strip('"').strip("'")
        else:
            email_addr = sender_str.strip()
            name = email_addr.split('@')[0]  # Use part before @ as name
        
        return email_addr, name
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string"""
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except:
            return datetime.now()
    
    def _extract_body(self, email_message) -> str:
        """Extract body text from email message"""
        
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8')
            except:
                body = str(email_message.get_payload())
        
        return body.strip()
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                print("📧 Disconnected from IMAP server")
            except:
                pass

class WebhookEmailHandler:
    """Handle emails received via webhook (e.g., from SendGrid, Mailgun)"""
    
    def __init__(self, email_processor: EmailProcessor):
        self.email_processor = email_processor
    
    def handle_sendgrid_webhook(self, webhook_data: Dict) -> Dict:
        """Handle SendGrid webhook data"""
        
        try:
            # Parse SendGrid webhook format
            from_email = webhook_data.get('from', '')
            to_email = webhook_data.get('to', '')
            subject = webhook_data.get('subject', '')
            text_body = webhook_data.get('text', '')
            html_body = webhook_data.get('html', '')
            
            # Use text body, fallback to HTML
            body = text_body if text_body else self._html_to_text(html_body)
            
            # Create IncomingEmail object
            email_data = IncomingEmail(
                sender_email=from_email,
                sender_name=from_email.split('@')[0],
                subject=subject,
                body=body,
                received_at=datetime.now(),
                message_id=webhook_data.get('message_id', f"sg_{int(time.time())}")
            )
            
            # Process the email
            result = self.email_processor.process_incoming_email(email_data)
            
            return {
                'success': True,
                'processing_result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_mailgun_webhook(self, webhook_data: Dict) -> Dict:
        """Handle Mailgun webhook data"""
        
        try:
            # Parse Mailgun webhook format
            from_email = webhook_data.get('sender', '')
            subject = webhook_data.get('Subject', '')
            body = webhook_data.get('body-plain', webhook_data.get('body-html', ''))
            
            if 'body-html' in webhook_data and not webhook_data.get('body-plain'):
                body = self._html_to_text(body)
            
            email_data = IncomingEmail(
                sender_email=from_email,
                sender_name=from_email.split('@')[0],
                subject=subject,
                body=body,
                received_at=datetime.now(),
                message_id=webhook_data.get('Message-Id', f"mg_{int(time.time())}")
            )
            
            result = self.email_processor.process_incoming_email(email_data)
            
            return {
                'success': True,
                'processing_result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

# Integration example
def setup_email_integration(interview_agent, candidates: List = None):
    """Set up complete email integration system"""
    
    # Initialize email processor
    processor = EmailProcessor(interview_agent)
    
    # Add candidates to processor database
    if candidates:
        for candidate in candidates:
            processor.add_candidate(candidate)
    
    # Example configuration for different email providers
    
    # Gmail IMAP setup
    gmail_monitor = IMAPEmailMonitor(
        imap_server='imap.gmail.com',
        email_address='your-email@gmail.com',  # Set from environment
        password='your-app-password',  # Set from environment
        folder='INBOX'
    )
    
    # Webhook handler setup
    webhook_handler = WebhookEmailHandler(processor)
    
    return {
        'processor': processor,
        'imap_monitor': gmail_monitor,
        'webhook_handler': webhook_handler
    }

# Example usage functions
def demo_email_integration():
    """Demonstrate email integration functionality"""
    
    from models.candidate import Candidate
    from agents.interview_agent import InterviewAgent
    
    # Create sample candidate
    candidate = Candidate(
        id="email_test_001",
        name="Test Candidate",
        email="test.candidate@example.com",
        skills=["Python", "Django"],
        experience_years=3.0
    )
    
    # Initialize interview agent
    agent = InterviewAgent()
    
    # Set up email integration
    integration = setup_email_integration(agent, [candidate])
    processor = integration['processor']
    
    # Simulate incoming email
    mock_email = IncomingEmail(
        sender_email="test.candidate@example.com",
        sender_name="Test Candidate",
        subject="Re: Screening Questions - Python Developer",
        body="""
        Hi! Thanks for the questions.
        
        1. I have 3 years of Python experience working on web applications.
        2. I recently solved a performance issue by optimizing database queries.
        3. I'm excited about this role because it matches my skills perfectly.
        4. I can start in 2 weeks.
        
        Best regards,
        Test Candidate
        """,
        received_at=datetime.now(),
        message_id="demo_001"
    )
    
    # Process the email
    result = processor.process_incoming_email(mock_email)
    
    print("📧 Email Integration Demo Result:")
    print(f"Status: {result['status']}")
    if result['status'] == 'processed':
        analysis = result['analysis_result']['analysis']
        print(f"Candidate: {result['candidate_name']}")
        print(f"Overall Score: {analysis.overall_score:.2f}")
        print(f"Recommendation: {analysis.recommendation}")

if __name__ == "__main__":
    demo_email_integration()