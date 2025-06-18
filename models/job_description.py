from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class JobDescription(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience: float = 0.0
    education_requirements: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: str = "full-time"
    keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)