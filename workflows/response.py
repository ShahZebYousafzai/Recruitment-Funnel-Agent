from langgraph.graph import StateGraph, START, END
from models.response import ResponseManagementState, ResponseConfig
from nodes.response import (
    initialize_response_management, collect_candidate_responses,
    analyze_responses_with_llm, execute_follow_up_actions,
    send_follow_up_communications, finalize_response_management,
    check_response_processing_completion
)

def create_response_management_workflow() -> StateGraph:
    """Create the response management workflow graph"""
    
    # Create workflow with ResponseManagementState
    workflow = StateGraph(ResponseManagementState)
    
    # Add nodes
    workflow.add_node("initialize_response_mgmt", initialize_response_management)
    workflow.add_node("collect_responses", collect_candidate_responses)
    workflow.add_node("analyze_with_llm", analyze_responses_with_llm)
    workflow.add_node("execute_actions", execute_follow_up_actions)
    workflow.add_node("send_communications", send_follow_up_communications)
    workflow.add_node("finalize_response_mgmt", finalize_response_management)
    
    # Add edges
    workflow.add_edge(START, "initialize_response_mgmt")
    workflow.add_edge("initialize_response_mgmt", "collect_responses")
    workflow.add_edge("collect_responses", "analyze_with_llm")
    workflow.add_edge("analyze_with_llm", "execute_actions")
    workflow.add_edge("execute_actions", "send_communications")
    workflow.add_edge("send_communications", "finalize_response_mgmt")
    workflow.add_edge("finalize_response_mgmt", END)
    
    return workflow.compile()

def create_response_management_state(
    sent_emails: list,
    email_statuses: dict,
    job_requirements: dict,
    response_config: dict = None
) -> ResponseManagementState:
    """Create initial state for response management workflow"""
    
    # Default response configuration
    if response_config is None:
        default_config = ResponseConfig()
        response_config = default_config.model_dump()
    
    return ResponseManagementState(
        sent_emails=sent_emails,
        email_statuses=email_statuses,
        job_requirements=job_requirements,
        response_config=response_config,
        
        incoming_responses=[],
        processed_responses=[],
        analysis_results=[],
        available_interview_slots=[],
        scheduled_interviews=[],
        follow_up_emails=[],
        pending_actions=[],
        
        current_response_index=0,
        total_responses=0,
        processing_complete=False,
        response_management_complete=False,
        
        response_metrics={},
        processing_errors=[],
        messages=[]
    )