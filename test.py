# simple_test.py - Test the response processing system

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.candidate import Candidate, CandidateStatus
from models.job_description import JobDescription
from agents.interview_agent import InterviewAgent

def test_response_processing():
    """Test the response processing functionality"""
    
    print("🧪 Testing Response Processing System")
    print("=" * 50)
    
    # Create test data
    candidate = Candidate(
        id="test_001",
        name="Test Candidate",
        email="test@example.com",
        skills=["Python", "Django", "AWS"],
        experience_years=3.0,
        status=CandidateStatus.SCREENED
    )
    
    job_desc = JobDescription(
        title="Senior Developer",
        company="Test Corp",
        description="Great opportunity for developers",
        required_skills=["Python", "Django", "AWS"]
    )
    
    # Initialize interview agent
    agent = InterviewAgent()
    
    # First, send screening questions
    print(f"\n1. Sending screening questions to {candidate.name}")
    questions_result = agent.execute({
        'candidate': candidate,
        'job_description': job_desc,
        'action': 'send_questions'
    })
    
    print(f"   Questions sent: {questions_result['status']}")
    
    # Simulate candidate response
    response_text =  """
            Hi,

            1. I'm learning Python and Django. Haven't used AWS yet but willing to learn.
            2. I don't have much experience with complex problems yet.
            3. This seems like a good opportunity for someone starting out.
            4. Available immediately.
            """
    
    # Process the response
    print(f"\n2. Processing response from {candidate.name}")
    
    try:
        result = agent.process_email_response(
            candidate=candidate,
            email_content=response_text,
            job_description=job_desc
        )
        
        if result['status'] == 'response_analyzed':
            analysis = result['analysis']
            
            print(f"   ✅ Analysis completed!")
            print(f"   📊 Overall Score: {analysis.overall_score:.2f}/1.0")
            print(f"   🎯 Fit Level: {analysis.fit_level.value.replace('_', ' ').title()}")
            print(f"   📝 Recommendation: {analysis.recommendation}")
            
            if analysis.strengths:
                print(f"   ✅ Strengths: {'; '.join(analysis.strengths[:2])}")
            
            if analysis.concerns:
                print(f"   ⚠️ Concerns: {'; '.join(analysis.concerns[:2])}")
            
            print(f"   🎬 Next Action: {result['next_action']}")
            
            # Test manual review queue
            print(f"\n3. Testing manual review system")
            queue = agent.get_manual_review_queue()
            print(f"   Manual review queue: {len(queue)} candidates")
            
            print(f"\n✅ All tests passed!")
            
        else:
            print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_response_processing()