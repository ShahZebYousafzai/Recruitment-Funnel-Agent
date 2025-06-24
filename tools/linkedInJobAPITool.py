from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.tools import StructuredTool
import logging

def create_linkedin_tool() -> StructuredTool:
    """Create LinkedIn sourcing tool"""
    from pydantic import BaseModel, Field
    
    class LinkedInInput(BaseModel):
        job_title: str = Field(description="Job title to search for")
        location: str = Field(description="Location to search in")
        skills: List[str] = Field(description="Required skills")
        max_results: int = Field(default=50, description="Maximum number of results")
    
    def linkedin_search(job_title: str, location: str, skills: List[str], max_results: int = 50) -> List[Dict[str, Any]]:
        """Search LinkedIn for candidates"""
        try:
            search_params = {
                "keywords": f"{job_title} {' '.join(skills)}",
                "location": location,
                "count": max_results
            }
            
            # Simulated LinkedIn API response
            return [
                {
                    "id": f"linkedin_{i}",
                    "name": f"LinkedIn Candidate {i}",
                    "headline": f"Senior {job_title}",
                    "location": location,
                    "profile_url": f"https://linkedin.com/in/candidate{i}",
                    "current_company": f"Tech Company {i}",
                    "experience": f"{3 + i} years",
                    "skills": skills[:3] + ["Communication", "Leadership"],
                    "contact_info": {
                        "email": f"candidate{i}@email.com"
                    }
                }
                for i in range(min(10, max_results))
            ]
        except Exception as e:
            logging.error(f"LinkedIn sourcing error: {e}")
            return []
    
    return StructuredTool.from_function(
        func=linkedin_search,
        name="linkedin_sourcer",
        description="Search for candidates on LinkedIn based on job criteria",
        args_schema=LinkedInInput
    )