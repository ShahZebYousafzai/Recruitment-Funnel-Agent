import sqlite3
import json
from typing import Dict, Any, List
import logging

def debug_database_candidates(db_path: str = "candidates.db"):
    """Debug function to identify why candidates query returns empty results"""
    
    print("🔍 DEBUGGING DATABASE CANDIDATE RETRIEVAL")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check if table exists
        print("1️⃣ Checking if candidates table exists...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='candidates'
        """)
        table_exists = cursor.fetchone()
        if not table_exists:
            print("❌ Table 'candidates' does not exist!")
            return False
        print("✅ Table 'candidates' exists")
        
        # 2. Check total number of records
        print("\n2️⃣ Checking total records...")
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total records in candidates table: {total_count}")
        
        if total_count == 0:
            print("❌ No candidates in database!")
            return False
        
        # 3. Check available candidates
        print("\n3️⃣ Checking available candidates...")
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'available'")
        available_count = cursor.fetchone()[0]
        print(f"📊 Available candidates: {available_count}")
        
        if available_count == 0:
            print("❌ No candidates with status 'available'!")
            # Check what statuses exist
            cursor.execute("SELECT DISTINCT status, COUNT(*) FROM candidates GROUP BY status")
            statuses = cursor.fetchall()
            print("📋 Existing statuses:")
            for status, count in statuses:
                print(f"   • {status}: {count}")
            return False
        
        # 4. Sample a few candidates to check data structure
        print("\n4️⃣ Sampling candidate data structure...")
        cursor.execute("SELECT * FROM candidates WHERE status = 'available' LIMIT 3")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"📋 Table columns: {columns}")
        
        for i, row in enumerate(rows):
            candidate = dict(zip(columns, row))
            print(f"\n👤 Sample Candidate {i+1}:")
            print(f"   ID: {candidate.get('id')} (type: {type(candidate.get('id'))})")
            print(f"   Source ID: {candidate.get('source_id')} (type: {type(candidate.get('source_id'))})")
            print(f"   Name: {candidate.get('name')}")
            print(f"   Email: {candidate.get('email')}")
            print(f"   Status: {candidate.get('status')}")
            print(f"   Skills: {candidate.get('skills')} (type: {type(candidate.get('skills'))})")
            print(f"   Location: {candidate.get('location')}")
            print(f"   Experience: {candidate.get('experience_years')}")
        
        # 5. Test specific job requirements that might be failing
        print("\n5️⃣ Testing job requirement filters...")
        
        test_job_requirements = {
            'required_skills': ['Python', 'Machine Learning'],
            'location': 'San Francisco, CA',
            'experience_level': 'Senior',
            'allow_remote': True
        }
        
        print(f"🎯 Test job requirements: {test_job_requirements}")
        
        # Test each filter individually
        
        # A. Test status filter only
        print("\n   A. Testing status filter only...")
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'available'")
        status_count = cursor.fetchone()[0]
        print(f"      Status filter result: {status_count} candidates")
        
        # B. Test skills filter
        print("\n   B. Testing skills filter...")
        required_skills = test_job_requirements.get('required_skills', [])
        if required_skills:
            skill_conditions = []
            params = []
            for skill in required_skills:
                skill_conditions.append("skills LIKE ?")
                params.append(f"%{skill}%")
            
            skills_query = f"""
                SELECT COUNT(*) FROM candidates 
                WHERE status = 'available' AND ({' OR '.join(skill_conditions)})
            """
            cursor.execute(skills_query, params)
            skills_count = cursor.fetchone()[0]
            print(f"      Skills filter result: {skills_count} candidates")
            
            # Check what skills actually exist
            cursor.execute("SELECT DISTINCT skills FROM candidates WHERE status = 'available' LIMIT 5")
            sample_skills = cursor.fetchall()
            print(f"      Sample skills in database:")
            for (skills_json,) in sample_skills:
                try:
                    if skills_json:
                        skills = json.loads(skills_json)
                        print(f"         {skills}")
                except:
                    print(f"         Raw: {skills_json}")
        
        # C. Test location filter
        print("\n   C. Testing location filter...")
        location = test_job_requirements.get('location', '')
        if location and not test_job_requirements.get('allow_remote', True):
            cursor.execute("""
                SELECT COUNT(*) FROM candidates 
                WHERE status = 'available' AND location LIKE ?
            """, (f"%{location}%",))
            location_count = cursor.fetchone()[0]
            print(f"      Location filter result: {location_count} candidates")
            
            # Check what locations exist
            cursor.execute("SELECT DISTINCT location FROM candidates WHERE status = 'available' LIMIT 5")
            sample_locations = cursor.fetchall()
            print(f"      Sample locations in database:")
            for (location_val,) in sample_locations:
                print(f"         {location_val}")
        else:
            print(f"      Location filter skipped (remote allowed or no location specified)")
        
        # D. Test experience filter
        print("\n   D. Testing experience filter...")
        experience_level = test_job_requirements.get('experience_level', '')
        if experience_level:
            exp_range = get_experience_range(experience_level)
            if exp_range:
                cursor.execute("""
                    SELECT COUNT(*) FROM candidates 
                    WHERE status = 'available' AND experience_years BETWEEN ? AND ?
                """, exp_range)
                exp_count = cursor.fetchone()[0]
                print(f"      Experience filter result: {exp_count} candidates (range: {exp_range})")
                
                # Check experience distribution
                cursor.execute("""
                    SELECT experience_years, COUNT(*) FROM candidates 
                    WHERE status = 'available' 
                    GROUP BY experience_years 
                    ORDER BY experience_years
                """)
                exp_dist = cursor.fetchall()
                print(f"      Experience distribution:")
                for exp_years, count in exp_dist:
                    print(f"         {exp_years} years: {count} candidates")
        
        # 6. Test the complete combined query
        print("\n6️⃣ Testing complete combined query...")
        
        where_clauses = ["status = 'available'"]
        params = []
        
        # Add skills filter
        required_skills = test_job_requirements.get('required_skills', [])
        if required_skills:
            skill_conditions = []
            for skill in required_skills:
                skill_conditions.append("skills LIKE ?")
                params.append(f"%{skill}%")
            where_clauses.append(f"({' OR '.join(skill_conditions)})")
        
        # Add location filter (only if not remote-friendly)
        location = test_job_requirements.get('location', '')
        if location and not test_job_requirements.get('allow_remote', True):
            where_clauses.append("location LIKE ?")
            params.append(f"%{location}%")
        
        # Add experience filter
        experience_level = test_job_requirements.get('experience_level', '')
        if experience_level:
            exp_range = get_experience_range(experience_level)
            if exp_range:
                where_clauses.append("experience_years BETWEEN ? AND ?")
                params.extend(exp_range)
        
        final_query = f"""
            SELECT COUNT(*) FROM candidates 
            WHERE {' AND '.join(where_clauses)}
        """
        
        print(f"      Final query: {final_query}")
        print(f"      Parameters: {params}")
        
        cursor.execute(final_query, params)
        final_count = cursor.fetchone()[0]
        print(f"      Final result: {final_count} candidates")
        
        # 7. If still no results, try without strict filters
        if final_count == 0:
            print("\n7️⃣ Trying relaxed filters...")
            
            # Try with just status and one skill
            if required_skills:
                relaxed_query = """
                    SELECT COUNT(*) FROM candidates 
                    WHERE status = 'available' AND skills LIKE ?
                """
                cursor.execute(relaxed_query, (f"%{required_skills[0]}%",))
                relaxed_count = cursor.fetchone()[0]
                print(f"      Relaxed filter (just {required_skills[0]}): {relaxed_count} candidates")
        
        conn.close()
        
        print(f"\n✅ Database debugging completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database debugging failed: {e}")
        logging.error(f"Database debug error: {e}", exc_info=True)
        return False

def get_experience_range(experience_level: str) -> tuple:
    """Convert experience level to years range"""
    level_map = {
        "entry": (0, 2),
        "junior": (1, 3),
        "mid": (3, 7),
        "senior": (5, 12),
        "lead": (7, 15),
        "principal": (10, 20),
        "staff": (8, 20)
    }
    return level_map.get(experience_level.lower(), None)

def fix_candidate_status_if_needed(db_path: str = "candidates.db"):
    """Fix candidate status if they're not set to 'available'"""
    
    print("\n🔧 FIXING CANDIDATE STATUS...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current status distribution
        cursor.execute("SELECT status, COUNT(*) FROM candidates GROUP BY status")
        status_dist = cursor.fetchall()
        
        print("📊 Current status distribution:")
        for status, count in status_dist:
            print(f"   • {status}: {count}")
        
        # If no candidates are 'available', set them all to available
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'available'")
        available_count = cursor.fetchone()[0]
        
        if available_count == 0:
            print("\n🔄 No candidates marked as 'available'. Setting all to 'available'...")
            cursor.execute("UPDATE candidates SET status = 'available'")
            updated_count = cursor.rowcount
            conn.commit()
            print(f"✅ Updated {updated_count} candidates to 'available' status")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix candidate status: {e}")
        return False

if __name__ == "__main__":
    # Run the debugging
    print("🚀 Starting database debugging process...")
    
    # First, try to fix status issues
    fix_candidate_status_if_needed()
    
    # Then run full debugging
    success = debug_database_candidates()
    
    if success:
        print("\n🎉 Debugging completed! Check the output above to identify the issue.")
    else:
        print("\n❌ Debugging failed. Please check your database setup.")