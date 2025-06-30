import re
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from models.response import (
    CandidateResponse, ResponseAnalysis, ResponseType, ResponseSentiment,
    FollowUpAction, InterviewType, InterviewSlot, ScheduledInterview,
    ResponseConfig, ResponseMetrics
)

class ResponseManagementAgent:
    """Agent responsible for processing candidate responses using LLM analysis"""
    
    def __init__(self, config: Optional[ResponseConfig] = None, llm_model: str = "gpt-4"):
        self.config = config or ResponseConfig()
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=2000
        )
        
        # Initialize parsers
        self.analysis_parser = PydanticOutputParser(pydantic_object=ResponseAnalysis)
        
        # Set up analysis prompt
        self._setup_analysis_prompts()
        
        print(f"🤖 Response Management Agent initialized")
        print(f"   LLM Model: {llm_model}")
        print(f"   Confidence Threshold: {self.config.confidence_threshold}")
        print(f"   Auto-response: Interested={self.config.auto_respond_to_interested}, Questions={self.config.auto_respond_to_questions}")
    
    def _setup_analysis_prompts(self):
        """Set up LLM prompts for response analysis"""
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert recruiter's assistant specializing in analyzing candidate email responses. 
            Your job is to accurately classify candidate responses and recommend appropriate follow-up actions.

            RESPONSE TYPES:
            - interested: Candidate explicitly shows interest in the role
            - not_interested: Candidate declines or shows no interest
            - questions: Candidate asks questions about the role/company
            - request_info: Candidate wants more information
            - schedule_later: Candidate is interested but wants to schedule later
            - out_of_office: Automatic out-of-office response
            - spam_complaint: Candidate complains about unsolicited email
            - unknown: Unable to clearly categorize

            SENTIMENT ANALYSIS:
            - positive: Enthusiastic, interested, positive tone
            - neutral: Professional, factual, no clear emotion
            - negative: Dismissive, annoyed, negative tone
            - mixed: Contains both positive and negative elements

            FOLLOW-UP ACTIONS:
            - schedule_interview: Ready to schedule interview
            - send_info: Send additional information
            - answer_questions: Answer specific questions
            - schedule_later: Follow up later for scheduling
            - add_to_future_pool: Add to future opportunities
            - escalate_to_human: Needs human review
            - no_action: No action needed
            - remove_from_list: Remove from communications

            Analyze the response carefully and provide your reasoning."""),
            
            ("human", """
            JOB CONTEXT:
            Job Title: {job_title}
            Company: {company_name}
            Job Description: {job_description}

            CANDIDATE RESPONSE:
            Subject: {response_subject}
            Content: {response_content}

            Please analyze this response and provide a structured analysis.

            {format_instructions}
            """)
        ])
    
    def analyze_response(self, response_text: str, response_subject: str, 
                        job_context: Dict[str, Any]) -> ResponseAnalysis:
        """Analyze a candidate response using LLM"""
        
        try:
            print(f"🔍 Analyzing response: '{response_subject[:50]}...'")
            
            # Prepare prompt
            prompt = self.analysis_prompt.format_messages(
                job_title=job_context.get('job_title', 'Unknown'),
                company_name=job_context.get('company_name', 'Our Company'),
                job_description=job_context.get('job_description', '')[:500],  # Truncate for prompt
                response_subject=response_subject,
                response_content=response_text,
                format_instructions=self.analysis_parser.get_format_instructions()
            )
            
            # Get LLM analysis
            response = self.llm.invoke(prompt)
            analysis = self.analysis_parser.parse(response.content)
            
            print(f"   📊 Classification: {analysis.response_type} (confidence: {analysis.confidence_score:.2f})")
            print(f"   😊 Sentiment: {analysis.sentiment}")
            print(f"   🎯 Action: {analysis.recommended_action}")
            
            return analysis
            
        except Exception as e:
            logging.error(f"Error analyzing response: {e}")
            # Return default analysis on error
            return ResponseAnalysis(
                response_type=ResponseType.UNKNOWN,
                sentiment=ResponseSentiment.NEUTRAL,
                confidence_score=0.0,
                recommended_action=FollowUpAction.ESCALATE_TO_HUMAN,
                priority_level=3,
                reasoning=f"Analysis failed: {str(e)}",
                key_phrases=[]
            )
    
    def process_candidate_response(self, raw_response: Dict[str, Any], 
                                 email_context: Dict[str, Any],
                                 job_context: Dict[str, Any]) -> CandidateResponse:
        """Process a single candidate response"""
        
        try:
            # Extract response content
            response_text = raw_response.get('content', '')
            response_subject = raw_response.get('subject', '')
            candidate_email = raw_response.get('from_email', '')
            
            print(f"📧 Processing response from: {candidate_email}")
            
            # Analyze with LLM
            analysis = self.analyze_response(response_text, response_subject, job_context)
            
            # Extract additional information
            questions = self._extract_questions(response_text)
            availability = self._extract_availability(response_text)
            special_requests = self._extract_special_requests(response_text)
            
            # Determine priority and interview type
            priority = self._calculate_priority(analysis)
            interview_type = self._recommend_interview_type(analysis, job_context)
            
            # Check if human review is needed
            human_review_needed = self._needs_human_review(analysis)
            
            # Create response object
            candidate_response = CandidateResponse(
                response_id=f"resp_{uuid.uuid4().hex[:8]}",
                email_id=email_context.get('email_id', ''),
                candidate_id=email_context.get('candidate_id', ''),
                candidate_name=email_context.get('candidate_name', ''),
                candidate_email=candidate_email,
                
                raw_response=response_text,
                response_subject=response_subject,
                response_received_at=datetime.now(),
                
                response_type=analysis.response_type,
                sentiment=analysis.sentiment,
                confidence_score=analysis.confidence_score,
                
                questions=questions,
                availability=availability,
                special_requests=special_requests,
                
                follow_up_action=analysis.recommended_action,
                interview_type=interview_type,
                priority_level=priority,
                
                processed_by_llm=True,
                human_review_needed=human_review_needed,
                
                job_id=job_context.get('job_id', ''),
                job_title=job_context.get('job_title', '')
            )
            
            print(f"   ✅ Response processed successfully")
            return candidate_response
            
        except Exception as e:
            logging.error(f"Error processing candidate response: {e}")
            
            # Return minimal response on error
            return CandidateResponse(
                response_id=f"resp_{uuid.uuid4().hex[:8]}",
                email_id=email_context.get('email_id', ''),
                candidate_id=email_context.get('candidate_id', ''),
                candidate_name=email_context.get('candidate_name', ''),
                candidate_email=raw_response.get('from_email', ''),
                
                raw_response=raw_response.get('content', ''),
                response_subject=raw_response.get('subject', ''),
                
                response_type=ResponseType.UNKNOWN,
                sentiment=ResponseSentiment.NEUTRAL,
                confidence_score=0.0,
                
                follow_up_action=FollowUpAction.ESCALATE_TO_HUMAN,
                priority_level=5,
                
                processing_errors=[f"Processing failed: {str(e)}"],
                human_review_needed=True,
                
                job_id=job_context.get('job_id', ''),
                job_title=job_context.get('job_title', '')
            )
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from response text"""
        questions = []
        
        # Look for question patterns
        question_patterns = [
            r'[A-Z][^.!?]*\?',  # Sentences ending with ?
            r'(?:can you|could you|would you|do you|is it|are there|what|when|where|why|how)[^.!?]*\?',
            r'(?:I\'d like to know|I want to understand|I\'m curious about|Tell me about)[^.!?]*[.?]'
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            questions.extend([q.strip() for q in matches if len(q.strip()) > 10])
        
        # Remove duplicates and limit
        return list(dict.fromkeys(questions))[:5]
    
    def _extract_availability(self, text: str) -> Optional[str]:
        """Extract availability mentions from text"""
        availability_patterns = [
            r'(?:available|free|open)\s+(?:on|this|next|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(?:can we|let\'s|how about)\s+(?:meet|schedule|talk|call)',
            r'(?:morning|afternoon|evening|am|pm|[0-9]{1,2}:[0-9]{2})',
            r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(?:next week|this week|tomorrow|today)'
        ]
        
        for pattern in availability_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                return text[start:end].strip()
        
        return None
    
    def _extract_special_requests(self, text: str) -> List[str]:
        """Extract special requests or requirements"""
        requests = []
        
        request_patterns = [
            r'(?:I need|I require|I would need|could you provide)[^.!?]*[.?]',
            r'(?:it would be helpful if|I would appreciate if|please)[^.!?]*[.?]',
            r'(?:remote|video|phone|in-person|on-site)[^.!?]*(?:interview|call|meeting)'
        ]
        
        for pattern in request_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requests.extend([r.strip() for r in matches if len(r.strip()) > 10])
        
        return requests[:3]
    
    def _calculate_priority(self, analysis: ResponseAnalysis) -> int:
        """Calculate priority level based on analysis"""
        
        # Start with LLM recommendation
        priority = analysis.priority_level
        
        # Adjust based on response type
        if analysis.response_type == ResponseType.INTERESTED:
            priority = min(priority, 2)  # High priority
        elif analysis.response_type == ResponseType.QUESTIONS:
            priority = min(priority, 3)  # Medium-high priority
        elif analysis.response_type == ResponseType.NOT_INTERESTED:
            priority = max(priority, 4)  # Low priority
        
        # Adjust based on sentiment
        if analysis.sentiment == ResponseSentiment.POSITIVE:
            priority = max(1, priority - 1)
        elif analysis.sentiment == ResponseSentiment.NEGATIVE:
            priority = min(5, priority + 1)
        
        return priority
    
    def _recommend_interview_type(self, analysis: ResponseAnalysis, 
                                 job_context: Dict[str, Any]) -> Optional[InterviewType]:
        """Recommend interview type based on analysis and job context"""
        
        if analysis.response_type not in [ResponseType.INTERESTED, ResponseType.QUESTIONS]:
            return None
        
        # Check for remote/video preferences
        response_text = analysis.key_phrases
        
        if any('remote' in phrase.lower() or 'video' in phrase.lower() for phrase in response_text):
            return InterviewType.VIDEO_INTERVIEW
        elif any('phone' in phrase.lower() or 'call' in phrase.lower() for phrase in response_text):
            return InterviewType.PHONE_SCREEN
        
        # Default based on job level
        job_title = job_context.get('job_title', '').lower()
        if 'senior' in job_title or 'lead' in job_title or 'principal' in job_title:
            return InterviewType.VIDEO_INTERVIEW
        else:
            return InterviewType.PHONE_SCREEN
    
    def _needs_human_review(self, analysis: ResponseAnalysis) -> bool:
        """Determine if response needs human review"""
        
        # Low confidence requires review
        if analysis.confidence_score < self.config.confidence_threshold:
            return True
        
        # Certain response types require review
        if analysis.response_type in [ResponseType.SPAM_COMPLAINT, ResponseType.UNKNOWN]:
            return True
        
        # Complex questions may need review
        if analysis.response_type == ResponseType.QUESTIONS and len(analysis.questions) > 3:
            return True
        
        return False
    
    def generate_follow_up_email(self, response: CandidateResponse, 
                                available_slots: List[InterviewSlot] = None) -> Dict[str, str]:
        """Generate follow-up email based on response type"""
        
        try:
            if response.follow_up_action == FollowUpAction.SCHEDULE_INTERVIEW:
                return self._generate_interview_scheduling_email(response, available_slots)
            elif response.follow_up_action == FollowUpAction.ANSWER_QUESTIONS:
                return self._generate_question_response_email(response)
            elif response.follow_up_action == FollowUpAction.SEND_INFO:
                return self._generate_info_email(response)
            elif response.follow_up_action == FollowUpAction.ADD_TO_FUTURE_POOL:
                return self._generate_future_opportunities_email(response)
            else:
                return {"subject": "", "body": "", "action": "no_email"}
                
        except Exception as e:
            logging.error(f"Error generating follow-up email: {e}")
            return {"subject": "Error", "body": f"Error generating email: {e}", "action": "error"}
    
    def _generate_interview_scheduling_email(self, response: CandidateResponse, 
                                           available_slots: List[InterviewSlot] = None) -> Dict[str, str]:
        """Generate email for interview scheduling"""
        
        subject = f"Interview Opportunity - {response.job_title} at {response.candidate_name}"
        
        # Generate time slots
        if available_slots:
            slots_text = "\n".join([
                f"• {slot.start_time.strftime('%A, %B %d at %I:%M %p')} ({slot.interview_type.replace('_', ' ').title()})"
                for slot in available_slots[:3]
            ])
        else:
            # Generate default slots
            now = datetime.now()
            slots_text = "\n".join([
                f"• {(now + timedelta(days=i*2, hours=10)).strftime('%A, %B %d at %I:%M %p')}"
                for i in range(1, 4)
            ])
        
        body = f"""Dear {response.candidate_name},

Thank you for your interest in the {response.job_title} position! I'm excited to move forward with the interview process.

Based on your response, I'd like to schedule our first interview. Here are some available time slots:

{slots_text}

Please let me know which time works best for you, or feel free to suggest alternative times.

The interview will be conducted via video call and should take approximately 60 minutes. I'll send you the meeting details once we confirm the time.

Looking forward to speaking with you soon!

Best regards,
The Recruiting Team"""
        
        return {"subject": subject, "body": body, "action": "schedule_interview"}
    
    def _generate_question_response_email(self, response: CandidateResponse) -> Dict[str, str]:
        """Generate email answering candidate questions"""
        
        subject = f"Re: {response.job_title} - Answers to Your Questions"
        
        questions_text = ""
        if response.questions:
            questions_text = "\n\n".join([
                f"Q: {q}\nA: I'd be happy to discuss this in detail during our interview."
                for q in response.questions[:3]
            ])
        
        body = f"""Dear {response.candidate_name},

Thank you for your interest in the {response.job_title} position and for your thoughtful questions.

{questions_text}

I believe a conversation would be the best way to address all your questions thoroughly. Would you be available for a brief call this week to discuss the role in more detail?

Please let me know your availability, and I'll be happy to schedule a time that works for you.

Best regards,
The Recruiting Team"""
        
        return {"subject": subject, "body": body, "action": "answer_questions"}
    
    def _generate_info_email(self, response: CandidateResponse) -> Dict[str, str]:
        """Generate email with additional information"""
        
        subject = f"Additional Information - {response.job_title} Position"
        
        body = f"""Dear {response.candidate_name},

Thank you for your interest in learning more about the {response.job_title} position.

I'd be happy to provide you with additional details about:
• The role and day-to-day responsibilities
• Our team structure and company culture
• Benefits and compensation package
• Growth opportunities

Would you be available for a brief conversation to discuss these details? I'm confident this will help you get a better understanding of the opportunity.

Please let me know your availability for a 15-20 minute call.

Best regards,
The Recruiting Team"""
        
        return {"subject": subject, "body": body, "action": "send_info"}
    
    def _generate_future_opportunities_email(self, response: CandidateResponse) -> Dict[str, str]:
        """Generate email for future opportunities"""
        
        subject = f"Thank You - Future Opportunities at Our Company"
        
        body = f"""Dear {response.candidate_name},

Thank you for taking the time to respond to our outreach about the {response.job_title} position.

I understand that the timing isn't right for you currently, but I'd love to keep you in mind for future opportunities that might be a better fit.

I'll add you to our talent network and reach out when we have positions that match your background and interests.

Thank you again for your time, and I hope we can connect in the future!

Best regards,
The Recruiting Team"""
        
        return {"subject": subject, "body": body, "action": "future_opportunities"}
    
    def schedule_interview(self, response: CandidateResponse, 
                          selected_slot: InterviewSlot,
                          interviewer_details: Dict[str, str]) -> ScheduledInterview:
        """Schedule an interview for a candidate"""
        
        try:
            # Create scheduled interview
            interview = ScheduledInterview(
                interview_id=f"interview_{uuid.uuid4().hex[:8]}",
                candidate_id=response.candidate_id,
                candidate_name=response.candidate_name,
                candidate_email=response.candidate_email,
                
                interview_type=selected_slot.interview_type,
                scheduled_time=selected_slot.start_time,
                duration_minutes=60,
                interviewer=selected_slot.interviewer,
                interviewer_email=interviewer_details.get('email', ''),
                
                meeting_link=self._generate_meeting_link(selected_slot),
                meeting_instructions=self._generate_meeting_instructions(selected_slot),
                
                job_id=response.job_id,
                job_title=response.job_title
            )
            
            print(f"📅 Interview scheduled: {response.candidate_name} at {selected_slot.start_time}")
            
            return interview
            
        except Exception as e:
            logging.error(f"Error scheduling interview: {e}")
            raise
    
    def _generate_meeting_link(self, slot: InterviewSlot) -> str:
        """Generate meeting link based on interview type"""
        
        if slot.interview_type == InterviewType.VIDEO_INTERVIEW:
            # In real implementation, integrate with Zoom/Teams/Meet API
            return f"https://zoom.us/j/{uuid.uuid4().hex[:10]}"
        elif slot.interview_type == InterviewType.PHONE_SCREEN:
            return "Phone interview - number will be provided"
        else:
            return slot.location or "Location TBD"
    
    def _generate_meeting_instructions(self, slot: InterviewSlot) -> str:
        """Generate meeting instructions"""
        
        if slot.interview_type == InterviewType.VIDEO_INTERVIEW:
            return """Please join the video call 5 minutes early to test your connection. 
            Ensure you have a quiet environment and good lighting. 
            Have your resume handy and be prepared to discuss your experience."""
        elif slot.interview_type == InterviewType.PHONE_SCREEN:
            return """Please ensure you're in a quiet location with good phone reception. 
            Have your resume available for reference during our conversation."""
        else:
            return "Additional details will be provided closer to the interview date."
    
    def generate_interview_confirmation_email(self, interview: ScheduledInterview) -> Dict[str, str]:
        """Generate interview confirmation email"""
        
        subject = f"Interview Confirmed - {interview.job_title} on {interview.scheduled_time.strftime('%B %d, %Y')}"
        
        # Format date and time
        interview_date = interview.scheduled_time.strftime('%A, %B %d, %Y')
        interview_time = interview.scheduled_time.strftime('%I:%M %p')
        
        body = f"""Dear {interview.candidate_name},

Great news! Your interview for the {interview.job_title} position has been confirmed.

INTERVIEW DETAILS:
📅 Date: {interview_date}
🕐 Time: {interview_time}
⏱️ Duration: {interview.duration_minutes} minutes
👤 Interviewer: {interview.interviewer}
📍 Type: {interview.interview_type.replace('_', ' ').title()}

MEETING INFORMATION:
{interview.meeting_link}

PREPARATION:
{interview.meeting_instructions}

Please confirm your attendance by replying to this email. If you need to reschedule, please let me know as soon as possible.

Looking forward to speaking with you!

Best regards,
{interview.interviewer}
{interview.interviewer_email}"""
        
        return {"subject": subject, "body": body, "action": "confirm_interview"}
    
    def generate_response_metrics(self, responses: List[CandidateResponse], 
                                 campaign_id: str) -> ResponseMetrics:
        """Generate metrics for response management"""
        
        metrics = ResponseMetrics(campaign_id=campaign_id)
        
        # Basic counts
        metrics.total_responses = len(responses)
        metrics.responses_processed = sum(1 for r in responses if r.processed_by_llm)
        
        # Response type breakdown
        for response in responses:
            if response.response_type == ResponseType.INTERESTED:
                metrics.interested_responses += 1
            elif response.response_type == ResponseType.NOT_INTERESTED:
                metrics.not_interested_responses += 1
            elif response.response_type == ResponseType.QUESTIONS:
                metrics.questions_responses += 1
            else:
                metrics.other_responses += 1
        
        # Processing metrics
        metrics.auto_processed = sum(1 for r in responses if not r.human_review_needed)
        metrics.human_review_needed = sum(1 for r in responses if r.human_review_needed)
        metrics.processing_errors = sum(len(r.processing_errors) for r in responses)
        
        # Interview metrics
        metrics.interviews_scheduled = sum(1 for r in responses if r.interview_scheduled)
        
        # Calculate rates
        if metrics.total_responses > 0:
            metrics.successful_automation_rate = metrics.auto_processed / metrics.total_responses * 100
        
        if metrics.responses_processed > 0:
            total_confidence = sum(r.confidence_score for r in responses if r.processed_by_llm)
            metrics.avg_confidence_score = total_confidence / metrics.responses_processed
        
        return metrics