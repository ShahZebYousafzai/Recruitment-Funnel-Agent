import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class CandidateDatabase:
    """Database integration for candidate retrieval and management"""
    
    def __init__(self, db_path: str = "candidates.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure the database and table exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if candidates table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='candidates'
            """)
            
            if not cursor.fetchone():
                print(f"⚠️ Database table 'candidates' not found at {self.db_path}")
                print(f"💡 Please run database_setup.py first to create and populate the database")
                return False
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def get_candidates_for_job(self, job_requirements: Dict[str, Any], 
                                max_candidates: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve candidates from database based on job requirements
        Maps database fields to expected screening format
        FIXED VERSION with better filtering logic
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Start with basic filtering - be more permissive initially
            print(f"🔍 Querying database for candidates...")
            print(f"   Job requirements: {job_requirements}")
            
            # Check if we have any available candidates at all
            cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'available'")
            available_count = cursor.fetchone()[0]
            
            if available_count == 0:
                print("⚠️ No candidates with 'available' status found")
                # Try with any status
                cursor.execute("SELECT COUNT(*) FROM candidates")
                total_count = cursor.fetchone()[0]
                print(f"   Total candidates in database: {total_count}")
                
                if total_count == 0:
                    print("❌ Database is empty!")
                    return []
                
                # Check what statuses exist
                cursor.execute("SELECT DISTINCT status, COUNT(*) FROM candidates GROUP BY status")
                statuses = cursor.fetchall()
                print("📋 Available statuses:")
                for status, count in statuses:
                    print(f"   • {status}: {count}")
                
                # Use all candidates regardless of status
                base_where = "1=1"  # Always true condition
                print("🔄 Using all candidates regardless of status...")
            else:
                base_where = "status = 'available'"
                print(f"   ✅ Found {available_count} available candidates")
            
            # Build dynamic query with more flexible filtering
            where_clauses = [base_where]
            params = []
            scoring_selects = []  # For relevance scoring
            
            # IMPROVED Skills filter - make it more flexible
            required_skills = job_requirements.get('required_skills', [])
            if required_skills:
                print(f"   🎯 Filtering by skills: {required_skills}")
                
                # Create individual skill conditions for OR logic
                skill_conditions = []
                skill_scores = []
                
                for i, skill in enumerate(required_skills):
                    skill_param = f"skill_{i}"
                    skill_conditions.append(f"skills LIKE :{skill_param}")
                    params.append((skill_param, f"%{skill}%"))
                    
                    # Add relevance scoring
                    skill_scores.append(f"CASE WHEN skills LIKE :{skill_param} THEN 1 ELSE 0 END")
                
                # Use OR logic for skills (candidate needs at least ONE skill)
                if skill_conditions:
                    where_clauses.append(f"({' OR '.join(skill_conditions)})")
                    # Add skill match score
                    scoring_selects.append(f"({' + '.join(skill_scores)}) as skill_matches")
            
            # IMPROVED Location filter - only apply if remote is not allowed
            location = job_requirements.get('location', '')
            allow_remote = job_requirements.get('allow_remote', True)
            
            if location and not allow_remote:
                print(f"   📍 Filtering by location: {location} (remote not allowed)")
                where_clauses.append("(location LIKE :location OR location LIKE '%remote%')")
                params.append(('location', f"%{location}%"))
            elif location:
                print(f"   📍 Location preference: {location} (remote allowed)")
                # Add location scoring but don't filter
                scoring_selects.append(f"CASE WHEN location LIKE :location_pref THEN 1 ELSE 0 END as location_match")
                params.append(('location_pref', f"%{location}%"))
            
            # IMPROVED Experience filter - be more flexible
            experience_level = job_requirements.get('experience_level', '')
            if experience_level:
                exp_range = self._get_experience_range(experience_level)
                if exp_range:
                    min_exp, max_exp = exp_range
                    print(f"   💼 Experience level: {experience_level} ({min_exp}-{max_exp} years)")
                    
                    # Instead of hard filtering, prefer candidates in range but include others
                    # Only hard filter if experience is way too low
                    if min_exp > 0:
                        # Allow candidates with at least 50% of minimum experience
                        flexible_min = max(0, min_exp // 2)
                        where_clauses.append("experience_years >= :min_exp")
                        params.append(('min_exp', flexible_min))
                    
                    # Add experience scoring
                    scoring_selects.append(f"""
                        CASE 
                            WHEN experience_years BETWEEN :exp_min AND :exp_max THEN 2
                            WHEN experience_years >= :exp_min THEN 1
                            ELSE 0 
                        END as exp_score
                    """)
                    params.extend([('exp_min', min_exp), ('exp_max', max_exp)])
            
            # Build the query with scoring
            base_select = """
                id, source_id, name, email, phone, location, current_title, 
                current_company, experience_years, skills, education, 
                certifications, raw_data, created_at, updated_at
            """
            
            if scoring_selects:
                select_clause = f"{base_select}, {', '.join(scoring_selects)}"
                order_clause = "ORDER BY " + ", ".join([s.split(" as ")[1] for s in scoring_selects]) + " DESC, experience_years DESC, created_at DESC"
            else:
                select_clause = base_select
                order_clause = "ORDER BY experience_years DESC, created_at DESC"
            
            # Build final query
            query = f"""
                SELECT {select_clause}
                FROM candidates 
                WHERE {' AND '.join(where_clauses)}
                {order_clause}
                LIMIT :max_candidates
            """
            params.append(('max_candidates', max_candidates))
            
            print(f"   📝 Generated query with {len(where_clauses)} conditions")
            print(f"   🔢 Query parameters: {len(params)} parameters")
            
            # Convert named parameters to positional for sqlite3
            param_dict = dict(params)
            
            # Debug: print the actual query
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                print(f"   🐛 SQL Query: {query}")
                print(f"   🐛 Parameters: {param_dict}")
            
            cursor.execute(query, param_dict)
            rows = cursor.fetchall()
            
            print(f"   📊 Raw query returned {len(rows)} rows")
            
            if len(rows) == 0:
                print("⚠️ No candidates found with current filters")
                # Try a simpler query
                simple_query = f"""
                    SELECT {base_select}
                    FROM candidates 
                    WHERE {base_where}
                    ORDER BY experience_years DESC, created_at DESC
                    LIMIT ?
                """
                cursor.execute(simple_query, (max_candidates,))
                rows = cursor.fetchall()
                print(f"   🔄 Fallback query returned {len(rows)} candidates")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to candidate format expected by screening
            candidates = []
            for row in rows:
                candidate_dict = dict(zip(columns, row))
                
                try:
                    # Parse JSON fields safely
                    for json_field in ['skills', 'education', 'certifications']:
                        if json_field in candidate_dict:
                            value = candidate_dict[json_field]
                            if value:
                                try:
                                    candidate_dict[json_field] = json.loads(value) if isinstance(value, str) else value
                                except (json.JSONDecodeError, TypeError):
                                    candidate_dict[json_field] = []
                            else:
                                candidate_dict[json_field] = []
                    
                    # Parse raw_data
                    if 'raw_data' in candidate_dict:
                        value = candidate_dict['raw_data']
                        if value:
                            try:
                                candidate_dict['raw_data'] = json.loads(value) if isinstance(value, str) else value
                            except (json.JSONDecodeError, TypeError):
                                candidate_dict['raw_data'] = {}
                        else:
                            candidate_dict['raw_data'] = {}
                    
                    # Map database fields to screening format
                    screening_candidate = {
                        'id': str(candidate_dict['id']),  # Convert to string
                        'source_id': str(candidate_dict['source_id']),  # Convert to string
                        'name': candidate_dict.get('name'),
                        'email': candidate_dict.get('email'),
                        'phone': candidate_dict.get('phone'),
                        'location': candidate_dict.get('location'),
                        'current_title': candidate_dict.get('current_title'),
                        'current_company': candidate_dict.get('current_company'),
                        'experience_years': candidate_dict.get('experience_years', 0),
                        'skills': candidate_dict.get('skills', []),
                        'education': candidate_dict.get('education', []),
                        'certifications': candidate_dict.get('certifications', []),
                        'source': 'database',  # Mark as database source
                        'raw_data': candidate_dict.get('raw_data', {}),
                        'created_at': candidate_dict.get('created_at'),
                        'updated_at': candidate_dict.get('updated_at')
                    }
                    
                    candidates.append(screening_candidate)
                    
                except Exception as parse_error:
                    print(f"   ⚠️ Error parsing candidate {candidate_dict.get('name', 'Unknown')}: {parse_error}")
                    continue
            
            conn.close()
            
            print(f"   ✅ Successfully processed {len(candidates)} candidates")
            
            # Show sample of found candidates
            if candidates:
                print(f"   📋 Sample candidates:")
                for i, candidate in enumerate(candidates[:3]):
                    skills_preview = ', '.join(candidate['skills'][:3]) + ('...' if len(candidate['skills']) > 3 else '')
                    print(f"      {i+1}. {candidate['name']} - {candidate['current_title']} - {candidate['experience_years']}y - [{skills_preview}]")
            
            return candidates
            
        except Exception as e:
            logging.error(f"Database query error: {e}", exc_info=True)
            print(f"❌ Error querying database: {e}")
            print(f"   💡 Try running the debug script to identify the issue")
            return []
    
    def _get_experience_range(self, experience_level: str) -> Optional[tuple]:
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
    
    def get_all_candidates(self, max_candidates: int = 100) -> List[Dict[str, Any]]:
        """Get all available candidates from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT id, source_id, name, email, phone, location, current_title, 
                        current_company, experience_years, skills, education, 
                        certifications, raw_data, created_at, updated_at
                FROM candidates 
                WHERE status = 'available'
                ORDER BY experience_years DESC, created_at DESC
                LIMIT ?
            """
            
            cursor.execute(query, (max_candidates,))
            rows = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            candidates = []
            
            for row in rows:
                candidate_dict = dict(zip(columns, row))
                
                # Parse JSON fields safely
                for json_field in ['skills', 'education', 'certifications', 'raw_data']:
                    try:
                        if candidate_dict[json_field]:
                            candidate_dict[json_field] = json.loads(candidate_dict[json_field])
                        else:
                            candidate_dict[json_field] = [] if json_field != 'raw_data' else {}
                    except (json.JSONDecodeError, TypeError):
                        candidate_dict[json_field] = [] if json_field != 'raw_data' else {}
                
                # Format for screening
                screening_candidate = {
                    'id': str(candidate_dict['id']),  # Convert to string
                    'source_id': str(candidate_dict['source_id']),  # Convert to string
                    'name': candidate_dict['name'],
                    'email': candidate_dict['email'],
                    'phone': candidate_dict['phone'],
                    'location': candidate_dict['location'],
                    'current_title': candidate_dict['current_title'],
                    'current_company': candidate_dict['current_company'],
                    'experience_years': candidate_dict['experience_years'],
                    'skills': candidate_dict['skills'],
                    'education': candidate_dict['education'],
                    'certifications': candidate_dict['certifications'],
                    'source': 'database',
                    'raw_data': candidate_dict['raw_data'],
                    'created_at': candidate_dict['created_at'],
                    'updated_at': candidate_dict['updated_at']
                }
                
                candidates.append(screening_candidate)
            
            conn.close()
            return candidates
            
        except Exception as e:
            logging.error(f"Error fetching all candidates: {e}", exc_info=True)
            print(f"❌ Error fetching candidates: {e}")
            return []
    
    def update_candidate_status(self, candidate_id: str, new_status: str, notes: str = None):
        """Update candidate status after screening"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update status and timestamp
            update_query = """
                UPDATE candidates 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE source_id = ? OR id = ?
            """
            
            cursor.execute(update_query, (new_status, candidate_id, candidate_id))
            
            # Add notes to raw_data if provided
            if notes:
                cursor.execute("SELECT raw_data FROM candidates WHERE source_id = ? OR id = ?", 
                                (candidate_id, candidate_id))
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        raw_data = json.loads(row[0])
                    except:
                        raw_data = {}
                else:
                    raw_data = {}
                
                raw_data['screening_notes'] = notes
                raw_data['last_screening'] = datetime.now().isoformat()
                
                cursor.execute("""
                    UPDATE candidates 
                    SET raw_data = ? 
                    WHERE source_id = ? OR id = ?
                """, (json.dumps(raw_data), candidate_id, candidate_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error updating candidate status: {e}", exc_info=True)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total candidates
            cursor.execute("SELECT COUNT(*) FROM candidates")
            stats['total_candidates'] = cursor.fetchone()[0]
            
            # Available candidates
            cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'available'")
            stats['available_candidates'] = cursor.fetchone()[0]
            
            # Experience distribution
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN experience_years <= 2 THEN 'Entry (0-2 years)'
                        WHEN experience_years <= 5 THEN 'Mid (3-5 years)'
                        WHEN experience_years <= 10 THEN 'Senior (6-10 years)'
                        ELSE 'Lead+ (10+ years)'
                    END as exp_level,
                    COUNT(*) as count
                FROM candidates 
                WHERE status = 'available'
                GROUP BY exp_level
            """)
            stats['experience_distribution'] = dict(cursor.fetchall())
            
            # Top locations
            cursor.execute("""
                SELECT location, COUNT(*) as count 
                FROM candidates 
                WHERE status = 'available' AND location IS NOT NULL
                GROUP BY location 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats['top_locations'] = dict(cursor.fetchall())
            
            conn.close()
            return stats
            
        except Exception as e:
            logging.error(f"Error getting database stats: {e}", exc_info=True)
            return {}

def test_database_connection():
    """Test database connection and data retrieval"""
    print("🧪 Testing Database Connection...")
    
    db = CandidateDatabase()
    
    # Test basic connection
    if not db.ensure_database_exists():
        return False
    
    # Get database stats
    stats = db.get_database_stats()
    if stats:
        print(f"✅ Database connection successful!")
        print(f"   📊 Total candidates: {stats.get('total_candidates', 0)}")
        print(f"   ✅ Available candidates: {stats.get('available_candidates', 0)}")
        
        exp_dist = stats.get('experience_distribution', {})
        if exp_dist:
            print(f"   📈 Experience distribution:")
            for level, count in exp_dist.items():
                print(f"      {level}: {count}")
        
        locations = stats.get('top_locations', {})
        if locations:
            print(f"   📍 Top locations:")
            for location, count in list(locations.items())[:3]:
                print(f"      {location}: {count}")
        
        return True
    else:
        print("❌ Database connection failed")
        return False

if __name__ == "__main__":
    # Test the database integration
    success = test_database_connection()
    
    if success:
        print(f"\n🔍 Testing candidate retrieval...")
        
        db = CandidateDatabase()
        
        # Test getting candidates for a specific job
        job_requirements = {
            'required_skills': ['Python', 'Machine Learning'],
            'location': 'San Francisco',
            'experience_level': 'senior',
            'allow_remote': True
        }
        
        candidates = db.get_candidates_for_job(job_requirements, max_candidates=5)
        
        if candidates:
            print(f"✅ Found {len(candidates)} matching candidates:")
            for candidate in candidates:
                print(f"   👤 {candidate['name']} - {candidate['current_title']} - {candidate['experience_years']} years")
                print(f"      Skills: {', '.join(candidate['skills'][:3])}...")
        else:
            print("⚠️ No candidates found matching criteria")
    
    print(f"\n🎯 Database integration ready for screening!")