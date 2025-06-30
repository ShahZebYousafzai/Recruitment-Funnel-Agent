import smtplib
import uuid
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
import re
from jinja2 import Template

from models.outreach import (
    OutreachTemplate, CandidateEmail, EmailStatus, OutreachMetrics, 
    OutreachSummary, EmailProvider
)

class OutreachAgent:
    """Agent responsible for REAL candidate outreach via email - ACTUAL EMAIL SENDING"""
    
    def __init__(self, email_provider: Optional[EmailProvider] = None, use_real_email: bool = True):
        self.use_real_email = use_real_email
        self.email_provider = email_provider or self._get_real_provider()
        self.sent_emails = []
        self.failed_emails = []
        
        # Initialize templates
        self.templates = self._load_default_templates()
        
        print(f"📧 Email Agent initialized:")
        print(f"   Real email sending: {'✅ ENABLED' if use_real_email else '❌ SIMULATION'}")
        print(f"   SMTP Server: {self.email_provider.api_endpoint}")
        print(f"   Sender: {self.email_provider.sender_email}")
    
    def _get_real_provider(self) -> EmailProvider:
        """Get email provider configuration from environment variables"""
        
        # Try to get from environment variables first
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
        sender_password = os.getenv('SENDER_PASSWORD', 'your-app-password')
        sender_name = os.getenv('SENDER_NAME', 'Recruiting Team')
        
        return EmailProvider(
            provider_name="real_smtp",
            api_endpoint=f"{smtp_server}:{smtp_port}",
            api_key=sender_password,
            sender_email=sender_email,
            sender_name=sender_name,
            rate_limit=50,
            batch_size=5
        )
    
    def _load_default_templates(self) -> Dict[str, OutreachTemplate]:
        """Load default email templates with better formatting"""
        templates = {}
        
        # Professional outreach template
        initial_template = OutreachTemplate(
            template_id="professional_outreach_v1",
            name="Professional Candidate Outreach",
            subject_template="{{ job_title }} Opportunity at {{ company_name }} - Let's Connect!",
            body_template="""Dear {{ candidate_name }},

I hope this email finds you well!

I came across your profile and was impressed by your background in {{ key_skills }}. We have an exciting {{ job_title }} position at {{ company_name }} that would be a perfect match for your expertise.

🎯 **About the Role:**
{{ job_description_brief }}

💼 **What We're Looking For:**
• {{ required_skills_list }}
• {{ experience_years }}+ years of experience
• Location: {{ job_location }}{{ remote_note }}

⭐ **Why You'd Be a Great Fit:**
• Your experience with {{ candidate_strengths }}
• {{ personalized_note }}

📞 **Next Steps:**
I'd love to schedule a brief 15-20 minute conversation to discuss this opportunity in detail and answer any questions you might have.

Are you available for a quick chat this week? I have the following time slots available:
• {{ interview_slot_1 }}
• {{ interview_slot_2 }}
• {{ interview_slot_3 }}

Or feel free to suggest a time that works better for you!

Looking forward to hearing from you.

Best regards,

{{ recruiter_name }}
{{ recruiter_title }}
{{ company_name }}
📧 {{ recruiter_email }}
📱 {{ recruiter_phone }}

P.S. If you're not actively looking but know someone who might be interested, I'd appreciate any referrals!

---
This email was sent regarding the {{ job_title }} position. If you'd prefer not to receive future opportunities, please reply with "UNSUBSCRIBE".""",
            required_fields=[
                "candidate_name", "job_title", "company_name", "key_skills",
                "job_description_brief", "required_skills_list", "experience_years",
                "job_location", "candidate_strengths", "recruiter_name",
                "recruiter_title", "recruiter_email"
            ],
            optional_fields=[
                "remote_note", "personalized_note", "recruiter_phone",
                "interview_slot_1", "interview_slot_2", "interview_slot_3"
            ]
        )
        templates[initial_template.template_id] = initial_template
        
        return templates
    
    def personalize_email(self, template: OutreachTemplate, candidate_data: Dict[str, Any], 
                         job_data: Dict[str, Any], recruiter_data: Dict[str, Any]) -> CandidateEmail:
        """Personalize email template with candidate and job data"""
        
        try:
            # Prepare template variables
            template_vars = self._prepare_template_variables(
                candidate_data, job_data, recruiter_data
            )
            
            # Render subject and body
            subject_template = Template(template.subject_template)
            body_template = Template(template.body_template)
            
            subject = subject_template.render(**template_vars)
            body = body_template.render(**template_vars)
            
            # Create personalized email
            email = CandidateEmail(
                email_id=f"email_{uuid.uuid4().hex[:8]}",
                candidate_id=str(candidate_data.get('source_id', candidate_data.get('id', 'unknown'))),
                candidate_name=candidate_data.get('name', 'Unknown'),
                candidate_email=candidate_data.get('email', ''),
                subject=subject,
                body=body,
                template_id=template.template_id,
                job_id=job_data.get('job_id', 'unknown'),
                job_title=job_data.get('job_title', 'Unknown Position')
            )
            
            return email
            
        except Exception as e:
            logging.error(f"Error personalizing email for {candidate_data.get('name', 'Unknown')}: {e}")
            raise
    
    def _prepare_template_variables(self, candidate_data: Dict[str, Any], 
                                  job_data: Dict[str, Any], 
                                  recruiter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare variables for template rendering"""
        
        # Extract candidate information
        candidate_skills = candidate_data.get('skills', [])
        key_skills = ', '.join(candidate_skills[:3]) if candidate_skills else "your technical background"
        
        # Generate candidate strengths based on skills match
        required_skills = job_data.get('required_skills', [])
        matching_skills = [skill for skill in candidate_skills if skill in required_skills]
        candidate_strengths = ', '.join(matching_skills[:3]) if matching_skills else "your technical expertise"
        
        # Format required skills list
        required_skills_list = '\n'.join([f"  • {skill}" for skill in required_skills[:5]])
        
        # Remote work note
        remote_note = ""
        if job_data.get('allow_remote', False):
            remote_note = " (Remote work available)"
        
        # Generate interview time slots
        now = datetime.now()
        slots = []
        for i in range(1, 4):
            slot_time = now + timedelta(days=i*2, hours=10)  # Every other day at 10 AM
            slots.append(slot_time.strftime("%A, %B %d at %I:%M %p"))
        
        # Compile all variables
        template_vars = {
            # Candidate variables
            'candidate_name': candidate_data.get('name', 'Unknown'),
            'key_skills': key_skills,
            'candidate_strengths': candidate_strengths,
            
            # Job variables
            'job_title': job_data.get('job_title', 'Unknown Position'),
            'job_description_brief': job_data.get('job_description', 'Exciting opportunity to join our team')[:150] + "...",
            'required_skills_list': required_skills_list,
            'experience_years': job_data.get('min_experience_years', 3),
            'job_location': job_data.get('location', 'Unknown Location'),
            'remote_note': remote_note,
            
            # Company variables
            'company_name': recruiter_data.get('company_name', 'Our Company'),
            
            # Recruiter variables
            'recruiter_name': recruiter_data.get('name', 'Recruiting Team'),
            'recruiter_title': recruiter_data.get('title', 'Senior Recruiter'),
            'recruiter_email': recruiter_data.get('email', 'recruiting@company.com'),
            'recruiter_phone': recruiter_data.get('phone', 'Available upon request'),
            
            # Interview slots
            'interview_slot_1': slots[0],
            'interview_slot_2': slots[1],
            'interview_slot_3': slots[2],
            
            # Optional personalization
            'personalized_note': self._generate_personalized_note(candidate_data, job_data)
        }
        
        return template_vars
    
    def _generate_personalized_note(self, candidate_data: Dict[str, Any], 
                                  job_data: Dict[str, Any]) -> str:
        """Generate a personalized note based on candidate data"""
        
        notes = []
        
        # Experience-based notes
        exp_years = candidate_data.get('experience_years', 0)
        if exp_years >= 8:
            notes.append("Your extensive experience would bring valuable leadership to our team")
        elif exp_years >= 5:
            notes.append("Your solid experience aligns perfectly with what we're looking for")
        else:
            notes.append("Your skills and enthusiasm would be a great addition to our team")
        
        # Skills-based notes
        candidate_skills = candidate_data.get('skills', [])
        
        if any(skill.lower() in [s.lower() for s in candidate_skills] for skill in ['AI', 'Machine Learning', 'PyTorch', 'TensorFlow']):
            notes.append("especially given your AI/ML expertise")
        elif any(skill.lower() in [s.lower() for s in candidate_skills] for skill in ['React', 'Vue', 'Angular']):
            notes.append("particularly with your frontend development skills")
        elif any(skill.lower() in [s.lower() for s in candidate_skills] for skill in ['Python', 'Django', 'FastAPI']):
            notes.append("especially with your Python development background")
        
        return '. '.join(notes[:2]) + "."
    
    def send_email(self, email: CandidateEmail) -> bool:
        """Send a single email - REAL EMAIL SENDING"""
        
        try:
            print(f"📧 Sending REAL email to {email.candidate_name} ({email.candidate_email})")
            
            # Validate email address
            if not self._is_valid_email(email.candidate_email):
                logging.error(f"Invalid email address: {email.candidate_email}")
                email.status = EmailStatus.FAILED
                return False
            
            # Send real email or simulate based on configuration
            if self.use_real_email:
                success = self._send_via_smtp(email)
            else:
                success = self._simulate_email_send(email)
            
            if success:
                email.status = EmailStatus.SENT
                email.sent_at = datetime.now()
                self.sent_emails.append(email)
                
                if self.use_real_email:
                    print(f"✅ REAL email sent successfully to {email.candidate_name}")
                    print(f"   📧 Check inbox: {email.candidate_email}")
                    print(f"   📝 Subject: {email.subject}")
                else:
                    print(f"✅ Email simulated for {email.candidate_name}")
                
                # Mark as delivered (in real implementation, this would come from webhooks)
                email.status = EmailStatus.DELIVERED
                email.delivered_at = datetime.now()
                
                return True
            else:
                email.status = EmailStatus.FAILED
                self.failed_emails.append(email)
                print(f"❌ Failed to send email to {email.candidate_name}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending email to {email.candidate_email}: {e}")
            email.status = EmailStatus.FAILED
            self.failed_emails.append(email)
            print(f"❌ Email sending error: {e}")
            return False
    
    def _send_via_smtp(self, email: CandidateEmail) -> bool:
        """Send email via SMTP - REAL EMAIL IMPLEMENTATION"""
        
        try:
            print(f"   🔗 Connecting to SMTP server: {self.email_provider.api_endpoint}")
            
            # Parse server and port
            server_parts = self.email_provider.api_endpoint.split(':')
            smtp_server = server_parts[0]
            smtp_port = int(server_parts[1]) if len(server_parts) > 1 else 587
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email.subject
            msg['From'] = f"{self.email_provider.sender_name} <{self.email_provider.sender_email}>"
            msg['To'] = email.candidate_email
            
            # Create HTML and plain text versions
            text_body = email.body
            
            # Convert plain text to HTML with basic formatting
            html_body = email.body.replace('\n', '<br>\n')
            html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
{html_body}
</body>
</html>
"""
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            print(f"   📨 Connecting to {smtp_server}:{smtp_port}")
            
            # Send email via SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.set_debuglevel(0)  # Set to 1 for debug output
            server.starttls()
            
            print(f"   🔐 Authenticating as {self.email_provider.sender_email}")
            server.login(self.email_provider.sender_email, self.email_provider.api_key)
            
            print(f"   📤 Sending email...")
            text = msg.as_string()
            server.sendmail(self.email_provider.sender_email, email.candidate_email, text)
            server.quit()
            
            print(f"   ✅ SMTP delivery successful!")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ SMTP Authentication failed: {e}")
            print(f"   💡 Check your email credentials in the configuration")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"   ❌ Recipient email rejected: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            print(f"   ❌ SMTP server disconnected: {e}")
            return False
        except Exception as e:
            print(f"   ❌ SMTP error: {e}")
            logging.error(f"SMTP error details: {e}", exc_info=True)
            return False
    
    def _simulate_email_send(self, email: CandidateEmail) -> bool:
        """Simulate email sending for demo purposes"""
        time.sleep(0.5)
        import random
        return random.random() < 0.95
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_batch_emails(self, emails: List[CandidateEmail], 
                         stagger_seconds: int = 30) -> Dict[str, Any]:
        """Send multiple emails with staggering"""
        
        results = {
            'sent': [],
            'failed': [],
            'total': len(emails),
            'success_rate': 0.0
        }
        
        mode = "REAL EMAILS" if self.use_real_email else "SIMULATION"
        print(f"📤 Starting batch email send: {len(emails)} emails ({mode})")
        
        for i, email in enumerate(emails):
            try:
                print(f"\n📧 [{i+1}/{len(emails)}] Processing {email.candidate_name}...")
                
                success = self.send_email(email)
                
                if success:
                    results['sent'].append(email.email_id)
                else:
                    results['failed'].append(email.email_id)
                
                # Progress update
                print(f"📊 Progress: {i+1}/{len(emails)} emails processed")
                
                # Stagger emails to avoid rate limits (skip for last email)
                if i < len(emails) - 1:
                    print(f"⏳ Waiting {stagger_seconds} seconds before next email...")
                    time.sleep(stagger_seconds)
                    
            except Exception as e:
                logging.error(f"Error in batch send for email {email.email_id}: {e}")
                results['failed'].append(email.email_id)
                print(f"❌ Batch error for {email.candidate_name}: {e}")
        
        # Calculate success rate
        if results['total'] > 0:
            results['success_rate'] = len(results['sent']) / results['total'] * 100
        
        print(f"\n✅ Batch send completed!")
        print(f"   📊 Sent: {len(results['sent'])}/{results['total']} ({results['success_rate']:.1f}%)")
        print(f"   ❌ Failed: {len(results['failed'])}")
        
        if self.use_real_email and len(results['sent']) > 0:
            print(f"\n📧 CHECK YOUR EMAIL INBOXES!")
            print(f"   Emails sent to:")
            for email in emails:
                if email.email_id in results['sent']:
                    print(f"   ✅ {email.candidate_email}")
        
        return results
    
    def generate_outreach_metrics(self, emails: List[CandidateEmail], 
                                 campaign_id: str) -> OutreachMetrics:
        """Generate metrics for outreach campaign"""
        
        from models.outreach import OutreachMetrics
        
        metrics = OutreachMetrics(campaign_id=campaign_id)
        
        # Count statuses
        status_counts = {}
        for email in emails:
            status = email.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Update metrics
        metrics.total_emails = len(emails)
        metrics.emails_sent = status_counts.get('sent', 0) + status_counts.get('delivered', 0)
        metrics.emails_delivered = status_counts.get('delivered', 0)
        metrics.emails_opened = status_counts.get('opened', 0)
        metrics.emails_replied = status_counts.get('replied', 0)
        metrics.emails_bounced = status_counts.get('bounced', 0)
        metrics.emails_failed = status_counts.get('failed', 0)
        
        # Calculate rates
        if metrics.emails_sent > 0:
            metrics.delivery_rate = metrics.emails_delivered / metrics.emails_sent * 100
        
        if metrics.emails_delivered > 0:
            metrics.open_rate = metrics.emails_opened / metrics.emails_delivered * 100
            metrics.reply_rate = metrics.emails_replied / metrics.emails_delivered * 100
        
        if metrics.total_emails > 0:
            metrics.bounce_rate = metrics.emails_bounced / metrics.total_emails * 100
        
        return metrics
    
    def generate_outreach_summary(self, emails: List[CandidateEmail], 
                                 campaign_id: str, job_title: str,
                                 processing_time: float) -> OutreachSummary:
        """Generate summary of outreach campaign"""
        
        from models.outreach import OutreachSummary
        
        # Count responses by type (simulated for now)
        interested = sum(1 for email in emails if getattr(email, 'response_type', None) == "interested")
        not_interested = sum(1 for email in emails if getattr(email, 'response_type', None) == "not_interested")
        questions = sum(1 for email in emails if getattr(email, 'response_type', None) == "questions")
        no_response = sum(1 for email in emails if not getattr(email, 'response_received', False))
        
        # Count deliveries
        successful_deliveries = sum(1 for email in emails if email.status in [EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.REPLIED])
        failed_deliveries = sum(1 for email in emails if email.status in [EmailStatus.FAILED, EmailStatus.BOUNCED])
        
        # Calculate response rate
        delivered_emails = successful_deliveries
        total_responses = interested + not_interested + questions
        response_rate = (total_responses / delivered_emails * 100) if delivered_emails > 0 else 0
        
        return OutreachSummary(
            campaign_id=campaign_id,
            job_title=job_title,
            total_candidates=len(emails),
            emails_sent=len([e for e in emails if e.status != EmailStatus.PENDING]),
            successful_deliveries=successful_deliveries,
            failed_deliveries=failed_deliveries,
            emails_opened=sum(1 for e in emails if e.status in [EmailStatus.OPENED, EmailStatus.REPLIED]),
            emails_replied=sum(1 for e in emails if e.status == EmailStatus.REPLIED),
            response_rate=response_rate,
            interested_candidates=interested,
            not_interested_candidates=not_interested,
            questions_candidates=questions,
            no_response_candidates=no_response,
            candidates_for_interview=interested + questions,
            follow_ups_needed=no_response,
            processing_time_seconds=processing_time,
            error_count=failed_deliveries
        )