from typing import TypedDict, List, Dict, Any, Optional
from models.screening import CandidateProfile
from models.sourcing import SourceChannel, SourcingState

def create_candidate_from_raw_data(raw_data: Dict[str, Any], source: SourceChannel) -> CandidateProfile:
    """Create a CandidateProfile from raw source data with proper type conversion"""
    
    # Extract common fields with type conversion
    candidate_data = {
        "source": source,
        "source_id": str(raw_data.get("source_id", raw_data.get("id", "unknown"))),  # Convert to string
        "raw_data": raw_data
    }
    
    # Source-specific field mapping
    if source == SourceChannel.LINKEDIN:
        candidate_data.update({
            "name": raw_data.get("name"),
            "email": raw_data.get("contact_info", {}).get("email"),
            "linkedin_url": raw_data.get("profile_url"),
            "location": raw_data.get("location"),
            "current_title": raw_data.get("headline"),
            "current_company": raw_data.get("current_company"),
            "skills": raw_data.get("skills", [])
        })
    
    elif source == SourceChannel.INDEED:
        candidate_data.update({
            "current_title": raw_data.get("title"),
            "current_company": raw_data.get("company"),
            "location": raw_data.get("location"),
            "email": raw_data.get("contact_email")
        })
    
    elif source == SourceChannel.DATABASE:
        # Handle database-specific fields with proper type conversion
        candidate_data.update({
            "name": raw_data.get("name"),
            "email": raw_data.get("email"),
            "phone": raw_data.get("phone"),
            "location": raw_data.get("location"),
            "current_title": raw_data.get("current_title"),
            "current_company": raw_data.get("current_company"),
            "skills": raw_data.get("skills", []),
            "education": raw_data.get("education", []),
            "certifications": raw_data.get("certifications", []),
            "experience_years": raw_data.get("experience_years")
        })
    
    # Remove None values
    candidate_data = {k: v for k, v in candidate_data.items() if v is not None}
    
    # Ensure source_id is always a string
    if "source_id" in candidate_data:
        candidate_data["source_id"] = str(candidate_data["source_id"])
    
    return CandidateProfile(**candidate_data)

def validate_candidate_completeness(candidate: CandidateProfile) -> Dict[str, Any]:
    """Validate how complete a candidate profile is"""
    
    required_fields = ["name", "email"]
    important_fields = ["current_title", "location", "skills"]
    optional_fields = ["phone", "linkedin_url", "current_company"]
    
    completeness = {
        "required_missing": [field for field in required_fields if not getattr(candidate, field)],
        "important_missing": [field for field in important_fields if not getattr(candidate, field)],
        "optional_missing": [field for field in optional_fields if not getattr(candidate, field)],
    }
    
    # Calculate completeness score
    total_fields = len(required_fields) + len(important_fields) + len(optional_fields)
    missing_fields = len(completeness["required_missing"]) + len(completeness["important_missing"]) + len(completeness["optional_missing"])
    
    completeness["score"] = ((total_fields - missing_fields) / total_fields) * 100
    completeness["is_valid"] = len(completeness["required_missing"]) == 0
    
    return completeness

def deduplicate_candidates(candidates: List[CandidateProfile]) -> List[CandidateProfile]:
    """Remove duplicate candidates based on email and name"""
    
    seen = set()
    unique_candidates = []
    
    for candidate in candidates:
        # Create identifier based on email or name
        identifier = None
        if candidate.email:
            identifier = candidate.email.lower()
        elif candidate.name:
            identifier = candidate.name.lower().replace(" ", "")
        
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_candidates.append(candidate)
        elif not identifier:
            # If no email or name, keep the candidate but mark as potentially duplicate
            unique_candidates.append(candidate)
    
    return unique_candidates

def ensure_state_completeness(state: SourcingState) -> SourcingState:
    """Ensure state has all required fields with defaults"""
    # Create a copy to avoid mutating the original
    complete_state = state.copy()
    
    # Set defaults for missing fields
    if "raw_candidates" not in complete_state:
        complete_state["raw_candidates"] = []
    if "sourcing_metrics" not in complete_state:
        complete_state["sourcing_metrics"] = {}
    if "errors" not in complete_state:
        complete_state["errors"] = []
    if "channels_completed" not in complete_state:
        complete_state["channels_completed"] = []
    if "total_candidates_found" not in complete_state:
        complete_state["total_candidates_found"] = 0
    if "sourcing_complete" not in complete_state:
        complete_state["sourcing_complete"] = False
    if "current_channel" not in complete_state:
        complete_state["current_channel"] = ""
    
    # Initialize messages if not present (optional)
    if "messages" not in complete_state:
        complete_state["messages"] = []
    
    return complete_state

def safe_add_message(state: SourcingState, message: Dict[str, str]) -> SourcingState:
    """Safely add a message to state, handling missing messages field"""
    if "messages" in state and state["messages"] is not None:
        state["messages"].append(message)
    else:
        # If messages field doesn't exist, just print the message
        print(f"📝 {message.get('content', '')}")
    return state

def create_initial_sourcing_state(
    job_id: str,
    job_title: str,
    job_description: str,
    required_skills: List[str],
    location: str,
    experience_level: str,
    sourcing_channels: List[str],
    max_candidates_per_channel: int = 25,
    include_messages: bool = False
) -> SourcingState:
    """Create a properly formatted initial state"""
    
    base_state = SourcingState(
        job_id=job_id,
        job_title=job_title,
        job_description=job_description,
        required_skills=required_skills,
        location=location,
        experience_level=experience_level,
        sourcing_channels=sourcing_channels,
        max_candidates_per_channel=max_candidates_per_channel,
        raw_candidates=[],
        sourcing_metrics={},
        errors=[],
        current_channel="",
        channels_completed=[],
        total_candidates_found=0,
        sourcing_complete=False
    )
    
    # Add messages field if requested
    if include_messages:
        base_state["messages"] = []
    
    return base_state

def convert_database_candidate(candidate_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database candidate to screening format with proper type handling"""
    
    # Convert IDs to strings to avoid Pydantic validation errors
    converted = candidate_dict.copy()
    
    # Ensure IDs are strings
    if 'id' in converted:
        converted['id'] = str(converted['id'])
    if 'source_id' in converted:
        converted['source_id'] = str(converted['source_id'])
    
    # Ensure lists are properly formatted
    for field in ['skills', 'education', 'certifications']:
        if field in converted and converted[field] is None:
            converted[field] = []
        elif field in converted and isinstance(converted[field], str):
            try:
                import json
                converted[field] = json.loads(converted[field])
            except:
                converted[field] = []
    
    # Ensure raw_data is a dict
    if 'raw_data' in converted and converted['raw_data'] is None:
        converted['raw_data'] = {}
    elif 'raw_data' in converted and isinstance(converted['raw_data'], str):
        try:
            import json
            converted['raw_data'] = json.loads(converted['raw_data'])
        except:
            converted['raw_data'] = {}
    
    # Ensure experience_years is an integer
    if 'experience_years' in converted and converted['experience_years'] is not None:
        try:
            converted['experience_years'] = int(converted['experience_years'])
        except (ValueError, TypeError):
            converted['experience_years'] = 0
    
    return converted