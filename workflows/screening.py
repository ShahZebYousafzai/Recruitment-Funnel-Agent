from langgraph.graph import StateGraph, START, END
from models.screening import ScreeningState, ScreeningCriteria
from nodes.screening import finalize_screening, check_screening_completion
from database.database_integration import CandidateDatabase
from agents.screening import ScreeningAgent
from models.screening import ScreeningResult
from utils import safe_add_message
import time
import logging

def initialize_database_screening(state: ScreeningState) -> ScreeningState:
    """Initialize screening process with database integration"""
    
    print("🔍 Initializing Database-Driven Candidate Screening...")
    
    # Ensure all required fields exist
    if "screening_results" not in state:
        state["screening_results"] = []
    if "passed_candidates" not in state:
        state["passed_candidates"] = []
    if "shortlisted_candidates" not in state:
        state["shortlisted_candidates"] = []
    if "screening_metrics" not in state:
        state["screening_metrics"] = {}
    if "processing_errors" not in state:
        state["processing_errors"] = []
    if "messages" not in state:
        state["messages"] = []
    
    # Initialize database connection
    try:
        db = CandidateDatabase()
        
        # Get database statistics
        stats = db.get_database_stats()
        print(f"📊 Database contains {stats.get('available_candidates', 0)} available candidates")
        
        # Retrieve candidates based on job requirements
        job_requirements = state["job_requirements"]
        max_candidates = state.get("max_candidates", 50)
        
        print(f"🎯 Job Requirements:")
        print(f"   Title: {job_requirements.get('job_title', 'N/A')}")
        print(f"   Required Skills: {', '.join(job_requirements.get('required_skills', []))}")
        print(f"   Location: {job_requirements.get('location', 'N/A')}")
        print(f"   Experience Level: {job_requirements.get('experience_level', 'N/A')}")
        
        # Get candidates from database
        candidates = db.get_candidates_for_job(job_requirements, max_candidates)
        
        if not candidates:
            print("⚠️ No candidates found matching job requirements")
            print("🔄 Trying to get all available candidates...")
            candidates = db.get_all_candidates(max_candidates=20)
        
        # Update state with database candidates
        state["raw_candidates"] = candidates
        state["current_candidate_index"] = 0
        state["total_candidates"] = len(candidates)
        state["screening_complete"] = False
        
        # Set default screening criteria if not provided
        if "screening_criteria" not in state:
            default_criteria = ScreeningCriteria()
            state["screening_criteria"] = default_criteria.model_dump()
        
        # Add initialization message
        init_message = {
            "type": "system",
            "content": f"🔍 Starting database screening of {state['total_candidates']} candidates"
        }
        state = safe_add_message(state, init_message)
        
        print(f"✅ Successfully loaded {state['total_candidates']} candidates from database")
        
        if state["total_candidates"] == 0:
            print("⚠️ No candidates found to screen")
            state["screening_complete"] = True
        
        return state
        
    except Exception as e:
        error_msg = f"Database initialization failed: {str(e)}"
        print(f"❌ {error_msg}")
        logging.error(f"Database screening initialization error: {e}", exc_info=True)
        
        state["processing_errors"] = [error_msg]
        state["raw_candidates"] = []
        state["total_candidates"] = 0
        state["screening_complete"] = True
        
        return state

def screen_database_candidates(state: ScreeningState) -> ScreeningState:
    """Screen candidates retrieved from database"""
    
    print(f"🔍 Starting database candidate screening...")
    
    # Initialize screening agent
    agent = ScreeningAgent()
    
    # Parse screening criteria
    criteria_dict = state["screening_criteria"]
    criteria = ScreeningCriteria(**criteria_dict)
    
    # Parse job requirements
    job_requirements = state["job_requirements"]
    
    # Track processing time
    start_time = time.time()
    
    # Process all candidates
    screening_results = []
    passed_candidates = []
    shortlisted_candidates = []
    processing_errors = []
    
    total_candidates = len(state["raw_candidates"])
    
    print(f"📋 Screening criteria:")
    print(f"   Pass threshold: {criteria.pass_threshold}%")
    print(f"   Shortlist threshold: {criteria.shortlist_threshold}%")
    print(f"   Min experience: {criteria.min_experience_years} years")
    print(f"   Allow remote: {criteria.allow_remote}")
    
    for i, candidate_data in enumerate(state["raw_candidates"]):
        try:
            candidate_name = candidate_data.get('name', 'Unknown')
            candidate_title = candidate_data.get('current_title', 'N/A')
            candidate_exp = candidate_data.get('experience_years', 0)
            
            print(f"  📝 [{i+1}/{total_candidates}] {candidate_name}")
            print(f"      Title: {candidate_title}")
            print(f"      Experience: {candidate_exp} years")
            print(f"      Skills: {', '.join(candidate_data.get('skills', [])[:3])}...")
            
            # Screen the candidate
            result = agent.screen_candidate(candidate_data, job_requirements, criteria)
            
            # Convert result to dict for state storage
            result_dict = result.model_dump()
            screening_results.append(result_dict)
            
            # Show result
            print(f"      📊 Score: {result.weighted_score:.1f} | {'✅ PASS' if result.passes_screening else '❌ FAIL'}")
            if result.recommended_for_shortlist:
                print(f"      🌟 SHORTLISTED")
            
            # Categorize candidates
            if result.passes_screening:
                passed_candidates.append(candidate_data)
                
                if result.recommended_for_shortlist:
                    shortlisted_candidates.append(candidate_data)
            
            # Update candidate status in database if needed
            try:
                db = CandidateDatabase()
                status = "shortlisted" if result.recommended_for_shortlist else \
                        "screened_pass" if result.passes_screening else \
                        "screened_fail"
                
                notes = f"Score: {result.weighted_score:.1f}, Strengths: {', '.join(result.strengths[:2])}"
                db.update_candidate_status(candidate_data['source_id'], status, notes)
            except Exception as db_error:
                print(f"      ⚠️ Failed to update database status: {db_error}")
            
            # Update progress
            state["current_candidate_index"] = i + 1
            
            print()  # Add spacing between candidates
            
        except Exception as e:
            error_msg = f"Error screening candidate {i+1} ({candidate_data.get('name', 'Unknown')}): {str(e)}"
            processing_errors.append(error_msg)
            logging.error(f"Screening error: {e}", exc_info=True)
            print(f"    ❌ {error_msg}")
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Generate summary
    summary = agent.generate_screening_summary(
        [ScreeningResult(**result) for result in screening_results],
        processing_time
    )
    
    # Update state with results
    state["screening_results"] = screening_results
    state["passed_candidates"] = passed_candidates
    state["shortlisted_candidates"] = shortlisted_candidates
    state["processing_errors"] = processing_errors
    state["screening_complete"] = True
    
    # Update metrics
    state["screening_metrics"] = {
        "total_processed": total_candidates,
        "processing_time_seconds": processing_time,
        "passed_count": len(passed_candidates),
        "shortlisted_count": len(shortlisted_candidates),
        "rejected_count": total_candidates - len(passed_candidates),
        "error_count": len(processing_errors),
        "average_score": summary.average_score,
        "summary": summary.model_dump()
    }
    
    # Add completion message
    completion_message = {
        "type": "system",
        "content": f"✅ Database screening complete: {len(passed_candidates)}/{total_candidates} candidates passed"
    }
    state = safe_add_message(state, completion_message)
    
    print(f"{'='*60}")
    print(f"📊 SCREENING SUMMARY")
    print(f"{'='*60}")
    print(f"📈 Results:")
    print(f"   Total Processed: {total_candidates}")
    print(f"   ✅ Passed: {len(passed_candidates)} ({len(passed_candidates)/total_candidates*100:.1f}%)")
    print(f"   🌟 Shortlisted: {len(shortlisted_candidates)} ({len(shortlisted_candidates)/total_candidates*100:.1f}%)")
    print(f"   ❌ Rejected: {total_candidates - len(passed_candidates)} ({(total_candidates-len(passed_candidates))/total_candidates*100:.1f}%)")
    print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
    print(f"   📊 Average score: {summary.average_score:.1f}/100")
    
    return state

def create_database_screening_workflow() -> StateGraph:
    """Create screening workflow that integrates with candidate database"""
    
    # Create workflow with ScreeningState
    workflow = StateGraph(ScreeningState)
    
    # Add nodes
    workflow.add_node("initialize_db_screening", initialize_database_screening)
    workflow.add_node("screen_db_candidates", screen_database_candidates)
    workflow.add_node("finalize_screening", finalize_screening)
    
    # Add edges
    workflow.add_edge(START, "initialize_db_screening")
    workflow.add_edge("initialize_db_screening", "screen_db_candidates")
    
    # Conditional edge for completion check
    workflow.add_conditional_edges(
        "screen_db_candidates",
        check_screening_completion,
        {
            "continue_screening": "screen_db_candidates",  # If batch processing needed
            "screening_complete": "finalize_screening"
        }
    )
    
    workflow.add_edge("finalize_screening", END)
    
    return workflow.compile()

def create_database_screening_state(
    job_requirements: dict,
    screening_criteria: dict = None,
    max_candidates: int = 50
) -> ScreeningState:
    """Create initial state for database-driven screening workflow"""
    
    # Default screening criteria if not provided
    if screening_criteria is None:
        default_criteria = ScreeningCriteria()
        screening_criteria = default_criteria.model_dump()
    
    return ScreeningState(
        raw_candidates=[],  # Will be populated from database
        job_requirements=job_requirements,
        screening_criteria=screening_criteria,
        max_candidates=max_candidates,
        current_candidate_index=0,
        total_candidates=0,
        screening_complete=False,
        screening_results=[],
        passed_candidates=[],
        shortlisted_candidates=[],
        screening_metrics={},
        processing_errors=[],
        messages=[]
    )