import traceback
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing components
from utils import convert_database_candidate
from database.database_integration import CandidateDatabase, test_database_connection
from workflows.screening import create_database_screening_workflow, create_database_screening_state
from models.screening import ScreeningCriteria

# Import REAL email outreach components
from agents.outreach import OutreachAgent
from models.outreach import EmailProvider, OutreachState

def run_real_email_pipeline():
    """Run complete recruitment pipeline with REAL email sending"""
    
    print("🚀 REAL EMAIL RECRUITMENT PIPELINE")
    print("=" * 70)
    print("📋 Stage 1-3: Database Screening")
    print("📧 Stage 5: REAL Email Outreach")
    print("=" * 70)
    
    # Check email configuration
    if not os.path.exists('.env'):
        print("❌ No email configuration found!")
        print("🔧 Run: python setup_real_emails.py")
        return None
    
    # Validate email configuration
    required_vars = ['SMTP_SERVER', 'SMTP_PORT', 'SENDER_EMAIL', 'SENDER_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing email configuration: {', '.join(missing_vars)}")
        print("🔧 Run: python setup_real_emails.py")
        return None
    
    # Display email configuration
    print(f"📧 Email Configuration:")
    print(f"   SMTP: {os.getenv('SMTP_SERVER')}:{os.getenv('SMTP_PORT')}")
    print(f"   Sender: {os.getenv('SENDER_NAME')} <{os.getenv('SENDER_EMAIL')}>")
    print(f"   Company: {os.getenv('COMPANY_NAME')}")
    
    # Final confirmation for real emails
    print(f"\n⚠️  WARNING: This will send REAL emails to candidates!")
    confirm = input("Continue with real email sending? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Pipeline cancelled")
        return None
    
    try:
        # Step 1: Database Connection Test
        print(f"\n🔌 Testing Database Connection...")
        if not test_database_connection():
            print("❌ Database connection failed")
            return None
        
        # Step 2: Job Requirements
        job_requirements = {
            "job_id": "real_email_ai_engineer_001",
            "job_title": "Senior AI Engineer",
            "job_description": """
Join our innovative AI team to build next-generation machine learning solutions that impact millions of users. 
You'll work on cutting-edge projects involving natural language processing, computer vision, and generative AI 
while collaborating with world-class engineers and researchers.
            """.strip(),
            "required_skills": ["Python", "Machine Learning", "PyTorch", "NLP"],
            "preferred_skills": ["Generative AI", "TensorFlow", "LangChain", "Computer Vision"],
            "location": "San Francisco, CA",
            "experience_level": "Senior",
            "min_experience_years": 4,
            "allow_remote": True,
            "company_name": os.getenv('COMPANY_NAME', 'AI Innovations Inc.'),
            "department": "AI Research & Development"
        }
        
        # Step 3: Screening Criteria
        screening_criteria = ScreeningCriteria(
            required_skills_weight=0.4,
            preferred_skills_weight=0.2,
            experience_weight=0.3,
            location_weight=0.1,
            min_experience_years=3,
            preferred_experience_years=5,
            pass_threshold=60.0,
            shortlist_threshold=70.0,  # Higher threshold for real emails
            allow_remote=True
        )
        
        print(f"\n🎯 Job: {job_requirements['job_title']}")
        print(f"🏢 Company: {job_requirements['company_name']}")
        print(f"⚖️ Shortlist Threshold: {screening_criteria.shortlist_threshold}%")
        
        # Step 4: Run Database Screening
        print(f"\n{'='*60}")
        print("🔍 STAGE 1-3: CANDIDATE SCREENING")
        print(f"{'='*60}")
        
        # Get and convert candidates
        db = CandidateDatabase()
        raw_candidates = db.get_candidates_for_job(job_requirements, max_candidates=20)
        
        if not raw_candidates:
            raw_candidates = db.get_all_candidates(max_candidates=10)
        
        print(f"🔧 Converting {len(raw_candidates)} candidates...")
        converted_candidates = []
        
        for candidate in raw_candidates:
            try:
                converted = convert_database_candidate(candidate)
                converted_candidates.append(converted)
            except Exception as e:
                print(f"   ⚠️ Conversion error: {e}")
        
        # Run screening
        screening_state = create_database_screening_state(
            job_requirements=job_requirements,
            screening_criteria=screening_criteria.model_dump(),
            max_candidates=50
        )
        
        screening_state["raw_candidates"] = converted_candidates
        screening_state["total_candidates"] = len(converted_candidates)
        
        screening_workflow = create_database_screening_workflow()
        screening_result = screening_workflow.invoke(screening_state)
        
        # Get screening results
        total_candidates = screening_result["total_candidates"]
        shortlisted_count = len(screening_result["shortlisted_candidates"])
        
        print(f"\n✅ Screening Complete!")
        print(f"   📊 Total: {total_candidates}")
        print(f"   🌟 Shortlisted: {shortlisted_count}")
        
        # Adjust threshold if needed
        if shortlisted_count == 0:
            print("⚠️ No candidates shortlisted. Lowering threshold...")
            screening_criteria.shortlist_threshold = 60.0
            screening_state["screening_criteria"] = screening_criteria.model_dump()
            screening_result = screening_workflow.invoke(screening_state)
            shortlisted_count = len(screening_result["shortlisted_candidates"])
            print(f"   🔄 New shortlist: {shortlisted_count}")
        
        if shortlisted_count == 0:
            print("❌ No candidates available for outreach")
            return None
        
        # Step 5: Setup Real Email Outreach
        print(f"\n{'='*60}")
        print("📧 STAGE 5: REAL EMAIL OUTREACH")
        print(f"{'='*60}")
        
        shortlisted_candidates = screening_result["shortlisted_candidates"]
        
        # Show candidates who will receive emails
        print(f"\n👥 Candidates who will receive REAL emails:")
        valid_candidates = []
        
        for i, candidate in enumerate(shortlisted_candidates, 1):
            name = candidate.get('name', 'Unknown')
            email = candidate.get('email', 'N/A')
            title = candidate.get('current_title', 'N/A')
            
            if email and email != 'N/A' and '@' in email:
                valid_candidates.append(candidate)
                print(f"   ✅ {i}. {name} ({email}) - {title}")
            else:
                print(f"   ❌ {i}. {name} (No valid email) - {title}")
        
        if not valid_candidates:
            print("❌ No candidates with valid email addresses")
            return None
        
        print(f"\n📧 {len(valid_candidates)} candidates will receive real emails")
        
        # Final email confirmation
        print(f"\n⚠️  FINAL CONFIRMATION")
        print(f"Real emails will be sent to {len(valid_candidates)} candidates")
        print(f"From: {os.getenv('SENDER_EMAIL')}")
        print(f"Subject: {job_requirements['job_title']} Opportunity at {job_requirements['company_name']}")
        
        final_confirm = input("\nSend real emails now? (YES/no): ").strip()
        if final_confirm.upper() != 'YES':
            print("❌ Email sending cancelled")
            return None
        
        # Step 6: Initialize Real Email Agent
        email_provider = EmailProvider(
            provider_name="real_pipeline_smtp",
            api_endpoint=f"{os.getenv('SMTP_SERVER')}:{os.getenv('SMTP_PORT')}",
            api_key=os.getenv('SENDER_PASSWORD'),
            sender_email=os.getenv('SENDER_EMAIL'),
            sender_name=os.getenv('SENDER_NAME', 'Recruiting Team')
        )
        
        agent = OutreachAgent(email_provider=email_provider, use_real_email=True)
        
        # Step 7: Prepare and Send Real Emails
        print(f"\n📝 Preparing personalized emails...")
        
        recruiter_data = {
            "name": os.getenv('SENDER_NAME', 'Sarah Johnson'),
            "title": "Senior Technical Recruiter",
            "email": os.getenv('SENDER_EMAIL'),
            "phone": "+1-555-0123",
            "company_name": job_requirements['company_name']
        }
        
        # Prepare emails
        emails_to_send = []
        template = agent.templates["professional_outreach_v1"]
        
        for candidate in valid_candidates:
            try:
                personalized_email = agent.personalize_email(
                    template=template,
                    candidate_data=candidate,
                    job_data=job_requirements,
                    recruiter_data=recruiter_data
                )
                emails_to_send.append(personalized_email)
                print(f"   ✅ Email prepared for {candidate['name']}")
            except Exception as e:
                print(f"   ❌ Error preparing email for {candidate['name']}: {e}")
        
        if not emails_to_send:
            print("❌ No emails prepared successfully")
            return None
        
        print(f"\n🚀 Sending {len(emails_to_send)} REAL emails...")
        print(f"⏱️ Stagger time: 30 seconds between emails")
        
        # Send emails with proper staggering
        start_time = datetime.now()
        results = agent.send_batch_emails(emails_to_send, stagger_seconds=30)
        end_time = datetime.now()
        
        # Step 8: Display Results
        print(f"\n🎉 REAL EMAIL CAMPAIGN COMPLETE!")
        print("=" * 60)
        
        print(f"📊 Email Campaign Results:")
        print(f"   📤 Emails Sent: {len(results['sent'])}/{results['total']}")
        print(f"   ✅ Success Rate: {results['success_rate']:.1f}%")
        print(f"   ⏱️ Total Time: {(end_time - start_time).total_seconds():.1f} seconds")
        
        if results['sent']:
            print(f"\n📧 REAL EMAILS SENT TO:")
            for email in emails_to_send:
                if email.email_id in results['sent']:
                    print(f"   ✅ {email.candidate_name} ({email.candidate_email})")
                    print(f"      📝 Subject: {email.subject}")
        
        if results['failed']:
            print(f"\n❌ Failed to send to {len(results['failed'])} candidates")
        
        # Generate metrics
        metrics = agent.generate_outreach_metrics(emails_to_send, "real_email_campaign")
        
        print(f"\n📈 Campaign Metrics:")
        print(f"   📬 Delivery Rate: {metrics.delivery_rate:.1f}%")
        print(f"   📊 Total Emails: {metrics.total_emails}")
        print(f"   📤 Successfully Sent: {metrics.emails_sent}")
        
        # Next steps
        print(f"\n🎯 Next Steps:")
        print(f"   1. 📧 Monitor email inboxes for responses")
        print(f"   2. 📞 Follow up with interested candidates")
        print(f"   3. 📅 Schedule interviews with respondents")
        print(f"   4. 🔄 Set up Stage 6: Response Management")
        
        print(f"\n✅ REAL EMAIL PIPELINE SUCCESSFUL!")
        print(f"🎉 {len(results['sent'])} candidates contacted via real email")
        
        return {
            "screening_result": screening_result,
            "emails_sent": len(results['sent']),
            "email_results": results,
            "campaign_metrics": metrics.model_dump(),
            "valid_candidates": len(valid_candidates),
            "success_rate": results['success_rate']
        }
        
    except Exception as e:
        print(f"❌ Real email pipeline failed: {e}")
        traceback.print_exc()
        return None

def run_quick_real_email_test():
    """Quick test with minimal real emails"""
    
    print("🧪 QUICK REAL EMAIL TEST")
    print("=" * 40)
    
    # Get test email
    test_email = input("Enter your email address for testing: ").strip()
    if not test_email:
        print("❌ No test email provided")
        return False
    
    confirm = input(f"Send real test email to {test_email}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Test cancelled")
        return False
    
    try:
        # Create test candidate
        test_candidate = {
            "source_id": "quick_test_001",
            "name": "Test Candidate",
            "email": test_email,
            "current_title": "AI Engineer",
            "experience_years": 5,
            "skills": ["Python", "Machine Learning", "AI"],
            "location": "Remote"
        }
        
        # Mock job requirements
        job_requirements = {
            "job_id": "quick_test_job",
            "job_title": "Senior AI Engineer",
            "job_description": "Quick test of real email functionality",
            "required_skills": ["Python", "AI"],
            "company_name": os.getenv('COMPANY_NAME', 'Test Company')
        }
        
        recruiter_data = {
            "name": os.getenv('SENDER_NAME', 'Test Recruiter'),
            "email": os.getenv('SENDER_EMAIL'),
            "company_name": job_requirements['company_name']
        }
        
        # Initialize real email agent
        email_provider = EmailProvider(
            provider_name="quick_test",
            api_endpoint=f"{os.getenv('SMTP_SERVER')}:{os.getenv('SMTP_PORT')}",
            api_key=os.getenv('SENDER_PASSWORD'),
            sender_email=os.getenv('SENDER_EMAIL'),
            sender_name=os.getenv('SENDER_NAME')
        )
        
        agent = OutreachAgent(email_provider=email_provider, use_real_email=True)
        
        # Prepare and send email
        template = agent.templates["professional_outreach_v1"]
        email = agent.personalize_email(template, test_candidate, job_requirements, recruiter_data)
        
        print(f"\n📤 Sending quick test email...")
        success = agent.send_email(email)
        
        if success:
            print(f"✅ Quick test email sent successfully!")
            print(f"📧 Check inbox: {test_email}")
            return True
        else:
            print(f"❌ Quick test email failed")
            return False
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    print("📧 REAL EMAIL RECRUITMENT PIPELINE")
    print("=" * 60)
    
    # Check for email configuration
    if not os.path.exists('.env'):
        print("❌ No email configuration found!")
        print("🔧 First run: python setup_real_emails.py")
        print("🧪 Then test: python test_real_emails.py")
        sys.exit(1)
    
    mode = input("\nSelect mode:\n1. Full Pipeline with Real Emails\n2. Quick Real Email Test\n\nEnter choice (1-2): ").strip()
    
    if mode == "1":
        print(f"\n🚀 Running full pipeline with REAL email sending...")
        result = run_real_email_pipeline()
        
        if result:
            print(f"\n🎉 SUCCESS! REAL EMAIL PIPELINE COMPLETE!")
            print(f"📧 {result['emails_sent']} real emails sent to candidates")
            print(f"📈 Success rate: {result['success_rate']:.1f}%")
            print(f"🎯 Check candidate email inboxes for delivered messages!")
        else:
            print(f"❌ Pipeline failed")
    
    elif mode == "2":
        print(f"\n🧪 Running quick real email test...")
        success = run_quick_real_email_test()
        
        if success:
            print(f"\n✅ Real email system working!")
            print(f"🚀 Ready for full pipeline deployment")
        else:
            print(f"❌ Email system needs configuration")
    
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print(f"\n🎯 RECRUITMENT AUTOMATION STATUS:")
    print(f"✅ Database Screening: Operational")
    print(f"✅ Real Email Outreach: Operational") 
    print(f"🔄 Response Management: Next Stage")
    print(f"🔄 Interview Coordination: Next Stage")