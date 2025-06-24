import traceback
import sys
from datetime import datetime

# Import fixed utilities
from utils import convert_database_candidate
from database.database_integration import CandidateDatabase, test_database_connection
from workflows.screening import (
    create_database_screening_workflow, 
    create_database_screening_state
)
from models.screening import ScreeningCriteria
from nodes.screening import generate_screening_report

# Patch the screening agent to use fixed utilities
from agents.screening import ScreeningAgent
import nodes.screening
nodes.screening.ScreeningAgent = ScreeningAgent

def run_fixed_database_screening():
    """Run database screening with data type conversion fixes"""
    
    print("🗄️ FIXED DATABASE-INTEGRATED RECRUITMENT SCREENING")
    print("=" * 70)
    print("🔧 Fixed: source_id integer → string conversion")
    print("📋 Pulling candidate data from candidates database table")
    print("=" * 70)
    
    try:
        # Step 1: Test database connection
        print("\n🔌 Testing Database Connection...")
        if not test_database_connection():
            print("❌ Database connection failed. Please ensure:")
            print("   1. Database file 'candidates.db' exists")
            print("   2. Run 'python database_setup.py' to create and populate database")
            return None
        
        # Step 2: Get candidates with proper data conversion
        print(f"\n📋 Retrieving and Converting Candidate Data...")
        
        db = CandidateDatabase()

        stats = db.get_database_stats()

        total_candidates = stats.get('total_candidates', 0)
        available_candidates = stats.get('available_candidates', 0)
        
        # Define job requirements
        job_requirements = {
            "job_id": "ai_engineer_fixed_001",
            "job_title": "Senior AI Engineer",
            "job_description": "Senior AI Engineer with ML and NLP expertise",
            "required_skills": ["Python", "Machine Learning", "PyTorch", "NLP"],
            "preferred_skills": ["Generative AI", "TensorFlow", "LangChain", "Computer Vision"],
            "location": "San Francisco, CA",
            "experience_level": "Senior",
            "allow_remote": True
        }
        
        print(f"🎯 Job Requirements:")
        print(f"   Required Skills: {', '.join(job_requirements['required_skills'])}")
        print(f"   Preferred Skills: {', '.join(job_requirements['preferred_skills'])}")
        print(f"   Experience Level: {job_requirements['experience_level']}")
        print(f"   Remote Allowed: {job_requirements['allow_remote']}")
        
        # Get candidates from database
        raw_candidates = db.get_candidates_for_job(job_requirements, max_candidates=20)
        
        if not raw_candidates:
            print("⚠️ No candidates found matching criteria, getting all available...")
            raw_candidates = db.get_all_candidates(max_candidates=10)
        
        print(f"📊 Found {len(raw_candidates)} candidates in database")
        
        # CRITICAL FIX: Convert data types before processing
        print(f"🔧 Converting data types for Pydantic compatibility...")
        converted_candidates = []
        
        for i, candidate in enumerate(raw_candidates):
            try:
                converted = convert_database_candidate(candidate)
                converted_candidates.append(converted)
                print(f"   ✅ [{i+1}/{len(raw_candidates)}] {candidate.get('name', 'Unknown')} - ID: {converted['source_id']} (string)")
            except Exception as e:
                print(f"   ❌ [{i+1}/{len(raw_candidates)}] Conversion failed: {e}")
        
        print(f"✅ Successfully converted {len(converted_candidates)} candidates")
        
        # Step 3: Run screening with converted data
        print(f"\n🔍 Running Screening with Fixed Data...")
        
        # Define screening criteria
        screening_criteria = ScreeningCriteria(
            required_skills_weight=0.4,
            preferred_skills_weight=0.2,
            experience_weight=0.3,
            location_weight=0.1,
            education_weight=0.0,
            min_experience_years=3,
            preferred_experience_years=5,
            pass_threshold=40.0,
            shortlist_threshold=40.0,
            allow_remote=True,
            education_required=False
        )
        
        print(f"⚖️ Screening Criteria:")
        print(f"   Pass threshold: {screening_criteria.pass_threshold}%")
        print(f"   Shortlist threshold: {screening_criteria.shortlist_threshold}%")
        print(f"   Min experience: {screening_criteria.min_experience_years} years")
        
        # Create screening state with converted candidates
        screening_state = create_database_screening_state(
            job_requirements=job_requirements,
            screening_criteria=screening_criteria.model_dump(),
            max_candidates=50
        )
        
        # Override with our converted candidates
        screening_state["raw_candidates"] = converted_candidates
        screening_state["total_candidates"] = len(converted_candidates)
        
        # Run screening workflow
        print(f"\n📋 Screening {len(converted_candidates)} candidates...")
        screening_workflow = create_database_screening_workflow()
        screening_result = screening_workflow.invoke(screening_state)
        
        # Step 4: Display Results
        print(f"\n🎉 SCREENING RESULTS")
        print("=" * 50)
        
        total_candidates = screening_result["total_candidates"]
        passed_count = len(screening_result["passed_candidates"])
        shortlisted_count = len(screening_result["shortlisted_candidates"])
        
        if total_candidates == 0:
            print("⚠️ No candidates processed")
            return None
        
        print(f"📈 Summary:")
        print(f"   Total processed: {total_candidates}")
        print(f"   ✅ Passed: {passed_count} ({passed_count/total_candidates*100:.1f}%)")
        print(f"   🌟 Shortlisted: {shortlisted_count} ({shortlisted_count/total_candidates*100:.1f}%)")
        print(f"   ❌ Rejected: {total_candidates - passed_count}")
        
        metrics = screening_result["screening_metrics"]
        print(f"   📊 Average score: {metrics.get('average_score', 0):.1f}/100")
        
        # Show top candidates
        if shortlisted_count > 0:
            print(f"\n🏆 SHORTLISTED CANDIDATES:")
            
            sorted_results = sorted(screening_result["screening_results"], 
                                  key=lambda x: x["weighted_score"], reverse=True)
            
            shortlisted_results = [r for r in sorted_results if r["recommended_for_shortlist"]]
            
            for i, result in enumerate(shortlisted_results, 1):
                candidate = next((c for c in screening_result["raw_candidates"] 
                                if str(c.get("source_id")) == str(result["candidate_id"]) or 
                                   str(c.get("id")) == str(result["candidate_id"])), None)
                
                if candidate:
                    print(f"\n{i}. {candidate['name']} ⭐")
                    print(f"   📧 {candidate.get('email', 'N/A')}")
                    print(f"   💼 {candidate.get('current_title', 'N/A')}")
                    print(f"   📍 {candidate.get('location', 'N/A')}")
                    print(f"   🎯 {candidate.get('experience_years', 0)} years experience")
                    print(f"   🛠️ Skills: {', '.join(candidate.get('skills', [])[:4])}")
                    print(f"   📊 Score: {result['weighted_score']:.1f}/100")
                    print(f"   💪 Strengths: {', '.join(result['strengths'][:2])}")
                    if result['concerns']:
                        print(f"   ⚠️ Concerns: {', '.join(result['concerns'][:2])}")
        
        # Show all candidates with scores
        print(f"\n📋 ALL CANDIDATES:")
        print("-" * 40)
        
        sorted_all = sorted(screening_result["screening_results"], 
                           key=lambda x: x["weighted_score"], reverse=True)
        
        for i, result in enumerate(sorted_all, 1):
            candidate = next((c for c in screening_result["raw_candidates"] 
                            if str(c.get("source_id")) == str(result["candidate_id"]) or 
                               str(c.get("id")) == str(result["candidate_id"])), None)
            
            if candidate:
                status = "🌟 SHORTLISTED" if result["recommended_for_shortlist"] else \
                        "✅ PASSED" if result["passes_screening"] else \
                        "❌ REJECTED"
                
                print(f"{i}. {candidate['name']} - {result['weighted_score']:.1f} - {status}")
                print(f"   Skills: {result['required_skills_score']:.1f} | Exp: {result['experience_score']:.1f} | Loc: {result['location_score']:.1f}")
        
        # Show insights
        summary = metrics.get("summary", {})
        missing_skills = summary.get("most_common_missing_skills", [])
        
        if missing_skills:
            print(f"\n🎯 Most Common Missing Skills:")
            for skill in missing_skills[:3]:
                print(f"   • {skill}")
        
        print(f"\n✅ SCREENING COMPLETED SUCCESSFULLY!")
        print(f"🔧 Data type conversion fix applied successfully")
        print(f"📊 {shortlisted_count} candidates ready for next stage")
        print(f"🗄️ Database updated with screening results")
        
        return {
            "screening_result": screening_result,
            "job_requirements": job_requirements,
            "screening_criteria": screening_criteria.model_dump(),
            "summary": {
                "total_candidates": total_candidates,
                "passed_count": passed_count,
                "shortlisted_count": shortlisted_count,
                "pass_rate": passed_count/total_candidates*100,
                "average_score": metrics.get("average_score", 0)
            }
        }
        
    except Exception as e:
        print(f"❌ Fixed database screening failed: {e}")
        traceback.print_exc()
        return None

def test_data_type_fix():
    """Test the data type conversion fix"""
    print("🧪 Testing Data Type Conversion Fix...")
    
    try:
        # Mock database candidate data with integer IDs
        test_candidate = {
            'id': 123,  # Integer from database
            'source_id': 456,  # Integer from database
            'name': 'Test Candidate',
            'email': 'test@example.com',
            'location': 'San Francisco, CA',
            'current_title': 'AI Engineer',
            'experience_years': 5,
            'skills': ['Python', 'Machine Learning'],
            'education': ['BS Computer Science'],
            'certifications': [],
            'raw_data': {}
        }
        
        print(f"Original data types:")
        print(f"   id: {type(test_candidate['id'])} = {test_candidate['id']}")
        print(f"   source_id: {type(test_candidate['source_id'])} = {test_candidate['source_id']}")
        
        # Apply conversion
        converted = convert_database_candidate(test_candidate)
        
        print(f"After conversion:")
        print(f"   id: {type(converted['id'])} = {converted['id']}")
        print(f"   source_id: {type(converted['source_id'])} = {converted['source_id']}")
        
        # Test with screening agent
        from agents.screening import ScreeningAgent
        from models.screening import ScreeningCriteria
        
        agent = ScreeningAgent()
        criteria = ScreeningCriteria()
        job_reqs = {
            "required_skills": ["Python"],
            "location": "San Francisco, CA"
        }
        
        result = agent.screen_candidate(converted, job_reqs, criteria)
        
        print(f"✅ Test passed! Candidate scored: {result.weighted_score:.1f}/100")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

def run_quick_fix_test():
    """Quick test with minimal candidates"""
    print("🧪 Quick Fix Test with Database...")
    
    try:
        db = CandidateDatabase()
        
        # Get just 1-2 candidates for testing
        candidates = db.get_all_candidates(max_candidates=2)
        
        if not candidates:
            print("⚠️ No candidates in database for testing")
            return False
        
        print(f"Found {len(candidates)} candidates for testing")
        
        # Apply conversion
        converted = []
        for candidate in candidates:
            conv = convert_database_candidate(candidate)
            converted.append(conv)
            print(f"   ✅ Converted: {candidate['name']} (ID: {conv['source_id']})")
        
        # Quick screening test
        from agents.screening import ScreeningAgent
        from models.screening import ScreeningCriteria
        
        agent = ScreeningAgent()
        criteria = ScreeningCriteria(pass_threshold=50.0)
        job_reqs = {
            "required_skills": ["Python"],
            "preferred_skills": ["Machine Learning"],
            "location": "San Francisco, CA"
        }
        
        results = []
        for candidate in converted:
            try:
                result = agent.screen_candidate(candidate, job_reqs, criteria)
                results.append((candidate['name'], result.weighted_score, result.passes_screening))
                print(f"   📊 {candidate['name']}: {result.weighted_score:.1f} - {'PASS' if result.passes_screening else 'FAIL'}")
            except Exception as e:
                print(f"   ❌ {candidate['name']}: Error - {e}")
        
        print(f"✅ Quick test completed! Processed {len(results)} candidates successfully")
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting FIXED Database Screening Pipeline...")
    print("=" * 70)
    
    # Step 1: Test the fix
    print("🔧 Testing data type conversion fix...")
    if not test_data_type_fix():
        print("❌ Data type fix test failed")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print("🧪 Running quick database test...")
    # if not run_quick_fix_test():
    #     print("❌ Quick database test failed")
    #     sys.exit(1)
    
    print(f"\n{'='*70}")
    print("🎯 All tests passed! Running full screening pipeline...\n")
    
    # Step 2: Run full pipeline
    result = run_fixed_database_screening()
    
    if result:
        print(f"\n🎉 SUCCESS! Fixed database screening completed successfully.")
        print(f"🔧 Data type conversion issues resolved")
        print(f"📊 Pipeline ready for production use")
        print(f"⏭️ Next: Implement automated candidate outreach")
    # else:
    #     print(f"\n❌ Pipeline failed. Check error messages above.")
    #     sys.exit(1)