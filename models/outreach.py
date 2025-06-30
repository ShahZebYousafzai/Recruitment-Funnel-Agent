from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class EmailStatus(str, Enum):
    """Email delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

class OutreachTemplate(BaseModel):
    """Email template for candidate outreach"""
    template_id: str = Field(description="Unique template identifier")
    name: str = Field(description="Template name")
    subject_template: str = Field(description="Email subject template with placeholders")
    body_template: str = Field(description="Email body template with placeholders")
    template_type: str = Field(default="initial_outreach", description="Type of template")
    
    # Personalization fields
    required_fields: List[str] = Field(default_factory=list, description="Required candidate fields")
    optional_fields: List[str] = Field(default_factory=list, description="Optional candidate fields")
    
    # Template metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="system")
    active: bool = Field(default=True)

class CandidateEmail(BaseModel):
    """Individual email sent to a candidate"""
    email_id: str = Field(description="Unique email identifier")
    candidate_id: str = Field(description="Candidate identifier")
    candidate_name: str = Field(description="Candidate name")
    candidate_email: str = Field(description="Candidate email address")
    
    # Email content
    subject: str = Field(description="Actual email subject")
    body: str = Field(description="Actual email body")
    template_id: str = Field(description="Template used")
    
    # Job information
    job_id: str = Field(description="Job posting ID")
    job_title: str = Field(description="Job title")
    
    # Status tracking
    status: EmailStatus = Field(default=EmailStatus.PENDING)
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    opened_at: Optional[datetime] = Field(default=None)
    replied_at: Optional[datetime] = Field(default=None)
    
    # Response tracking
    response_received: bool = Field(default=False)
    response_type: Optional[str] = Field(default=None)  # "interested", "not_interested", "questions"
    response_content: Optional[str] = Field(default=None)
    
    # Follow-up tracking
    follow_up_scheduled: bool = Field(default=False)
    follow_up_date: Optional[datetime] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = Field(default=None)

class OutreachCampaign(BaseModel):
    """Outreach campaign for a specific job"""
    campaign_id: str = Field(description="Unique campaign identifier")
    job_id: str = Field(description="Associated job ID")
    job_title: str = Field(description="Job title")
    
    # Campaign configuration
    template_id: str = Field(description="Email template to use")
    target_candidates: List[str] = Field(description="List of candidate IDs to contact")
    
    # Scheduling
    scheduled_send_time: Optional[datetime] = Field(default=None)
    stagger_minutes: int = Field(default=5, description="Minutes between emails to avoid spam")
    
    # Status
    campaign_status: str = Field(default="draft")  # draft, scheduled, active, paused, completed
    emails_sent: int = Field(default=0)
    emails_delivered: int = Field(default=0)
    emails_opened: int = Field(default=0)
    emails_replied: int = Field(default=0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_by: str = Field(default="system")

class OutreachMetrics(BaseModel):
    """Metrics for outreach performance"""
    campaign_id: str
    total_emails: int = 0
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    emails_failed: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    
    # Response analysis
    positive_responses: int = 0
    negative_responses: int = 0
    questions_responses: int = 0
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)

class OutreachState(TypedDict, total=False):
    """State for the outreach stage"""
    # Input from screening stage
    shortlisted_candidates: List[Dict[str, Any]]
    job_requirements: Dict[str, Any]
    
    # Outreach configuration
    outreach_config: Dict[str, Any]
    email_template_id: str
    
    # Campaign management
    campaign_id: str
    campaign_status: str
    
    # Email processing
    emails_to_send: List[Dict[str, Any]]  # CandidateEmail as dicts
    sent_emails: List[Dict[str, Any]]
    current_email_index: int
    total_emails: int
    
    # Results and tracking
    outreach_metrics: Dict[str, Any]
    email_statuses: Dict[str, str]  # email_id -> status
    processing_errors: List[str]
    
    # Status
    outreach_complete: bool
    
    # Optional LangGraph messages
    messages: Optional[Annotated[List, add_messages]]

class EmailProvider(BaseModel):
    """Email service provider configuration"""
    provider_name: str = Field(description="Name of email provider")
    api_endpoint: str = Field(description="API endpoint URL")
    api_key: str = Field(description="API key")
    sender_email: str = Field(description="Sender email address")
    sender_name: str = Field(description="Sender display name")
    
    # Provider-specific settings
    rate_limit: int = Field(default=100, description="Emails per hour limit")
    batch_size: int = Field(default=10, description="Emails per batch")
    retry_attempts: int = Field(default=3, description="Retry attempts for failed emails")
    
    # Tracking settings
    track_opens: bool = Field(default=True)
    track_clicks: bool = Field(default=True)
    track_delivery: bool = Field(default=True)

class OutreachSummary(BaseModel):
    """Summary of outreach campaign results"""
    campaign_id: str
    job_title: str
    
    # Basic metrics
    total_candidates: int
    emails_sent: int
    successful_deliveries: int
    failed_deliveries: int
    
    # Engagement metrics
    emails_opened: int
    emails_replied: int
    response_rate: float
    
    # Response breakdown
    interested_candidates: int
    not_interested_candidates: int
    questions_candidates: int
    no_response_candidates: int
    
    # Next steps
    candidates_for_interview: int
    follow_ups_needed: int
    
    # Processing info
    processing_time_seconds: float
    error_count: int
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)