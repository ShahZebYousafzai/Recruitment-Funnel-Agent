import sqlite3
import json
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.tools import StructuredTool
import logging
from datetime import datetime
import os

class CandidateDatabase:
    """Database connection manager for candidate retrieval"""
    
    def __init__(self, db_path: str = "candidates.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            logging.warning(f"Database file {db_path} not found. Please run database setup first.")
    
    def search_candidates(self, skills: List[str] = None, location: str = None, 
                         experience_level: str = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search candidates based on criteria"""
        if not os.path.exists(self.db_path):
            logging.error(f"Database file {self.db_path} not found")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic query
            where_clauses = ["status = 'available'"]
            params = []
            
            if skills:
                # Search for any of the required skills
                skill_conditions = []
                for skill in skills:
                    skill_conditions.append("skills LIKE ?")
                    params.append(f"%{skill}%")
                where_clauses.append(f"({' OR '.join(skill_conditions)})")
            
            if location:
                where_clauses.append("location LIKE ?")
                params.append(f"%{location}%")
            
            if experience_level:
                exp_range = self._get_experience_range(experience_level)
                if exp_range:
                    where_clauses.append("experience_years BETWEEN ? AND ?")
                    params.extend(exp_range)
            
            query = f"""
                SELECT * FROM candidates 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY experience_years DESC, created_at DESC
                LIMIT ?
            """
            params.append(max_results)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            columns = [desc[0] for desc in cursor.description]
            candidates = []
            
            for row in rows:
                candidate = dict(zip(columns, row))
                # Parse JSON fields
                candidate['skills'] = json.loads(candidate['skills']) if candidate['skills'] else []
                candidate['education'] = json.loads(candidate['education']) if candidate['education'] else []
                candidate['certifications'] = json.loads(candidate['certifications']) if candidate['certifications'] else []
                candidate['raw_data'] = json.loads(candidate['raw_data']) if candidate['raw_data'] else {}
                
                # Format for sourcing tool output
                formatted_candidate = {
                    "id": candidate['source_id'],
                    "name": candidate['name'],
                    "email": candidate['email'],
                    "phone": candidate['phone'],
                    "location": candidate['location'],
                    "skills": candidate['skills'],
                    "experience_years": candidate['experience_years'],
                    "current_title": candidate['current_title'],
                    "current_company": candidate['current_company'],
                    "linkedin_url": candidate['linkedin_url'],
                    "resume_url": candidate['resume_url'],
                    "education": candidate['education'],
                    "certifications": candidate['certifications'],
                    "last_updated": candidate['updated_at'],
                    "status": candidate['status'],
                    # Additional metadata
                    "source": "database",
                    "raw_data": candidate['raw_data']
                }
                candidates.append(formatted_candidate)
            
            conn.close()
            return candidates
            
        except Exception as e:
            logging.error(f"Database search error: {e}")
            return []
    
    def _get_experience_range(self, experience_level: str) -> tuple:
        """Convert experience level to years range"""
        level_map = {
            "entry": (0, 2),
            "junior": (1, 3),
            "mid": (3, 7),
            "senior": (5, 12),
            "lead": (7, 15),
            "principal": (10, 20),
            "staff": (8, 20)
        }
        return level_map.get(experience_level.lower(), None)

def create_database_tool() -> StructuredTool:
    """Create database sourcing tool with real database connection"""
    from pydantic import BaseModel, Field
    
    class DatabaseInput(BaseModel):
        skills: List[str] = Field(description="Required skills")
        location: str = Field(description="Location to search in")
        experience_level: str = Field(description="Experience level required")
        max_results: int = Field(default=50, description="Maximum number of results")
    
    def database_search(skills: List[str], location: str, experience_level: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search internal database for candidates"""
        try:
            db = CandidateDatabase()
            candidates = db.search_candidates(
                skills=skills,
                location=location,
                experience_level=experience_level,
                max_results=max_results
            )
            
            logging.info(f"Database search found {len(candidates)} candidates for skills: {skills}, location: {location}")
            return candidates
            
        except Exception as e:
            logging.error(f"Database sourcing error: {e}")
            return []
    
    return StructuredTool.from_function(
        func=database_search,
        name="database_sourcer",
        description="Search internal candidate database for qualified candidates",
        args_schema=DatabaseInput
    )

# For testing the tool directly
def test_database_tool():
    """Test the database tool functionality"""
    print("🧪 Testing Database Sourcing Tool...")
    
    # Create the tool
    tool = create_database_tool()
    
    # Test searches
    test_cases = [
        {
            "name": "Python + ML Engineers",
            "params": {
                "skills": ["Python", "Machine Learning"],
                "location": "San Francisco",
                "experience_level": "senior",
                "max_results": 3
            }
        },
        {
            "name": "AI Engineers",
            "params": {
                "skills": ["AI", "PyTorch", "NLP"],
                "location": "",
                "experience_level": "mid",
                "max_results": 5
            }
        },
        {
            "name": "Remote JavaScript Developers",
            "params": {
                "skills": ["JavaScript", "React"],
                "location": "Remote",
                "experience_level": "junior",
                "max_results": 2
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        try:
            results = tool.invoke(test_case['params'])
            print(f"   Found {len(results)} candidates")
            
            for i, candidate in enumerate(results[:2]):  # Show first 2
                print(f"   {i+1}. {candidate['name']} - {candidate['current_title']} ({candidate['experience_years']} years)")
                print(f"      Skills: {', '.join(candidate['skills'][:3])}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_database_tool()