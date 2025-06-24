from langgraph.graph import StateGraph, START, END
from models.sourcing import SourcingState
from nodes.sourcing import initialize_sourcing, execute_sourcing, finalize_sourcing, check_sourcing_completion

def create_sourcing_workflow() -> StateGraph:
    """Create the sourcing workflow graph with better error handling"""
    
    # Create workflow with updated StateGraph
    workflow = StateGraph(SourcingState)
    
    # Add nodes
    workflow.add_node("initialize_sourcing", initialize_sourcing)
    workflow.add_node("execute_sourcing", execute_sourcing)
    workflow.add_node("finalize_sourcing", finalize_sourcing)
    
    # Add edges
    workflow.add_edge(START, "initialize_sourcing")
    workflow.add_edge("initialize_sourcing", "execute_sourcing")
    
    # Conditional edge for sourcing completion check
    workflow.add_conditional_edges(
        "execute_sourcing",
        check_sourcing_completion,
        {
            "continue_sourcing": "execute_sourcing",
            "sourcing_complete": "finalize_sourcing"
        }
    )
    
    workflow.add_edge("finalize_sourcing", END)
    
    return workflow.compile()