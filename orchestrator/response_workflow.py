# orchestrator/response_workflow.py

import time
from typing import Dict, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"

@dataclass
class ResponseWorkflow:
    workflow_id: str
    candidate_id: str
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict

class ResponseWorkflowOrchestrator:
    """Simple orchestrator for response processing workflows"""
    
    def __init__(self, interview_agent, email_integration=None):
        self.interview_agent = interview_agent
        self.email_integration = email_integration
        self.workflows = {}
        self.is_running = False
        self.stats = {
            'total_responses_processed': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'manual_reviews': 0,
            'automated_actions': 0
        }
    
    def start_orchestrator(self, check_interval: int = 30):
        """Start the workflow orchestrator"""
        self.is_running = True
        print(f"🚀 Starting Response Workflow Orchestrator (check interval: {check_interval}s)")
    
    def process_candidate_response(self, candidate, response_text: str, 
                                 job_description=None, email_metadata: Dict = None) -> str:
        """Process a candidate response and create workflow"""
        
        workflow_id = f"workflow_{candidate.id}_{int(time.time())}"
        
        # Create workflow
        workflow = ResponseWorkflow(
            workflow_id=workflow_id,
            candidate_id=candidate.id,
            status=WorkflowStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'candidate_name': candidate.name,
                'candidate_email': candidate.email,
                'response_length': len(response_text.split()),
                'email_metadata': email_metadata or {}
            }
        )
        
        self.workflows[workflow_id] = workflow
        
        # Process the response
        try:
            result = self.interview_agent.process_email_response(
                candidate=candidate,
                email_content=response_text,
                job_description=job_description
            )
            
            if result['status'] == 'response_analyzed':
                workflow.status = WorkflowStatus.COMPLETED
                self.stats['successful_workflows'] += 1
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.metadata['error'] = result.get('error', 'Unknown processing error')
                self.stats['failed_workflows'] += 1
            
        except Exception as e:
            print(f"ERROR: Error processing response for {candidate.name}: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            workflow.metadata['error'] = str(e)
            self.stats['failed_workflows'] += 1
        
        workflow.updated_at = datetime.now()
        self.stats['total_responses_processed'] += 1
        
        print(f"📝 Created workflow {workflow_id} for {candidate.name} - Status: {workflow.status}")
        
        return workflow_id
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get status of a specific workflow"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            'workflow_id': workflow.workflow_id,
            'candidate_id': workflow.candidate_id,
            'status': workflow.status,
            'created_at': workflow.created_at.isoformat(),
            'updated_at': workflow.updated_at.isoformat(),
            'total_actions': 0,  # Simplified
            'completed_actions': 0,  # Simplified
            'failed_actions': 0,  # Simplified
            'metadata': workflow.metadata
        }
    
    def get_all_workflows(self, status_filter=None) -> List[Dict]:
        """Get all workflows, optionally filtered by status"""
        
        workflows = list(self.workflows.values())
        
        if status_filter:
            workflows = [w for w in workflows if w.status == status_filter]
        
        return [self.get_workflow_status(w.workflow_id) for w in workflows]
    
    def get_candidate_workflows(self, candidate_id: str) -> List[Dict]:
        """Get all workflows for a specific candidate"""
        
        candidate_workflows = [
            w for w in self.workflows.values() 
            if w.candidate_id == candidate_id
        ]
        
        return [self.get_workflow_status(w.workflow_id) for w in candidate_workflows]
    
    def generate_dashboard_data(self) -> Dict:
        """Generate dashboard data for monitoring"""
        
        now = datetime.now()
        
        # Status breakdown
        status_counts = {}
        for status in WorkflowStatus:
            status_counts[status.value] = len([
                w for w in self.workflows.values() 
                if w.status == status
            ])
        
        completed_workflows = [
            w for w in self.workflows.values() 
            if w.status == WorkflowStatus.COMPLETED
        ]
        
        return {
            'overview': {
                'total_workflows': len(self.workflows),
                'active_workflows': len([w for w in self.workflows.values() if w.status == WorkflowStatus.PROCESSING]),
                'completed_workflows': len(completed_workflows),
                'failed_workflows': status_counts.get('failed', 0),
                'manual_review_count': status_counts.get('manual_review', 0)
            },
            'recent_activity': {
                'workflows_last_24h': len(self.workflows),
                'workflows_last_hour': len(self.workflows),
                'avg_completion_time_seconds': None
            },
            'status_breakdown': status_counts,
            'system_stats': self.stats,
            'generated_at': now.isoformat()
        }
    
    def stop_orchestrator(self):
        """Stop the workflow orchestrator"""
        self.is_running = False
        print("🛑 Workflow Orchestrator stopped")