# agents/interview_agent.py
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

from agents.base_agent import BaseAgent
from models.candidate import Candidate, CandidateStatus
from models.job_description import JobDescription
from config.settings import settings
from utils.email_service import EmailService
from utils.screening_questions_generator import ScreeningQuestionsGenerator

class InterviewAgent(BaseAgent):
    """Agent responsible for conducting initial candidate outreach and screening"""
    
    def __init__(self):
        super().__init__("Interview Agent")
        self.conversation_history = {}  # Track conversations with candidates
        
        # Initialize email service
        self.email_service = EmailService(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            from_name=settings.EMAIL_FROM_NAME
        )
        
        # Initialize screening questions generator
        self.questions_generator = ScreeningQuestionsGenerator(llm=self.llm)
        
        # Check if email is properly configured
        self.email_enabled = settings.validate_email_config()
        if self.email_enabled:
            self.log("Email service initialized successfully")
        else:
            self.log("Email service disabled - check configuration")
        
    def _setup_email_config(self) -> Dict:
        """Setup email configuration - we'll implement this step by step"""
        # For now, return empty config - we'll add SMTP settings later
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': '',  # Will be set from environment
            'password': ''  # Will be set from environment
        }
    
    def execute(self, input_data: Dict) -> Dict:
        """
        Main execution method for interview agent
        
        Args:
            input_data: {
                'candidate': Candidate,
                'job_description': JobDescription,
                'action': str ('send_initial_email', 'send_questions', 'process_response')
            }
        
        Returns:
            Dict containing execution results
        """
        try:
            candidate = input_data['candidate']
            job_description = input_data['job_description']
            action = input_data.get('action', 'send_initial_email')
            
            self.log(f"Starting interview process for {candidate.name} - Action: {action}")
            
            if action == 'send_initial_email':
                return self._send_initial_contact_email(candidate, job_description)
            elif action == 'send_questions':
                return self._send_screening_questions(candidate, job_description)
            elif action == 'process_response':
                response_text = input_data.get('response_text', '')
                return self._process_candidate_response(candidate, response_text)
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            self.log(f"Error in interview agent execution: {str(e)}")
            raise e
    
    def _send_initial_contact_email(self, candidate: Candidate, job_description: JobDescription) -> Dict:
        """Send initial contact email to candidate"""
        
        # Generate personalized email content
        email_content = self._generate_initial_email(candidate, job_description)
        
        result = {
            'status': 'email_generated',
            'email_content': email_content,
            'candidate_id': candidate.id,
            'next_action': 'send_questions'
        }
        
        # If email is enabled, actually send the email
        if self.email_enabled:
            try:
                # Add signature to email body
                body_with_signature = email_content['body'] + f"\n\n{settings.EMAIL_SIGNATURE.format(from_name=settings.EMAIL_FROM_NAME)}"
                
                email_result = self.email_service.send_email(
                    to_email=candidate.email,
                    to_name=candidate.name,
                    subject=email_content['subject'],
                    body=body_with_signature
                )
                
                result['email_sent'] = email_result['success']
                result['email_status'] = email_result['message']
                result['email_timestamp'] = email_result.get('timestamp')
                
                if email_result['success']:
                    self.log(f"✅ Email sent successfully to {candidate.name} ({candidate.email})")
                    result['status'] = 'email_sent'
                    
                    # Store in conversation history
                    self._store_email_in_history(candidate.id, 'initial_contact', email_content, email_result)
                    
                else:
                    self.log(f"❌ Failed to send email to {candidate.name}: {email_result['message']}")
                    result['status'] = 'email_failed'
                    result['error'] = email_result.get('error', 'Unknown error')
                    result['suggestion'] = email_result.get('suggestion', '')
                    
            except Exception as e:
                self.log(f"❌ Unexpected error sending email to {candidate.name}: {str(e)}")
                result['email_sent'] = False
                result['status'] = 'email_error'
                result['error'] = str(e)
        else:
            self.log(f"📧 Email generated for {candidate.name} (sending disabled)")
            result['email_sent'] = False
            result['email_status'] = 'Email sending is disabled - check configuration'
        
        return result
    
    def _generate_initial_email(self, candidate: Candidate, job_description: JobDescription) -> Dict:
        """Generate personalized initial contact email using LLM"""
        
        email_prompt = PromptTemplate(
            input_variables=["candidate_name", "job_title", "company", "candidate_skills"],
            template="""
            Generate a professional and personalized initial contact email for a job candidate.
            
            Candidate Details:
            - Name: {candidate_name}
            - Skills: {candidate_skills}
            
            Job Details:
            - Position: {job_title}
            - Company: {company}
            
            Requirements:
            1. Keep it professional but friendly
            2. Mention specific skills that caught our attention
            3. Explain next steps in the process
            4. Ask about their availability for a brief screening call
            5. Include a request to confirm their interest
            
            Return the response as JSON with the following structure:
            {{
                "subject": "Email subject line",
                "body": "Email body content",
                "call_to_action": "Specific next step we want them to take"
            }}
            
            Make it engaging and personalized, not generic.
            """
        )
        
        try:
            prompt = email_prompt.format(
                candidate_name=candidate.name,
                job_title=job_description.title,
                company=job_description.company,
                candidate_skills=", ".join(candidate.skills[:5])  # Top 5 skills
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            email_data = json.loads(response.content)
            
            return email_data
            
        except Exception as e:
            self.log(f"Error generating email content: {str(e)}")
            # Fallback to template
            return self._fallback_email_template(candidate, job_description)
    
    def _fallback_email_template(self, candidate: Candidate, job_description: JobDescription) -> Dict:
        """Fallback email template if LLM generation fails"""
        return {
            "subject": f"Exciting Opportunity at {job_description.company} - {job_description.title}",
            "body": f"""Dear {candidate.name},

I hope this email finds you well. I came across your profile and was impressed by your background, particularly your experience with {', '.join(candidate.skills[:3])}.

We have an exciting opportunity for a {job_description.title} position at {job_description.company} that I believe would be a great fit for your skills and experience.

I'd love to schedule a brief 15-20 minute call to discuss this opportunity further and learn more about your career goals.

Are you available for a quick call this week or next? Please let me know a few time slots that work best for you.

Looking forward to hearing from you!

Best regards,
Recruitment Team""",
            "call_to_action": "Please reply with your availability for a brief screening call"
        }
    
    def _send_screening_questions(self, candidate: Candidate, job_description: JobDescription) -> Dict:
        """Send screening questions to candidate (placeholder for now)"""
        # We'll implement this in the next step
        self.log(f"Preparing screening questions for {candidate.name}")
    def _send_screening_questions(self, candidate: Candidate, job_description: JobDescription) -> Dict:
        """Generate and send screening questions to candidate"""
        
        self.log(f"Generating screening questions for {candidate.name}")
        
        try:
            # Generate personalized screening questions
            questions_data = self.questions_generator.generate_screening_questions(
                candidate=candidate,
                job_description=job_description,
                num_questions=5,
                categories=['technical', 'experience', 'motivation', 'availability']
            )
            
            # Format questions for email
            questions_text = self.questions_generator.format_questions_for_email(questions_data)
            
            # Create email content
            email_content = self._create_screening_questions_email(
                candidate, job_description, questions_text, questions_data
            )
            
            result = {
                'status': 'questions_generated',
                'questions_data': questions_data,
                'email_content': email_content,
                'candidate_id': candidate.id,
                'next_action': 'process_response'
            }
            
            # Send email if enabled
            if self.email_enabled:
                try:
                    # Add signature to email body
                    body_with_signature = email_content['body'] + f"\n\n{settings.EMAIL_SIGNATURE.format(from_name=settings.EMAIL_FROM_NAME)}"
                    
                    email_result = self.email_service.send_email(
                        to_email=candidate.email,
                        to_name=candidate.name,
                        subject=email_content['subject'],
                        body=body_with_signature
                    )
                    
                    result['email_sent'] = email_result['success']
                    result['email_status'] = email_result['message']
                    result['email_timestamp'] = email_result.get('timestamp')
                    
                    if email_result['success']:
                        self.log(f"✅ Screening questions sent to {candidate.name}")
                        result['status'] = 'questions_sent'
                        
                        # Store in conversation history
                        self._store_email_in_history(candidate.id, 'screening_questions', email_content, email_result)
                        
                        # Store questions data for later reference
                        self._store_screening_questions(candidate.id, questions_data)
                        
                    else:
                        self.log(f"❌ Failed to send screening questions to {candidate.name}")
                        result['status'] = 'questions_email_failed'
                        result['error'] = email_result.get('error', 'Unknown error')
                        
                except Exception as e:
                    self.log(f"❌ Error sending screening questions: {str(e)}")
                    result['email_sent'] = False
                    result['status'] = 'questions_email_error'
                    result['error'] = str(e)
            else:
                self.log(f"📧 Screening questions generated for {candidate.name} (sending disabled)")
                result['email_sent'] = False
                result['email_status'] = 'Email sending is disabled'
            
            return result
            
        except Exception as e:
            self.log(f"Error generating screening questions: {str(e)}")
            return {
                'status': 'questions_generation_failed',
                'error': str(e),
                'candidate_id': candidate.id
            }
    
    def _create_screening_questions_email(self, candidate: Candidate, job_description: JobDescription, 
                                        questions_text: str, questions_data: Dict) -> Dict:
        """Create email content for screening questions"""
        
        subject = f"Next Steps: {job_description.title} Opportunity - Quick Questions"
        
        body = f"""Dear {candidate.name},

Thank you for your interest in the {job_description.title} position at {job_description.company}!

Based on your background and the role requirements, I'd like to move forward with a few screening questions to better understand your experience and interests.

{questions_text}

These questions will help us prepare for our upcoming conversation and ensure we make the best use of our time together.

Please feel free to respond directly to this email with your answers. I'm looking forward to learning more about your experience and discussing how this opportunity aligns with your career goals.

If you have any questions about the role or the process, please don't hesitate to ask!

Best regards,
{settings.EMAIL_FROM_NAME}
{job_description.company}"""

        return {
            'subject': subject,
            'body': body,
            'call_to_action': 'Please respond with your answers to the screening questions'
        }
    
    def _store_screening_questions(self, candidate_id: str, questions_data: Dict):
        """Store screening questions data for later reference"""
        if not hasattr(self, 'screening_questions_data'):
            self.screening_questions_data = {}
        
        self.screening_questions_data[candidate_id] = {
            'timestamp': datetime.now().isoformat(),
            'questions_data': questions_data
        }
    
    def get_screening_questions(self, candidate_id: str) -> Dict:
        """Get stored screening questions for a candidate"""
        if hasattr(self, 'screening_questions_data'):
            return self.screening_questions_data.get(candidate_id, {})
        return {}
    
    def generate_custom_questions(self, candidate: Candidate, job_description: JobDescription,
                                categories: List[str] = None, num_questions: int = 5) -> Dict:
        """Generate custom screening questions with specific parameters"""
        
        return self.questions_generator.generate_screening_questions(
            candidate=candidate,
            job_description=job_description,
            num_questions=num_questions,
            categories=categories or ['technical', 'experience', 'motivation']
        )
    
    def _process_candidate_response(self, candidate: Candidate, response_text: str) -> Dict:
        """Process candidate's response (placeholder for now)"""
        # We'll implement this in the next step
        self.log(f"Processing response from {candidate.name}")
        return {'status': 'response_processed'}
    
    def test_email_configuration(self) -> Dict:
        """Test email configuration and connectivity"""
        if not self.email_enabled:
            return {
                'success': False,
                'message': 'Email service is not configured'
            }
        
        return self.email_service.test_connection()
    
    def _store_email_in_history(self, candidate_id: str, email_type: str, email_content: Dict, email_result: Dict):
        """Store email in conversation history"""
        if candidate_id not in self.conversation_history:
            self.conversation_history[candidate_id] = []
        
        self.conversation_history[candidate_id].append({
            'timestamp': datetime.now().isoformat(),
            'type': email_type,
            'subject': email_content['subject'],
            'body': email_content['body'],
            'sent_successfully': email_result['success'],
            'email_result': email_result
        })
    
    def get_conversation_history(self, candidate_id: str) -> List[Dict]:
        """Get conversation history for a candidate"""
        return self.conversation_history.get(candidate_id, [])
    
    def send_custom_email(self, candidate: Candidate, subject: str, body: str, email_type: str = 'custom') -> Dict:
        """Send a custom email to a candidate"""
        if not self.email_enabled:
            return {
                'success': False,
                'message': 'Email service is not configured'
            }
        
        try:
            # Add signature
            body_with_signature = body + f"\n\n{settings.EMAIL_SIGNATURE.format(from_name=settings.EMAIL_FROM_NAME)}"
            
            email_result = self.email_service.send_email(
                to_email=candidate.email,
                to_name=candidate.name,
                subject=subject,
                body=body_with_signature
            )
            
            if email_result['success']:
                self.log(f"✅ Custom email sent to {candidate.name}")
                
                # Store in history
                email_content = {'subject': subject, 'body': body}
                self._store_email_in_history(candidate.id, email_type, email_content, email_result)
            else:
                self.log(f"❌ Failed to send custom email to {candidate.name}")
            
            return email_result
            
        except Exception as e:
            error_result = {
                'success': False,
                'message': f'Error sending custom email: {str(e)}',
                'error': str(e)
            }
            self.log(f"❌ Error sending custom email to {candidate.name}: {str(e)}")
            return error_result
    
    def send_test_email(self, test_email: str) -> Dict:
        """Send a test email to verify email functionality"""
        if not self.email_enabled:
            return {
                'success': False,
                'message': 'Email service is not configured'
            }
        
        return self.email_service.send_test_email(test_email)

# Test function to demonstrate usage
def test_interview_agent():
    """Test function to show how the interview agent works"""
    from models.candidate import Candidate
    from models.job_description import JobDescription
    
    # Create test candidate
    candidate = Candidate(
        name="John Doe",
        email="john.doe@email.com",
        skills=["Python", "Machine Learning", "TensorFlow", "AWS"],
        experience_years=3.5
    )
    
    # Create test job description
    job_desc = JobDescription(
        title="Senior AI Engineer",
        company="TechCorp AI",
        description="We're looking for an experienced AI engineer...",
        required_skills=["Python", "Machine Learning", "Deep Learning"]
    )
    
    # Initialize agent
    agent = InterviewAgent()
    
    # Test initial email generation
    result = agent.execute({
        'candidate': candidate,
        'job_description': job_desc,
        'action': 'send_initial_email'
    })
    
    print("=== Generated Email ===")
    print(f"Subject: {result['email_content']['subject']}")
    print(f"Body: {result['email_content']['body']}")
    print(f"Call to Action: {result['email_content']['call_to_action']}")

if __name__ == "__main__":
    test_interview_agent()