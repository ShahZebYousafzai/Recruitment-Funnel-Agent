# quick_fix_test.py
"""
Quick test to verify the screening questions system is working after fixes
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.interview_agent import InterviewAgent
from models.candidate import Candidate
from models.job_description import JobDescription

def test_candidate_creation():
    """Test creating candidates with proper fields"""
    print("🔧 Testing Candidate Creation Fix\n")
    
    try:
        # Create candidate with all required fields
        candidate = Candidate(
            name="Alex Johnson",
            email="zebshah7851@gmail.com",
            phone="+1-555-0123",
            resume_text="Experienced AI engineer with strong background in machine learning...",  # Required field
            skills=["Python", "TensorFlow", "AWS", "Computer Vision"],
            experience_years=3.5
        )
        
        print(f"✅ Candidate created successfully: {candidate.name}")
        print(f"   Email: {candidate.email}")
        print(f"   Skills: {', '.join(candidate.skills)}")
        print(f"   Experience: {candidate.experience_years} years")
        return True
        
    except Exception as e:
        print(f"❌ Candidate creation failed: {str(e)}")
        return False

def test_questions_generation():
    """Test screening questions generation"""
    print("\n🧠 Testing Questions Generation\n")
    
    try:
        # Create proper candidate and job objects
        candidate = Candidate(
            name="Sarah Kim",
            email="zebshah7851@gmail.com",
            phone="+1-555-0124",
            resume_text="Senior AI engineer with 4.5 years of experience in deep learning and computer vision. Led multiple projects using TensorFlow and PyTorch.",
            skills=["Python", "TensorFlow", "PyTorch", "Computer Vision", "Deep Learning"],
            experience_years=4.5
        )
        
        job = JobDescription(
            title="Senior AI Engineer",
            company="AI Innovations",
            description="Build cutting-edge AI solutions using deep learning and computer vision technologies...",
            required_skills=["Python", "TensorFlow", "Deep Learning", "Computer Vision"],
            min_experience=3.0
        )
        
        # Create agent and test questions generation
        agent = InterviewAgent()
        
        questions_data = agent.questions_generator.generate_screening_questions(
            candidate=candidate,
            job_description=job,
            num_questions=4,
            categories=['technical', 'experience', 'motivation']
        )
        
        print(f"✅ Generated {len(questions_data['questions'])} questions:")
        for i, q in enumerate(questions_data['questions'], 1):
            print(f"   {i}. [{q['category'].upper()}] {q['question'][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Questions generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_email_integration():
    """Test email integration for screening questions"""
    print("\n📧 Testing Email Integration\n")
    
    try:
        candidate = Candidate(
            name="Test User",
            email="zebshah7851@gmail.com", 
            phone="+1-555-0125",
            resume_text="Full-stack developer with 3 years of experience...",
            skills=["JavaScript", "React", "Node.js", "Python"],
            experience_years=3.0
        )
        
        job = JobDescription(
            title="Full Stack Developer",
            company="TechCorp",
            description="Develop modern web applications...",
            required_skills=["JavaScript", "React", "Node.js"],
            min_experience=2.0
        )
        
        agent = InterviewAgent()
        
        # Test the send_questions action
        result = agent.execute({
            'candidate': candidate,
            'job_description': job,
            'action': 'send_questions'
        })
        
        print(f"Action result: {result['status']}")
        print(f"Questions generated: {'questions_data' in result}")
        print(f"Email content created: {'email_content' in result}")
        
        if 'email_content' in result:
            email = result['email_content']
            print(f"Email subject: {email['subject']}")
            print(f"Email preview: {email['body'][:100]}...")
        
        if result.get('error'):
            print(f"Error details: {result['error']}")
        
        print("✅ Email integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Email integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_real_email_sending():
    """Test actual email sending (optional)"""
    print("\n📨 Testing Real Email Sending\n")
    
    test_email = input("Enter your email to test real sending (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipping real email test")
        return True
    
    try:
        candidate = Candidate(
            name="Demo Candidate",
            email=test_email,
            phone="+1-555-0126",
            resume_text="AI engineer with expertise in machine learning and computer vision...",
            skills=["Python", "TensorFlow", "Computer Vision", "AWS"],
            experience_years=4.0
        )
        
        job = JobDescription(
            title="AI Engineer",
            company="Demo Company", 
            description="Work on exciting AI projects...",
            required_skills=["Python", "TensorFlow", "Machine Learning"],
            min_experience=3.0
        )
        
        agent = InterviewAgent()
        
        if not agent.email_enabled:
            print("❌ Email not configured - check your .env file")
            return False
        
        print(f"Sending screening questions to: {test_email}")
        
        result = agent.execute({
            'candidate': candidate,
            'job_description': job,
            'action': 'send_questions'
        })
        
        if result.get('email_sent'):
            print("✅ Email sent successfully!")
            print(f"Status: {result['status']}")
            if result.get('email_timestamp'):
                print(f"Sent at: {result['email_timestamp']}")
        else:
            print("❌ Email sending failed")
            print(f"Status: {result.get('email_status', 'Unknown')}")
            if result.get('error'):
                print(f"Error: {result['error']}")
        
        return result.get('email_sent', False)
        
    except Exception as e:
        print(f"❌ Real email test failed: {str(e)}")
        return False

def main():
    """Run all fix tests"""
    print("🔧 Quick Fix Test Suite")
    print("=" * 50)
    print("Testing fixes for screening questions system\n")
    
    tests = [
        ("Candidate Creation", test_candidate_creation),
        ("Questions Generation", test_questions_generation),
        ("Email Integration", test_email_integration),
        ("Real Email Sending", test_real_email_sending)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            break
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Screening questions system is working!")
    else:
        print(f"\n🔧 {total - passed} tests failed. Check the errors above.")
    
    print("\n💡 If email sending failed:")
    print("1. Check your .env file configuration")
    print("2. Verify EMAIL_HOST=smtp.gmail.com")
    print("3. Use Gmail App Password (not regular password)")
    print("4. Run: python debug_email_config.py")

if __name__ == "__main__":
    main()