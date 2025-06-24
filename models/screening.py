from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from models.sourcing import CandidateProfile, JobRequirements

class ScreeningCriteria(BaseModel):
    """Criteria for candidate screening"""
    # Skill requirements
    required_skills_weight: float = Field(default=0.4, description="Weight for required skills match")
    preferred_skills_weight: float = Field(default=0.2, description="Weight for preferred skills match")
    
    # Experience requirements
    experience_weight: float = Field(default=0.3, description="Weight for experience level match")
    min_experience_years: int = Field(default=0, description="Minimum years of experience required")
    preferred_experience_years: int = Field(default=3, description="Preferred years of experience")
    
    # Location requirements
    location_weight: float = Field(default=0.1, description="Weight for location match")
    allow_remote: bool = Field(default=True, description="Allow remote candidates")
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred locations")
    
    # Education and other factors
    education_required: bool = Field(default=False, description="Is education mandatory")
    education_weight: float = Field(default=0.0, description="Weight for education match")
    
    # Scoring thresholds
    pass_threshold: float = Field(default=60.0, description="Minimum score to pass screening")
    shortlist_threshold: float = Field(default=75.0, description="Minimum score for shortlisting")

class SkillMatch(BaseModel):
    """Skill matching result"""
    skill_name: str
    found: bool
    match_type: str  # "exact", "partial", "related", "none"
    confidence: float = Field(ge=0.0, le=1.0)

class ScreeningResult(BaseModel):
    """Individual candidate screening result"""
    candidate_id: str
    candidate_name: str
    
    # Skill analysis
    required_skills_score: float = Field(ge=0.0, le=100.0)
    preferred_skills_score: float = Field(ge=0.0, le=100.0)
    skill_matches: List[SkillMatch] = Field(default_factory=list)
    missing_critical_skills: List[str] = Field(default_factory=list)
    
    # Experience analysis
    experience_score: float = Field(ge=0.0, le=100.0)
    experience_years: Optional[int] = None
    experience_level_match: str  # "under", "meets", "exceeds"
    
    # Location analysis
    location_score: float = Field(ge=0.0, le=100.0)
    location_match: bool
    candidate_location: Optional[str] = None
    
    # Education analysis
    education_score: float = Field(ge=0.0, le=100.0)
    education_match: bool
    
    # Overall scoring
    overall_score: float = Field(ge=0.0, le=100.0)
    weighted_score: float = Field(ge=0.0, le=100.0)
    
    # Decision
    passes_screening: bool
    recommended_for_shortlist: bool
    
    # Additional insights
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # Metadata
    screened_at: datetime = Field(default_factory=datetime.now)

class ScreeningState(TypedDict, total=False):
    """State for the screening stage"""
    # Input from sourcing stage
    raw_candidates: List[Dict[str, Any]]
    job_requirements: Dict[str, Any]  # Job requirements as dict
    
    # Screening configuration
    screening_criteria: Dict[str, Any]  # ScreeningCriteria as dict
    
    # Processing status
    current_candidate_index: int
    total_candidates: int
    screening_complete: bool
    
    # Results
    screening_results: List[Dict[str, Any]]  # ScreeningResult as dicts
    passed_candidates: List[Dict[str, Any]]
    shortlisted_candidates: List[Dict[str, Any]]
    
    # Metrics and analysis
    screening_metrics: Dict[str, Any]
    processing_errors: List[str]
    
    # Optional LangGraph messages
    messages: Optional[Annotated[List, add_messages]]

class ScreeningSummary(BaseModel):
    """Summary of screening results"""
    total_candidates: int
    passed_screening: int
    shortlisted: int
    rejected: int
    
    # Score distribution
    average_score: float
    highest_score: float
    lowest_score: float
    
    # Common patterns
    most_common_missing_skills: List[str]
    experience_distribution: Dict[str, int]
    location_distribution: Dict[str, int]
    
    # Processing metrics
    processing_time_seconds: float
    error_count: int
    
    # Generated at
    generated_at: datetime = Field(default_factory=datetime.now)