from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class CandidateStatus(str, Enum):
    """Candidate status throughout the recruitment pipeline"""
    SOURCED = "sourced"
    PARSED = "parsed"
    SCREENED = "screened"
    SHORTLISTED = "shortlisted"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    INTERVIEWED = "interviewed"
    HIRED = "hired"
    REJECTED = "rejected"

class SourceChannel(str, Enum):
    """Available sourcing channels"""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    DATABASE = "database"
    GITHUB = "github"
    REFERRAL = "referral"
    DIRECT_APPLY = "direct_apply"

class CandidateProfile(BaseModel):
    """Individual candidate profile structure"""
    # Required fields
    source: SourceChannel = Field(description="Source channel where candidate was found")
    source_id: str = Field(description="Unique identifier from the source system")
    
    # Personal information
    name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Primary email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    
    # Professional information
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    resume_url: Optional[str] = Field(default=None, description="Resume/CV file URL")
    location: Optional[str] = Field(default=None, description="Current location")
    current_title: Optional[str] = Field(default=None, description="Current job title")
    current_company: Optional[str] = Field(default=None, description="Current employer")
    experience_years: Optional[int] = Field(default=None, description="Years of experience")
    
    # Skills and qualifications
    skills: List[str] = Field(default_factory=list, description="List of skills")
    education: List[str] = Field(default_factory=list, description="Education background")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")
    
    # Metadata
    status: CandidateStatus = Field(default=CandidateStatus.SOURCED, description="Current status in pipeline")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Original data from source")
    sourced_at: datetime = Field(default_factory=datetime.now, description="Timestamp when sourced")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    # Scoring and ranking (will be populated in later stages)
    eligibility_score: Optional[float] = Field(default=None, description="Eligibility score (0-100)")
    ranking_score: Optional[float] = Field(default=None, description="Overall ranking score")
    notes: Optional[str] = Field(default=None, description="Additional notes or comments")

    class Config:
        # Allow arbitrary types for datetime
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def update_status(self, new_status: CandidateStatus, notes: Optional[str] = None):
        """Update candidate status with timestamp"""
        self.status = new_status
        self.last_updated = datetime.now()
        if notes:
            self.notes = notes

class JobRequirements(BaseModel):
    """Job requirements and criteria"""
    job_id: str = Field(description="Unique job identifier")
    job_title: str = Field(description="Job title")
    job_description: str = Field(description="Detailed job description")
    
    # Requirements
    required_skills: List[str] = Field(description="Mandatory skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    education_requirements: List[str] = Field(default_factory=list, description="Education requirements")
    experience_requirements: str = Field(description="Experience level required")
    
    # Location and logistics
    location: str = Field(description="Job location")
    remote_ok: bool = Field(default=False, description="Remote work allowed")
    travel_required: Optional[str] = Field(default=None, description="Travel requirements")
    
    # Compensation (optional)
    salary_range_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_range_max: Optional[int] = Field(default=None, description="Maximum salary")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    urgency: str = Field(default="normal", description="Hiring urgency: low, normal, high, urgent")

class SourcingState(TypedDict, total=False):
    """State for the sourcing stage - Messages are optional"""
    # Required job information
    job_id: str
    job_title: str
    job_description: str
    required_skills: List[str]
    location: str
    experience_level: str
    
    # Required sourcing configuration
    sourcing_channels: List[str]
    max_candidates_per_channel: int
    
    # Required results
    raw_candidates: List[Dict[str, Any]]
    sourcing_metrics: Dict[str, Any]
    errors: List[str]
    
    # Required processing status
    current_channel: str
    channels_completed: List[str]
    total_candidates_found: int
    sourcing_complete: bool
    
    # Optional LangGraph messages
    messages: Optional[Annotated[List, add_messages]]

class ParsingState(TypedDict):
    """State for the parsing stage (Stage 2)"""
    # Input from sourcing
    raw_candidates: List[CandidateProfile]
    
    # Parsing configuration
    parsing_settings: Dict[str, Any]
    
    # Results
    parsed_candidates: List[CandidateProfile]
    parsing_metrics: Dict[str, Any]
    parsing_errors: List[str]
    
    # Processing status
    parsing_complete: bool

class ScreeningState(TypedDict):
    """State for the screening stage (Stage 3)"""
    # Input from parsing
    parsed_candidates: List[CandidateProfile]
    job_requirements: JobRequirements
    
    # Screening configuration
    screening_criteria: Dict[str, Any]
    pass_threshold: float
    
    # Results
    screened_candidates: List[CandidateProfile]
    eligible_candidates: List[CandidateProfile]
    screening_metrics: Dict[str, Any]
    
    # Processing status
    screening_complete: bool

class RecruitmentPipelineState(TypedDict):
    """Complete recruitment pipeline state"""
    # Job information
    job_requirements: JobRequirements
    
    # Stage-specific states
    sourcing_state: SourcingState
    parsing_state: ParsingState
    screening_state: ScreeningState
    
    # Overall pipeline status
    current_stage: str
    pipeline_complete: bool
    
    # Global metrics and tracking
    pipeline_metrics: Dict[str, Any]
    total_errors: List[str]
    
    # Configuration
    pipeline_config: Dict[str, Any]
