from langgraph.graph import StateGraph, START, END
from models.outreach import OutreachState
from nodes.outreach import (
    initialize_outreach, prepare_emails, send_outreach_emails, 
    track_email_responses, finalize_outreach, check_outreach_completion
)

def create_outreach_workflow() -> StateGraph:
    """Create the outreach workflow graph"""
    
    # Create workflow with OutreachState
    workflow = StateGraph(OutreachState)
    
    # Add nodes
    workflow.add_node("initialize_outreach", initialize_outreach)
    workflow.add_node("prepare_emails", prepare_emails)
    workflow.add_node("send_emails", send_outreach_emails)
    workflow.add_node("track_responses", track_email_responses)
    workflow.add_node("finalize_outreach", finalize_outreach)
    
    # Add edges
    workflow.add_edge(START, "initialize_outreach")
    workflow.add_edge("initialize_outreach", "prepare_emails")
    workflow.add_edge("prepare_emails", "send_emails")
    workflow.add_edge("send_emails", "track_responses")
    workflow.add_edge("track_responses", "finalize_outreach")
    workflow.add_edge("finalize_outreach", END)
    
    return workflow.compile()

def create_outreach_state(
    shortlisted_candidates: list,
    job_requirements: dict,
    outreach_config: dict = None
) -> OutreachState:
    """Create initial state for outreach workflow"""
    
    # Default outreach configuration
    if outreach_config is None:
        outreach_config = {
            "recruiter_name": "Sarah Johnson",
            "recruiter_title": "Senior Technical Recruiter", 
            "recruiter_email": "sarah.johnson@company.com",
            "recruiter_phone": "+1-555-0123",
            "company_name": "TechCorp Inc.",
            "stagger_seconds": 30,
            "enable_tracking": True,
            "follow_up_days": 7
        }
    
    return OutreachState(
        shortlisted_candidates=shortlisted_candidates,
        job_requirements=job_requirements,
        outreach_config=outreach_config,
        email_template_id="initial_outreach_v1",
        campaign_id="",
        campaign_status="draft",
        emails_to_send=[],
        sent_emails=[],
        current_email_index=0,
        total_emails=len(shortlisted_candidates),
        outreach_metrics={},
        email_statuses={},
        processing_errors=[],
        outreach_complete=False,
        messages=[]
    )