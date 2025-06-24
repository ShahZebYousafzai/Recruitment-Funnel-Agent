from datetime import datetime
from models.sourcing import SourcingState
from agents.sourcing import SourcingAgent
import logging
from utils import ensure_state_completeness, safe_add_message

def initialize_sourcing(state: SourcingState) -> SourcingState:
    """Initialize the sourcing process with error handling"""
    # Ensure state completeness
    state = ensure_state_completeness(state)
    
    # Reset sourcing-specific fields
    state["raw_candidates"] = []
    state["sourcing_metrics"] = {}
    state["errors"] = []
    state["channels_completed"] = []
    state["total_candidates_found"] = 0
    state["sourcing_complete"] = False
    
    if state["sourcing_channels"]:
        state["current_channel"] = state["sourcing_channels"][0]
    
    # Add initialization message (safely)
    init_message = {
        "type": "system",
        "content": f"🚀 Starting candidate sourcing for job: {state['job_title']}"
    }
    state = safe_add_message(state, init_message)
    
    print(f"🚀 Starting candidate sourcing for job: {state['job_title']}")
    print(f"📍 Location: {state['location']}")
    print(f"🎯 Target skills: {', '.join(state['required_skills'])}")
    print(f"📡 Channels: {', '.join(state['sourcing_channels'])}")
    
    return state

def execute_sourcing(state: SourcingState) -> SourcingState:
    """Execute sourcing from current channel with error handling"""
    # Ensure state completeness
    state = ensure_state_completeness(state)
    
    # Import here to avoid circular imports
    from agents.sourcing import SourcingAgent
    
    agent = SourcingAgent()
    current_channel = state["current_channel"]
    
    print(f"🔍 Sourcing from: {current_channel}")
    
    try:
        # Source candidates from current channel
        candidates = agent.source_from_channel(current_channel, state)
        
        # Add to results
        state["raw_candidates"].extend(candidates)
        
        # Update metrics
        state["sourcing_metrics"][current_channel] = {
            "candidates_found": len(candidates),
            "sourced_at": datetime.now().isoformat(),
            "success": True
        }
        
        # Add success message (safely)
        success_message = {
            "type": "system",
            "content": f"✅ Found {len(candidates)} candidates from {current_channel}"
        }
        state = safe_add_message(state, success_message)
        
        print(f"✅ Found {len(candidates)} candidates from {current_channel}")
        
    except Exception as e:
        error_msg = f"Error sourcing from {current_channel}: {str(e)}"
        state["errors"].append(error_msg)
        state["sourcing_metrics"][current_channel] = {
            "candidates_found": 0,
            "error": error_msg,
            "success": False
        }
        
        # Add error message (safely)
        error_message = {
            "type": "system",
            "content": f"❌ {error_msg}"
        }
        state = safe_add_message(state, error_message)
        
        print(f"❌ {error_msg}")
        logging.error(f"Sourcing error: {e}", exc_info=True)
    
    # Mark channel as completed
    state["channels_completed"].append(current_channel)
    state["total_candidates_found"] = len(state["raw_candidates"])
    
    return state

def check_sourcing_completion(state: SourcingState) -> str:
    """Check if sourcing is complete"""
    remaining_channels = [
        ch for ch in state["sourcing_channels"] 
        if ch not in state["channels_completed"]
    ]
    
    if remaining_channels:
        # Move to next channel
        state["current_channel"] = remaining_channels[0]
        return "continue_sourcing"
    else:
        # All channels completed
        state["sourcing_complete"] = True
        return "sourcing_complete"

def finalize_sourcing(state: SourcingState) -> SourcingState:
    """Finalize sourcing stage and prepare summary"""
    # Ensure state completeness
    state = ensure_state_completeness(state)
    
    total_candidates = len(state["raw_candidates"])
    successful_channels = [
        ch for ch, metrics in state["sourcing_metrics"].items()
        if metrics.get("success", False)
    ]
    
    # Add final summary message (safely)
    summary = f"📊 SOURCING COMPLETE - Found {total_candidates} candidates from {len(successful_channels)} channels"
    summary_message = {
        "type": "system",
        "content": summary
    }
    state = safe_add_message(state, summary_message)
    
    print(f"\n📊 SOURCING COMPLETE")
    print(f"🎯 Total candidates found: {total_candidates}")
    print(f"✅ Successful channels: {', '.join(successful_channels)}")
    print(f"📈 Channel breakdown:")
    
    for channel, metrics in state["sourcing_metrics"].items():
        status = "✅" if metrics.get("success") else "❌"
        count = metrics.get("candidates_found", 0)
        print(f"   {status} {channel}: {count} candidates")
    
    if state["errors"]:
        print(f"⚠️ Errors encountered: {len(state['errors'])}")
        for error in state["errors"]:
            print(f"   - {error}")
    
    return state
