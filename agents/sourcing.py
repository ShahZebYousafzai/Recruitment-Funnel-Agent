from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from source_tools.DatabaseSourcingTool import create_database_tool
from source_tools.IndeedAPITool import create_indeed_tool
from source_tools.linkedInJobAPITool import create_linkedin_tool
from models.sourcing import SourcingState, SourceChannel
from utils import create_candidate_from_raw_data
import logging

class SourcingAgent:
    """Main sourcing agent - Updated for current LangGraph API"""
    
    def __init__(self, llm_model: str = "gpt-4", api_keys: Optional[Dict[str, str]] = None):
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.api_keys = api_keys or {}
        self.tools = self._initialize_tools()
        # No longer using ToolExecutor - tools are called directly
        
    def _initialize_tools(self) -> List[StructuredTool]:
        """Initialize all sourcing tools"""
        return [
            create_linkedin_tool(),
            create_indeed_tool(),
            create_database_tool()
        ]
    
    def get_tool_by_name(self, tool_name: str) -> Optional[StructuredTool]:
        """Get tool by name"""
        return next((tool for tool in self.tools if tool.name == tool_name), None)
    
    def source_from_channel(self, channel: str, state: SourcingState) -> List[Dict[str, Any]]:
        """Source candidates from a specific channel"""
        try:
            tool_map = {
                "linkedin": "linkedin_sourcer",
                "indeed": "indeed_sourcer", 
                "database": "database_sourcer"
            }
            
            if channel not in tool_map:
                raise ValueError(f"Unknown sourcing channel: {channel}")
            
            tool_name = tool_map[channel]
            tool = self.get_tool_by_name(tool_name)
            
            if not tool:
                raise ValueError(f"Tool {tool_name} not found")
            
            # Execute sourcing based on channel type
            if channel == "linkedin":
                raw_results = tool.invoke({
                    "job_title": state["job_title"],
                    "location": state["location"],
                    "skills": state["required_skills"],
                    "max_results": state["max_candidates_per_channel"]
                })
            elif channel == "indeed":
                raw_results = tool.invoke({
                    "job_title": state["job_title"],
                    "location": state["location"],
                    "skills": state["required_skills"],
                    "max_results": state["max_candidates_per_channel"]
                })
            else:  # database
                raw_results = tool.invoke({
                    "skills": state["required_skills"],
                    "location": state["location"],
                    "experience_level": state["experience_level"],
                    "max_results": state["max_candidates_per_channel"]
                })
            
            # Convert to candidate profiles and back to dicts for state storage
            candidates = []
            for raw_candidate in raw_results:
                # Create candidate profile
                source_channel = SourceChannel.LINKEDIN if channel == "linkedin" else \
                                SourceChannel.INDEED if channel == "indeed" else \
                                SourceChannel.DATABASE
                
                candidate = create_candidate_from_raw_data(raw_candidate, source_channel)
                # Convert back to dict for JSON serialization in state
                candidates.append(candidate.model_dump())
            
            return candidates
            
        except Exception as e:
            logging.error(f"Error sourcing from {channel}: {e}")
            return []