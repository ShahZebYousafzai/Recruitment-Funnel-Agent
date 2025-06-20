# utils/email_templates.py
from typing import Dict

class EmailTemplates:
    """Collection of email templates for different recruitment scenarios"""
    
    @staticmethod
    def initial_contact_template(candidate_name: str, job_title: str, company: str, 
                               candidate_skills: str, hiring_manager: str = "Hiring Team") -> Dict[str, str]:
        """Template for initial candidate contact"""
        return {
            "subject": f"Exciting {job_title} Opportunity at {company} - Let's Connect!",
            "body": f"""Dear {candidate_name},

I hope this email finds you well! I came across your profile and was genuinely impressed by your background, particularly your expertise in {candidate_skills}.

We have an exciting {job_title} position at {company} that I believe would be a perfect match for your skill set. Your experience really stands out and aligns well with what we're looking for.

Here's what makes this opportunity special:
• Work with cutting-edge technology and innovative projects
• Collaborative team environment with growth opportunities
• Competitive compensation and comprehensive benefits
• Flexible work arrangements and professional development support

I'd love to schedule a brief 15-20 minute call to discuss this opportunity in detail and learn more about your career goals and interests.

Would you be available for a quick screening call this week or next? Please share 2-3 time slots that work best for you, and I'll send over a calendar invite.

Looking forward to connecting with you!""",
            "call_to_action": "Please reply with 2-3 time slots for a brief screening call"
        }
    
    @staticmethod
    def follow_up_template(candidate_name: str, job_title: str, company: str, 
                         days_since_last_contact: int = 3) -> Dict[str, str]:
        """Template for follow-up emails"""
        return {
            "subject": f"Following up: {job_title} Opportunity at {company}",
            "body": f"""Dear {candidate_name},

I hope you're doing well! I wanted to follow up on my previous email about the {job_title} position at {company}.

I understand you're likely considering multiple opportunities, and I wanted to make sure this didn't get lost in your inbox. We're genuinely excited about the possibility of having you join our team.

A few quick highlights about this role:
• Immediate impact on innovative projects
• Strong team culture and mentorship opportunities
• Competitive package with growth potential

If you're interested, I'd still love to schedule a brief call to discuss the opportunity. Even if the timing isn't right now, I'd be happy to keep you in mind for future positions that might be a better fit.

Would a 15-minute call work for you this week?""",
            "call_to_action": "Please let me know if you'd like to schedule a brief call"
        }
    
    @staticmethod
    def screening_questions_template(candidate_name: str, job_title: str, 
                                   questions: list) -> Dict[str, str]:
        """Template for sending screening questions"""
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        return {
            "subject": f"Quick Questions: {job_title} Opportunity",
            "body": f"""Dear {candidate_name},

Thank you for your interest in the {job_title} position! To help us move forward efficiently, I'd like to ask you a few quick questions.

Please find the questions below and feel free to respond directly to this email:

{questions_text}

These questions will help us understand your background better and ensure we're making the best use of everyone's time during our call.

Feel free to be as detailed or concise as you'd like in your responses. I'm looking forward to learning more about your experience!""",
            "call_to_action": "Please respond with your answers to the questions above"
        }
    
    @staticmethod
    def interview_invitation_template(candidate_name: str, job_title: str, company: str,
                                    interview_date: str, interview_time: str, 
                                    interview_type: str = "video call") -> Dict[str, str]:
        """Template for interview invitations"""
        return {
            "subject": f"Interview Invitation: {job_title} at {company}",
            "body": f"""Dear {candidate_name},

Great news! We'd like to invite you for an interview for the {job_title} position at {company}.

Interview Details:
• Date: {interview_date}
• Time: {interview_time}
• Format: {interview_type}
• Duration: Approximately 45-60 minutes

What to expect:
• Discussion about your background and experience
• Deep dive into the role and team structure
• Technical discussion relevant to the position
• Q&A session for any questions you might have

I'll send a calendar invite shortly with the meeting details. Please confirm your availability at your earliest convenience.

If you have any questions or need to reschedule, please don't hesitate to reach out.

Looking forward to our conversation!""",
            "call_to_action": "Please confirm your availability for the interview"
        }
    
    @staticmethod
    def rejection_template(candidate_name: str, job_title: str, company: str,
                         feedback: str = "") -> Dict[str, str]:
        """Template for rejection emails"""
        feedback_section = f"\n\nFeedback:\n{feedback}" if feedback else ""
        
        return {
            "subject": f"Update on Your {job_title} Application",
            "body": f"""Dear {candidate_name},

Thank you for taking the time to apply for the {job_title} position at {company} and for your interest in joining our team.

After careful consideration, we have decided to move forward with other candidates whose experience more closely aligns with our current needs.

This was a difficult decision, as we were impressed by your background and qualifications. We encourage you to apply for future positions that match your expertise.{feedback_section}

We'll keep your profile on file and reach out if we have opportunities that would be a better fit for your skills and experience.

Thank you again for your time and interest in {company}. We wish you the best in your job search!""",
            "call_to_action": "Feel free to apply for future opportunities that match your background"
        }
    
    @staticmethod
    def offer_template(candidate_name: str, job_title: str, company: str,
                      salary_range: str = "", start_date: str = "") -> Dict[str, str]:
        """Template for job offers"""
        salary_section = f"• Starting salary: {salary_range}\n" if salary_range else ""
        start_section = f"• Proposed start date: {start_date}\n" if start_date else ""
        
        return {
            "subject": f"Job Offer: {job_title} at {company}",
            "body": f"""Dear {candidate_name},

Congratulations! We're thrilled to extend an offer for the {job_title} position at {company}.

We were very impressed with your background, experience, and how well you'd fit with our team culture. We believe you'll make a significant impact in this role.

Offer Details:
{salary_section}{start_section}• Comprehensive benefits package
• Professional development opportunities
• Flexible work arrangements

We're excited about the possibility of you joining our team and contributing to our mission. Please review the attached formal offer letter for complete details.

We'd love to schedule a call to discuss the offer and answer any questions you might have. Please let me know your availability in the next few days.

Welcome to the team (pending your acceptance)!""",
            "call_to_action": "Please review the offer and let me know when you're available to discuss"
        }
    
    @staticmethod
    def custom_template(subject: str, greeting: str, main_content: str, 
                       call_to_action: str, candidate_name: str = "there") -> Dict[str, str]:
        """Template for custom emails"""
        return {
            "subject": subject,
            "body": f"""Dear {candidate_name},

{greeting}

{main_content}

{call_to_action}""",
            "call_to_action": call_to_action
        }

# Example usage functions
def get_template_by_type(template_type: str, **kwargs) -> Dict[str, str]:
    """Get a template by type with provided parameters"""
    templates = {
        'initial_contact': EmailTemplates.initial_contact_template,
        'follow_up': EmailTemplates.follow_up_template,
        'screening_questions': EmailTemplates.screening_questions_template,
        'interview_invitation': EmailTemplates.interview_invitation_template,
        'rejection': EmailTemplates.rejection_template,
        'offer': EmailTemplates.offer_template,
        'custom': EmailTemplates.custom_template
    }
    
    if template_type not in templates:
        raise ValueError(f"Unknown template type: {template_type}")
    
    return templates[template_type](**kwargs)