import sys
import traceback
from typing import List, Dict, Any
from datetime import datetime

def test_basic_imports():
    """Test that all basic imports work"""
    print("🧪 Testing Basic Imports...")
    
    try:
        # Test LangGraph imports
        from langgraph.graph import StateGraph, END, START
        from langgraph.graph.message import add_messages
        print("✅ LangGraph imports successful")
        
        # Test LangChain imports
        from langchain_core.tools import StructuredTool
        from langchain_openai import ChatOpenAI
        print("✅ LangChain imports successful")
        
        # Test Pydantic imports
        from pydantic import BaseModel, Field
        print("✅ Pydantic imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_model_creation():
    """Test that Pydantic models work correctly"""
    print("\n🧪 Testing Model Creation...")
    
    try:
        from pydantic import BaseModel, Field
        from typing import List, Optional
        from datetime import datetime
        from enum import Enum
        
        class SourceChannel(str, Enum):
            LINKEDIN = "linkedin"
            INDEED = "indeed"
            DATABASE = "database"
        
        class CandidateProfile(BaseModel):
            source: SourceChannel
            source_id: str
            name: Optional[str] = None
            email: Optional[str] = None
            skills: List[str] = Field(default_factory=list)
            raw_data: Dict[str, Any] = Field(default_factory=dict)
            sourced_at: datetime = Field(default_factory=datetime.now)
        
        # Test model creation
        candidate = CandidateProfile(
            source=SourceChannel.LINKEDIN,
            source_id="test_123",
            name="Test Candidate",
            email="test@example.com",
            skills=["Python", "AI"]
        )
        
        print(f"✅ Created candidate: {candidate.name}")
        
        # Test JSON serialization
        json_data = candidate.model_dump_json()
        print("✅ JSON serialization works")
        
        # Test deserialization
        candidate_from_json = CandidateProfile.model_validate_json(json_data)
        print("✅ JSON deserialization works")
        
        return True
    except Exception as e:
        print(f"❌ Model creation test failed: {e}")
        traceback.print_exc()
        return False

def test_tool_creation():
    """Test that StructuredTool creation works"""
    print("\n🧪 Testing Tool Creation...")
    
    try:
        from langchain_core.tools import StructuredTool
        from pydantic import BaseModel, Field
        from typing import List
        
        class SearchInput(BaseModel):
            job_title: str = Field(description="Job title to search for")
            location: str = Field(description="Location")
            skills: List[str] = Field(description="Required skills")
            max_results: int = Field(default=10, description="Max results")
        
        def mock_search(job_title: str, location: str, skills: List[str], max_results: int = 10):
            """Mock search function"""
            return [
                {
                    "id": f"candidate_{i}",
                    "name": f"Candidate {i}",
                    "title": job_title,
                    "location": location,
                    "skills": skills[:2]
                }
                for i in range(min(3, max_results))
            ]
        
        # Create tool
        search_tool = StructuredTool.from_function(
            func=mock_search,
            name="mock_search_tool",
            description="Mock search for testing",
            args_schema=SearchInput
        )
        
        print(f"✅ Created tool: {search_tool.name}")
        
        # Test tool execution
        result = search_tool.invoke({
            "job_title": "AI Engineer",
            "location": "San Francisco",
            "skills": ["Python", "ML"],
            "max_results": 2
        })
        
        print(f"✅ Tool execution successful, got {len(result)} results")
        return True
        
    except Exception as e:
        print(f"❌ Tool creation test failed: {e}")
        traceback.print_exc()
        return False

def test_workflow_creation():
    """Test that LangGraph workflow creation works"""
    print("\n🧪 Testing Workflow Creation...")
    
    try:
        from langgraph.graph import StateGraph, END, START
        from langgraph.graph.message import add_messages
        from typing import TypedDict, Annotated, List
        
        class TestState(TypedDict):
            job_title: str
            candidates: List[Dict[str, Any]]
            current_step: str
            messages: Annotated[List, add_messages]
        
        def initialize_node(state: TestState) -> TestState:
            """Initialize the workflow"""
            state = state.copy()
            state["current_step"] = "initialized"
            state["messages"].append({
                "type": "system",
                "content": f"Initialized workflow for {state['job_title']}"
            })
            return state
        
        def process_node(state: TestState) -> TestState:
            """Process node"""
            state = state.copy()
            state["candidates"] = [
                {"name": "Test Candidate 1", "source": "test"},
                {"name": "Test Candidate 2", "source": "test"}
            ]
            state["current_step"] = "processed"
            state["messages"].append({
                "type": "system",
                "content": f"Found {len(state['candidates'])} candidates"
            })
            return state
        
        # Create workflow
        workflow = StateGraph(TestState)
        
        # Add nodes
        workflow.add_node("initialize", initialize_node)
        workflow.add_node("process", process_node)
        
        # Add edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "process")
        workflow.add_edge("process", END)
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        print("✅ Workflow compilation successful")
        
        # Test workflow execution
        initial_state = TestState(
            job_title="Test Engineer",
            candidates=[],
            current_step="",
            messages=[]
        )
        
        result = compiled_workflow.invoke(initial_state)
        
        print(f"✅ Workflow execution successful")
        print(f"   Final step: {result['current_step']}")
        print(f"   Candidates found: {len(result['candidates'])}")
        print(f"   Messages: {len(result['messages'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow creation test failed: {e}")
        traceback.print_exc()
        return False

def test_complete_integration():
    """Test complete integration of tools + workflow"""
    print("\n🧪 Testing Complete Integration...")
    
    try:
        from langgraph.graph import StateGraph, END, START
        from langgraph.graph.message import add_messages
        from langchain_core.tools import StructuredTool
        from pydantic import BaseModel, Field
        from typing import TypedDict, Annotated, List, Dict, Any
        from enum import Enum
        
        # Define models
        class SourceChannel(str, Enum):
            LINKEDIN = "linkedin"
            INDEED = "indeed"
        
        class SourcingState(TypedDict):
            job_title: str
            required_skills: List[str]
            location: str
            candidates: List[Dict[str, Any]]
            current_channel: str
            channels: List[str]
            completed_channels: List[str]
            messages: Annotated[List, add_messages]
        
        # Create tools
        class LinkedInInput(BaseModel):
            job_title: str = Field(description="Job title")
            location: str = Field(description="Location")
            skills: List[str] = Field(description="Skills")
        
        def linkedin_search(job_title: str, location: str, skills: List[str]):
            return [
                {
                    "id": "linkedin_1",
                    "name": "LinkedIn Candidate 1",
                    "source": "linkedin",
                    "title": job_title,
                    "location": location,
                    "skills": skills[:2]
                },
                {
                    "id": "linkedin_2", 
                    "name": "LinkedIn Candidate 2",
                    "source": "linkedin",
                    "title": job_title,
                    "location": location,
                    "skills": skills[:1]
                }
            ]
        
        linkedin_tool = StructuredTool.from_function(
            func=linkedin_search,
            name="linkedin_sourcer",
            description="Search LinkedIn for candidates",
            args_schema=LinkedInInput
        )
        
        # Create workflow nodes
        def sourcing_node(state: SourcingState) -> SourcingState:
            """Execute sourcing"""
            state = state.copy()
            
            if state["current_channel"] == "linkedin":
                results = linkedin_tool.invoke({
                    "job_title": state["job_title"],
                    "location": state["location"],
                    "skills": state["required_skills"]
                })
                
                state["candidates"].extend(results)
                state["completed_channels"].append("linkedin")
                state["messages"].append({
                    "type": "system",
                    "content": f"Found {len(results)} candidates from LinkedIn"
                })
            
            return state
        
        def check_completion(state: SourcingState) -> str:
            """Check if sourcing is complete"""
            remaining = [ch for ch in state["channels"] if ch not in state["completed_channels"]]
            if remaining:
                state["current_channel"] = remaining[0]
                return "continue"
            return "complete"
        
        def finalize_node(state: SourcingState) -> SourcingState:
            """Finalize sourcing"""
            state = state.copy()
            state["messages"].append({
                "type": "system",
                "content": f"Sourcing complete! Found {len(state['candidates'])} total candidates"
            })
            return state
        
        # Create workflow
        workflow = StateGraph(SourcingState)
        workflow.add_node("sourcing", sourcing_node)
        workflow.add_node("finalize", finalize_node)
        
        workflow.add_edge(START, "sourcing")
        workflow.add_conditional_edges(
            "sourcing",
            check_completion,
            {
                "continue": "sourcing",
                "complete": "finalize"
            }
        )
        workflow.add_edge("finalize", END)
        
        compiled_workflow = workflow.compile()
        
        # Test execution
        initial_state = SourcingState(
            job_title="AI Engineer",
            required_skills=["Python", "Machine Learning"],
            location="San Francisco",
            candidates=[],
            current_channel="linkedin",
            channels=["linkedin"],
            completed_channels=[],
            messages=[]
        )
        
        result = compiled_workflow.invoke(initial_state)
        
        print(f"✅ Complete integration test successful")
        print(f"   Job: {result['job_title']}")
        print(f"   Candidates found: {len(result['candidates'])}")
        print(f"   Channels completed: {result['completed_channels']}")
        print(f"   Messages: {len(result['messages'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete integration test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all compatibility tests"""
    print("🔧 RUNNING COMPLETE COMPATIBILITY TEST SUITE")
    print("=" * 60)
    print("Testing Pydantic v2 + LangGraph API compatibility...")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Model Creation (Pydantic v2)", test_model_creation),
        ("Tool Creation (StructuredTool)", test_tool_creation),
        ("Workflow Creation (LangGraph)", test_workflow_creation),
        ("Complete Integration", test_complete_integration)
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 TEST RESULTS")
    print("=" * 40)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ Pydantic v2 compatibility: WORKING")
        print("✅ LangGraph API compatibility: WORKING") 
        print("✅ Tool creation and execution: WORKING")
        print("✅ Workflow creation and execution: WORKING")
        print("✅ End-to-end integration: WORKING")
    else:
        print(f"\n⚠️ {len(failed_tests)} tests failed.")
        print("Please check the error messages above and:")
        print("1. Ensure all dependencies are installed correctly")
        print("2. Check Python version compatibility")
        print("3. Verify import paths match your project structure")
        print("4. Install missing packages if needed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    print(f"\n🎯 Overall Test Suite: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)