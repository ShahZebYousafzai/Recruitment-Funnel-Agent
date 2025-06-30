from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum

class ResponseType(str, Enum):
    """Types of candidate responses"""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    QUESTIONS = "questions"
    REQUEST_INFO = "request_info"
    SCHEDULE_LATER = "schedule_later"
    OUT_OF_OFFICE = "out_of_office"
    SPAM_COMPLAINT = "spam_complaint"
    UNKNOWN = "unknown"

class ResponseSentiment(str, Enum):
    """Sentiment analysis of responses"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"

class InterviewType(str, Enum):
    """Types of interviews"""
    PHONE_SCREEN = "phone_screen"
    VIDEO_INTERVIEW = "video_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    ON_SITE_INTERVIEW = "on_site_interview"
    PANEL_INTERVIEW = "panel_interview"

class FollowUpAction(str, Enum):
    """Required follow-up actions"""
    SCHEDULE_INTERVIEW = "schedule_interview"
    SEND_INFO = "send_info"
    ANSWER_QUESTIONS = "answer_questions"
    SCHEDULE_LATER = "schedule_later"
    ADD_TO_FUTURE_POOL = "add_to_future_pool"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    NO_ACTION = "no_action"
    REMOVE_FROM_LIST = "remove_from_list"

class CandidateResponse(BaseModel):
    """Individual candidate response structure"""
    response_id: str = Field(description="Unique response identifier")
    email_id: str = Field(description="Original email ID this responds to")
    candidate_id: str = Field(description="Candidate identifier")
    candidate_name: str = Field(description="Candidate name")
    candidate_email: str = Field(description="Candidate email")
    
    # Response content
    raw_response: str = Field(description="Original response text")
    response_subject: str = Field(default="", description="Email subject line")
    response_received_at: datetime = Field(default_factory=datetime.now)
    
    # LLM Analysis Results
    response_type: ResponseType = Field(description="Classified response type")
    sentiment: ResponseSentiment = Field(description="Response sentiment")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    
    # Extracted Information
    questions: List[str] = Field(default_factory=list, description="Questions asked by candidate")
    availability: Optional[str] = Field(default=None, description="Candidate availability mentions")
    preferred_time: Optional[str] = Field(default=None, description="Preferred interview time")
    special_requests: List[str] = Field(default_factory=list, description="Special requests or requirements")
    
    # Decision and Actions
    follow_up_action: FollowUpAction = Field(description="Required follow-up action")
    interview_type: Optional[InterviewType] = Field(default=None, description="Recommended interview type")
    priority_level: int = Field(default=3, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    
    # Scheduling Information
    suggested_interview_slots: List[str] = Field(default_factory=list, description="Suggested interview time slots")
    interview_scheduled: bool = Field(default=False)
    scheduled_interview_time: Optional[datetime] = Field(default=None)
    
    # Processing metadata
    processed_by_llm: bool = Field(default=False)
    processing_errors: List[str] = Field(default_factory=list)
    human_review_needed: bool = Field(default=False)
    
    # Communication tracking
    follow_up_sent: bool = Field(default=False)
    follow_up_sent_at: Optional[datetime] = Field(default=None)
    response_count: int = Field(default=1, description="Number of responses from this candidate")
    
    # Job context
    job_id: str = Field(description="Related job ID")
    job_title: str = Field(description="Job title")

class ResponseAnalysis(BaseModel):
    """LLM analysis results for a response"""
    response_type: ResponseType
    sentiment: ResponseSentiment
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Extracted entities
    questions: List[str] = Field(default_factory=list)
    availability_mentions: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)
    
    # Recommendations
    recommended_action: FollowUpAction
    priority_level: int = Field(ge=1, le=5)
    interview_type: Optional[InterviewType] = None
    
    # Reasoning
    reasoning: str = Field(description="LLM reasoning for classification")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases that influenced decision")

class InterviewSlot(BaseModel):
    """Available interview time slot"""
    slot_id: str
    start_time: datetime
    end_time: datetime
    interviewer: str
    interview_type: InterviewType
    location: Optional[str] = Field(default=None, description="Physical location or video link")
    available: bool = Field(default=True)
    timezone: str = Field(default="UTC")

class ScheduledInterview(BaseModel):
    """Scheduled interview details"""
    interview_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    
    # Interview details
    interview_type: InterviewType
    scheduled_time: datetime
    duration_minutes: int = Field(default=60)
    interviewer: str
    interviewer_email: str
    
    # Meeting details
    meeting_link: Optional[str] = Field(default=None)
    meeting_location: Optional[str] = Field(default=None)
    meeting_instructions: Optional[str] = Field(default=None)
    
    # Job context
    job_id: str
    job_title: str
    
    # Status
    confirmation_sent: bool = Field(default=False)
    confirmed_by_candidate: bool = Field(default=False)
    calendar_event_created: bool = Field(default=False)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="system")

class ResponseManagementState(TypedDict, total=False):
    """State for response management stage"""
    # Input from outreach stage
    sent_emails: List[Dict[str, Any]]
    email_statuses: Dict[str, str]
    job_requirements: Dict[str, Any]
    
    # Response collection
    incoming_responses: List[Dict[str, Any]]  # Raw email responses
    processed_responses: List[Dict[str, Any]]  # CandidateResponse as dicts
    
    # Processing status
    current_response_index: int
    total_responses: int
    processing_complete: bool
    
    # LLM Analysis results
    analysis_results: List[Dict[str, Any]]  # ResponseAnalysis as dicts
    
    # Scheduling
    available_interview_slots: List[Dict[str, Any]]  # InterviewSlot as dicts
    scheduled_interviews: List[Dict[str, Any]]  # ScheduledInterview as dicts
    
    # Follow-up actions
    follow_up_emails: List[Dict[str, Any]]
    pending_actions: List[Dict[str, str]]
    
    # Metrics and tracking
    response_metrics: Dict[str, Any]
    processing_errors: List[str]
    
    # Configuration
    response_config: Dict[str, Any]
    
    # Status flags
    response_management_complete: bool
    
    # Optional LangGraph messages
    messages: Optional[Annotated[List, add_messages]]

class ResponseConfig(BaseModel):
    """Configuration for response management"""
    # LLM settings
    llm_model: str = Field(default="gpt-4")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for auto-processing")
    
    # Interview scheduling
    default_interview_duration: int = Field(default=60, description="Default interview duration in minutes")
    interview_buffer_hours: int = Field(default=24, description="Minimum hours before scheduling")
    max_interviews_per_day: int = Field(default=5)
    
    # Business hours
    business_start_hour: int = Field(default=9, description="Business start hour (24h format)")
    business_end_hour: int = Field(default=17, description="Business end hour (24h format)")
    business_days: List[int] = Field(default=[0, 1, 2, 3, 4], description="Business days (0=Monday)")
    timezone: str = Field(default="America/New_York")
    
    # Auto-response settings
    auto_respond_to_interested: bool = Field(default=True)
    auto_respond_to_questions: bool = Field(default=True)
    auto_respond_to_not_interested: bool = Field(default=False)
    
    # Escalation settings
    escalate_spam_complaints: bool = Field(default=True)
    escalate_low_confidence: bool = Field(default=True)
    escalate_complex_questions: bool = Field(default=True)
    
    # Follow-up timing
    follow_up_delay_hours: int = Field(default=2, description="Hours to wait before sending follow-up")
    max_follow_ups: int = Field(default=2, description="Maximum follow-ups per candidate")

class ResponseMetrics(BaseModel):
    """Metrics for response management performance"""
    campaign_id: str
    
    # Response statistics
    total_responses: int = 0
    responses_processed: int = 0
    
    # Response type breakdown
    interested_responses: int = 0
    not_interested_responses: int = 0
    questions_responses: int = 0
    other_responses: int = 0
    
    # Processing metrics
    auto_processed: int = 0
    human_review_needed: int = 0
    processing_errors: int = 0
    
    # Interview scheduling
    interviews_scheduled: int = 0
    interviews_confirmed: int = 0
    scheduling_conflicts: int = 0
    
    # Follow-up actions
    follow_ups_sent: int = 0
    auto_responses_sent: int = 0
    
    # Performance metrics
    avg_processing_time_seconds: float = 0.0
    avg_confidence_score: float = 0.0
    successful_automation_rate: float = 0.0
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)

class ResponseSummary(BaseModel):
    """Summary of response management results"""
    campaign_id: str
    job_title: str
    
    # Overall statistics
    total_responses_received: int
    responses_processed: int
    processing_success_rate: float
    
    # Response breakdown
    interested_candidates: int
    interview_scheduled_count: int
    questions_requiring_answers: int
    not_interested_count: int
    
    # Next actions required
    interviews_to_confirm: int
    questions_to_answer: int
    follow_ups_pending: int
    human_review_required: int
    
    # Performance metrics
    automation_rate: float
    avg_response_time_hours: float
    
    # Processing info
    processing_time_seconds: float
    error_count: int
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)