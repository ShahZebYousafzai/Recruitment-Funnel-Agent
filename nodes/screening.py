import time
from datetime import datetime
from typing import Dict, List, Any
from models.screening import ScreeningState, ScreeningCriteria, ScreeningSummary
from agents.screening import ScreeningAgent
from models.screening import ScreeningResult
from utils import safe_add_message
import logging

def initialize_screening(state: ScreeningState) -> ScreeningState:
    """Initialize the screening process"""
    
    print("🔍 Initializing Candidate Screening...")
    
    # Ensure all required fields exist
    if "raw_candidates" not in state:
        state["raw_candidates"] = []
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
    
    # Set up processing status
    state["current_candidate_index"] = 0
    state["total_candidates"] = len(state["raw_candidates"])
    state["screening_complete"] = False
    
    # Set default screening criteria if not provided
    if "screening_criteria" not in state:
        default_criteria = ScreeningCriteria()
        state["screening_criteria"] = default_criteria.model_dump()
    
    # Add initialization message
    init_message = {
        "type": "system",
        "content": f"🔍 Starting screening of {state['total_candidates']} candidates"
    }
    state = safe_add_message(state, init_message)
    
    print(f"📊 Total candidates to screen: {state['total_candidates']}")
    
    if state["total_candidates"] == 0:
        print("⚠️ No candidates found to screen")
        state["screening_complete"] = True
    
    return state

def screen_candidates_batch(state: ScreeningState) -> ScreeningState:
    """Screen all candidates in the current batch"""
    
    print(f"🔍 Starting batch screening of candidates...")
    
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
    
    for i, candidate_data in enumerate(state["raw_candidates"]):
        try:
            print(f"  📝 Screening candidate {i+1}/{total_candidates}: {candidate_data.get('name', 'Unknown')}")
            
            # Screen the candidate
            result = agent.screen_candidate(candidate_data, job_requirements, criteria)
            
            # Convert result to dict for state storage
            result_dict = result.model_dump()
            screening_results.append(result_dict)
            
            # Categorize candidates
            if result.passes_screening:
                passed_candidates.append(candidate_data)
                
                if result.recommended_for_shortlist:
                    shortlisted_candidates.append(candidate_data)
            
            # Update progress
            state["current_candidate_index"] = i + 1
            
        except Exception as e:
            error_msg = f"Error screening candidate {i+1}: {str(e)}"
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
        "content": f"✅ Screening complete: {len(passed_candidates)}/{total_candidates} candidates passed"
    }
    state = safe_add_message(state, completion_message)
    
    print(f"✅ Batch screening completed!")
    print(f"   📊 Processed: {total_candidates} candidates")
    print(f"   ✅ Passed: {len(passed_candidates)}")
    print(f"   🌟 Shortlisted: {len(shortlisted_candidates)}")
    print(f"   ❌ Rejected: {total_candidates - len(passed_candidates)}")
    print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
    
    return state

def check_screening_completion(state: ScreeningState) -> str:
    """Check if screening is complete"""
    if state.get("screening_complete", False):
        return "screening_complete"
    else:
        return "continue_screening"

def finalize_screening(state: ScreeningState) -> ScreeningState:
    """Finalize screening and generate detailed report"""
    
    print("\n📊 Finalizing Screening Results...")
    
    metrics = state["screening_metrics"]
    
    # Display detailed results
    print(f"\n{'='*60}")
    print(f"📋 SCREENING STAGE COMPLETE")
    print(f"{'='*60}")
    
    print(f"📊 Summary Statistics:")
    print(f"   Total Candidates: {metrics['total_processed']}")
    print(f"   Passed Screening: {metrics['passed_count']} ({metrics['passed_count']/metrics['total_processed']*100:.1f}%)")
    print(f"   Recommended for Shortlist: {metrics['shortlisted_count']} ({metrics['shortlisted_count']/metrics['total_processed']*100:.1f}%)")
    print(f"   Rejected: {metrics['rejected_count']} ({metrics['rejected_count']/metrics['total_processed']*100:.1f}%)")
    print(f"   Average Score: {metrics['average_score']:.1f}/100")
    print(f"   Processing Time: {metrics['processing_time_seconds']:.2f} seconds")
    
    # Show top candidates
    if state["shortlisted_candidates"]:
        print(f"\n🌟 Top Shortlisted Candidates:")
        
        # Sort by score
        results_with_scores = []
        for i, result_dict in enumerate(state["screening_results"]):
            if result_dict["recommended_for_shortlist"]:
                candidate = None
                for candidate_data in state["raw_candidates"]:
                    if candidate_data.get("source_id") == result_dict["candidate_id"] or \
                       candidate_data.get("id") == result_dict["candidate_id"]:
                        candidate = candidate_data
                        break
                
                if candidate:
                    results_with_scores.append((result_dict, candidate))
        
        # Sort by weighted score
        results_with_scores.sort(key=lambda x: x[0]["weighted_score"], reverse=True)
        
        for i, (result, candidate) in enumerate(results_with_scores[:5]):
            name = candidate.get('name', 'Unknown')
            title = candidate.get('current_title', 'N/A')
            score = result['weighted_score']
            print(f"   {i+1}. {name} - {title} - Score: {score:.1f}")
    
    # Show common issues
    summary = metrics.get('summary', {})
    if summary.get('most_common_missing_skills'):
        print(f"\n⚠️ Most Common Missing Skills:")
        for skill in summary['most_common_missing_skills'][:5]:
            print(f"   • {skill}")
    
    # Show experience distribution
    if summary.get('experience_distribution'):
        print(f"\n📈 Experience Level Distribution:")
        for level, count in summary['experience_distribution'].items():
            print(f"   • {level}: {count} candidates")
    
    # Show any errors
    if state["processing_errors"]:
        print(f"\n❌ Processing Errors ({len(state['processing_errors'])}):")
        for error in state["processing_errors"][:3]:
            print(f"   • {error}")
    
    # Add final summary message
    final_message = {
        "type": "system",
        "content": f"📊 Screening finalized: {metrics['shortlisted_count']} candidates ready for next stage"
    }
    state = safe_add_message(state, final_message)
    
    print(f"\n🎉 Screening stage completed successfully!")
    print(f"📋 {metrics['shortlisted_count']} candidates ready for next stage")
    
    return state

def generate_screening_report(state: ScreeningState) -> Dict[str, Any]:
    """Generate a detailed screening report"""
    
    metrics = state["screening_metrics"]
    summary = metrics.get('summary', {})
    
    # Detailed candidate analysis
    candidate_details = []
    for result_dict in state["screening_results"]:
        # Find corresponding candidate data
        candidate = None
        for candidate_data in state["raw_candidates"]:
            if candidate_data.get("source_id") == result_dict["candidate_id"] or \
               candidate_data.get("id") == result_dict["candidate_id"]:
                candidate = candidate_data
                break
        
        if candidate:
            candidate_details.append({
                "candidate": candidate,
                "screening_result": result_dict,
                "decision": "Shortlisted" if result_dict["recommended_for_shortlist"] else 
                           "Passed" if result_dict["passes_screening"] else "Rejected"
            })
    
    # Sort by score
    candidate_details.sort(key=lambda x: x["screening_result"]["weighted_score"], reverse=True)
    
    report = {
        "stage": "Initial Screening",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_candidates": metrics["total_processed"],
            "passed_screening": metrics["passed_count"],
            "shortlisted": metrics["shortlisted_count"],
            "rejected": metrics["rejected_count"],
            "pass_rate": f"{metrics['passed_count']/metrics['total_processed']*100:.1f}%",
            "shortlist_rate": f"{metrics['shortlisted_count']/metrics['total_processed']*100:.1f}%",
            "average_score": f"{metrics['average_score']:.1f}",
            "processing_time": f"{metrics['processing_time_seconds']:.2f} seconds"
        },
        "top_candidates": candidate_details[:10],  # Top 10 candidates
        "analysis": {
            "most_common_missing_skills": summary.get('most_common_missing_skills', []),
            "experience_distribution": summary.get('experience_distribution', {}),
            "location_distribution": summary.get('location_distribution', {}),
            "score_distribution": {
                "highest_score": summary.get('highest_score', 0),
                "lowest_score": summary.get('lowest_score', 0),
                "average_score": summary.get('average_score', 0)
            }
        },
        "recommendations": _generate_recommendations(state),
        "errors": state.get("processing_errors", [])
    }
    
    return report

def _generate_recommendations(state: ScreeningState) -> List[str]:
    """Generate recommendations based on screening results"""
    
    recommendations = []
    metrics = state["screening_metrics"]
    summary = metrics.get('summary', {})
    
    # Pass rate analysis
    pass_rate = metrics["passed_count"] / metrics["total_processed"] * 100
    if pass_rate < 20:
        recommendations.append("Consider adjusting screening criteria - pass rate is very low")
    elif pass_rate > 80:
        recommendations.append("Consider raising screening standards - pass rate is very high")
    
    # Shortlist analysis
    shortlist_rate = metrics["shortlisted_count"] / metrics["total_processed"] * 100
    if shortlist_rate < 10:
        recommendations.append("Consider lowering shortlist threshold or expanding sourcing")
    
    # Common missing skills
    missing_skills = summary.get('most_common_missing_skills', [])
    if missing_skills:
        recommendations.append(f"Focus sourcing on candidates with {', '.join(missing_skills[:3])} skills")
    
    # Experience distribution
    exp_dist = summary.get('experience_distribution', {})
    under_count = exp_dist.get('under', 0)
    total = sum(exp_dist.values()) if exp_dist else 1
    
    if under_count / total > 0.5:
        recommendations.append("Many candidates are under-experienced - consider junior-friendly roles or training programs")
    
    # Processing efficiency
    if metrics["error_count"] > 0:
        recommendations.append("Review data quality - errors encountered during processing")
    
    if not recommendations:
        recommendations.append("Screening process completed successfully with good candidate quality")
    
    return recommendations