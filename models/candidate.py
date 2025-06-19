# models/candidate.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class CandidateStatus(str, Enum):
    PENDING = "pending"
    SCREENED = "screened"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"

class Candidate(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    resume_text: str
    skills: List[str] = Field(default_factory=list)
    experience_years: float = 0.0
    education: List[str] = Field(default_factory=list)
    previous_roles: List[str] = Field(default_factory=list)
    status: CandidateStatus = CandidateStatus.PENDING
    screening_score: Optional[float] = None
    screening_feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ResumeAnalysis(BaseModel):
    candidate_id: str
    extracted_skills: List[str]
    experience_years: float
    education_level: str
    previous_companies: List[str]
    key_achievements: List[str]
    contact_info: Dict[str, str]
    summary: str