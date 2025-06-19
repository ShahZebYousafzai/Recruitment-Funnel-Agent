# simple_test_email.py
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_imports():
    """Test that we can import everything we need"""
    print("🔍 Testing imports...")
    try:
        from agents.interview_agent import InterviewAgent
        from models.candidate import Candidate
        from models.job_description import JobDescription
        from config.settings import settings
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\n🔍 Testing email configuration...")
    
    try:
        from agents.interview_agent import InterviewAgent
        from config.settings import settings
        
        print("Current email settings:")
        print(f"  EMAIL_HOST: '{settings.EMAIL_HOST}'")
        print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"  EMAIL_HOST_USER: '{settings.EMAIL_HOST_USER}'")
        print(f"  EMAIL_HOST_PASSWORD: {'***SET***' if settings.EMAIL_HOST_PASSWORD else '***NOT SET***'}")
        print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        
        # Create agent
        agent = InterviewAgent()
        
        if agent.email_enabled:
            print("✅ Email service is enabled")
        else:
            print("❌ Email service is disabled - check your .env file")
            return False
        
        # Test connection
        config_result = agent.test_email_configuration()
        print(f"Connection test: {'✅ SUCCESS' if config_result['success'] else '❌ FAILED'}")
        print(f"Message: {config_result['message']}")
        
        if not config_result['success']:
            if 'error' in config_result:
                print(f"Error: {config_result['error']}")
            if 'suggestion' in config_result:
                print(f"Suggestion: {config_result['suggestion']}")
        
        return config_result['success']
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_email_generation():
    """Test email generation without sending"""
    print("\n🔍 Testing email generation...")
    
    try:
        from agents.interview_agent import InterviewAgent
        from models.candidate import Candidate
        from models.job_description import JobDescription
        
        # Create test data
        candidate = Candidate(
            name="Test Candidate",
            email="test@example.com",
            phone="+1-555-0123",
            resume_text="Test resume content...",
            skills=["Python", "Machine Learning", "AWS"],
            experience_years=3.0
        )
        
        job_desc = JobDescription(
            title="Software Engineer",
            company="Test Company",
            description="Test job description...",
            required_skills=["Python", "AWS"]
        )
        
        # Create agent and disable email sending for testing
        agent = InterviewAgent()
        original_email_enabled = agent.email_enabled
        agent.email_enabled = False  # Just generate, don't send
        
        # Generate email
        result = agent.execute({
            'candidate': candidate,
            'job_description': job_desc,
            'action': 'send_initial_email'
        })
        
        print("✅ Email generation successful")
        print(f"Subject: {result['email_content']['subject']}")
        print(f"Body preview: {result['email_content']['body'][:100]}...")
        
        # Restore original setting
        agent.email_enabled = original_email_enabled
        
        return True
        
    except Exception as e:
        print(f"❌ Email generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_send_real_email():
    """Test sending a real email if user wants to"""
    print("\n🔍 Testing real email sending...")
    
    try:
        from agents.interview_agent import InterviewAgent
        
        agent = InterviewAgent()
        
        if not agent.email_enabled:
            print("❌ Email is not configured, skipping real email test")
            return True
        
        # Ask user for email
        test_email = input("Enter your email to receive a test email (or press Enter to skip): ").strip()
        
        if not test_email:
            print("Skipping real email test")
            return True
        
        print(f"Sending test email to: {test_email}")
        
        # Send test email using the email service directly
        result = agent.email_service.send_test_email(test_email)
        
        print(f"Result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        print(f"Message: {result['message']}")
        
        if not result['success'] and 'error' in result:
            print(f"Error: {result['error']}")
            if 'suggestion' in result:
                print(f"Suggestion: {result['suggestion']}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Real email test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("📧 Simple Email Test Suite\n")
    
    # Test 1: Imports
    imports_ok = test_email_imports()
    if not imports_ok:
        print("\n❌ Fix import issues before continuing")
        return
    
    # Test 2: Configuration
    config_ok = test_email_configuration()
    
    # Test 3: Email Generation
    generation_ok = test_email_generation()
    
    # Test 4: Real Email (optional)
    if config_ok:
        real_email_ok = test_send_real_email()
    else:
        real_email_ok = True  # Skip if config is bad
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"✅ Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"✅ Configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"✅ Email Generation: {'PASS' if generation_ok else 'FAIL'}")
    print(f"✅ Real Email: {'PASS' if real_email_ok else 'FAIL'}")
    
    if all([imports_ok, config_ok, generation_ok]):
        print("\n🎉 Core email functionality is working!")
        if not config_ok:
            print("\n💡 To enable email sending:")
            print("1. Check your .env file")
            print("2. Make sure EMAIL_HOST=smtp.gmail.com")
            print("3. Use your Gmail App Password")
            print("4. Run: python debug_email_config.py")
    else:
        print("\n🔧 Some tests failed. Check the errors above.")
    
    print(f"\n📁 Next: Run 'python debug_email_config.py' to fix configuration issues")

if __name__ == "__main__":
    main()