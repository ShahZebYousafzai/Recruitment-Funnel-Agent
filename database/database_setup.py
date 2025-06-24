import sqlite3
import json
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import os

class CandidateDatabase:
    """Database manager for candidate storage and retrieval"""
    
    def __init__(self, db_path: str = "candidates.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with candidate table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                location TEXT,
                current_title TEXT,
                current_company TEXT,
                experience_years INTEGER,
                skills TEXT,  -- JSON array of skills
                education TEXT,  -- JSON array of education
                certifications TEXT,  -- JSON array of certifications
                linkedin_url TEXT,
                resume_url TEXT,
                status TEXT DEFAULT 'available',
                raw_data TEXT,  -- JSON blob for additional data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on commonly queried fields
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills ON candidates(skills)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON candidates(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experience ON candidates(experience_years)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON candidates(status)")
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def populate_sample_data(self):
        """Populate database with sample candidate data"""
        sample_candidates = self._generate_sample_candidates()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for candidate in sample_candidates:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO candidates 
                    (source_id, name, email, phone, location, current_title, current_company,
                     experience_years, skills, education, certifications, linkedin_url, 
                     resume_url, status, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candidate['source_id'],
                    candidate['name'],
                    candidate['email'],
                    candidate['phone'],
                    candidate['location'],
                    candidate['current_title'],
                    candidate['current_company'],
                    candidate['experience_years'],
                    json.dumps(candidate['skills']),
                    json.dumps(candidate['education']),
                    json.dumps(candidate['certifications']),
                    candidate['linkedin_url'],
                    candidate['resume_url'],
                    candidate['status'],
                    json.dumps(candidate['raw_data'])
                ))
            except sqlite3.IntegrityError as e:
                print(f"⚠️ Skipping duplicate candidate: {candidate['email']} - {e}")
        
        conn.commit()
        count = cursor.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        conn.close()
        
        print(f"✅ Database populated with {count} candidates")
        return count
    
    def search_candidates(self, skills: List[str] = None, location: str = None, 
                         experience_level: str = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search candidates based on criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic query
        where_clauses = ["status = 'available'"]
        params = []
        
        if skills:
            # Search for any of the required skills
            skill_conditions = []
            for skill in skills:
                skill_conditions.append("skills LIKE ?")
                params.append(f"%{skill}%")
            where_clauses.append(f"({' OR '.join(skill_conditions)})")
        
        if location:
            where_clauses.append("location LIKE ?")
            params.append(f"%{location}%")
        
        if experience_level:
            exp_range = self._get_experience_range(experience_level)
            if exp_range:
                where_clauses.append("experience_years BETWEEN ? AND ?")
                params.extend(exp_range)
        
        query = f"""
            SELECT * FROM candidates 
            WHERE {' AND '.join(where_clauses)}
            ORDER BY experience_years DESC, created_at DESC
            LIMIT ?
        """
        params.append(max_results)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        columns = [desc[0] for desc in cursor.description]
        candidates = []
        
        for row in rows:
            candidate = dict(zip(columns, row))
            # Parse JSON fields
            candidate['skills'] = json.loads(candidate['skills']) if candidate['skills'] else []
            candidate['education'] = json.loads(candidate['education']) if candidate['education'] else []
            candidate['certifications'] = json.loads(candidate['certifications']) if candidate['certifications'] else []
            candidate['raw_data'] = json.loads(candidate['raw_data']) if candidate['raw_data'] else {}
            candidates.append(candidate)
        
        conn.close()
        return candidates
    
    def _get_experience_range(self, experience_level: str) -> tuple:
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
    
    def _generate_sample_candidates(self) -> List[Dict[str, Any]]:
        """Generate realistic sample candidate data"""
        
        # Common tech skills
        tech_skills = [
            "Python", "Machine Learning", "PyTorch", "TensorFlow", "NLP", "Computer Vision",
            "JavaScript", "React", "Node.js", "TypeScript", "Vue.js", "Angular",
            "Java", "Spring Boot", "Kafka", "Microservices", "REST API",
            "Go", "Kubernetes", "Docker", "AWS", "Azure", "GCP",
            "SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "DevOps", "CI/CD", "Jenkins", "GitHub Actions", "Terraform",
            "Data Science", "Pandas", "Scikit-learn", "Apache Spark",
            "Generative AI", "LangChain", "LangGraph", "OpenAI", "Transformers",
            "System Design", "Distributed Systems", "Blockchain", "Solidity"
        ]
        
        # Job titles by seniority
        titles_by_level = {
            "junior": ["Junior Software Engineer", "Software Developer I", "Associate Developer", "Junior AI Engineer"],
            "mid": ["Software Engineer", "Full Stack Developer", "AI Engineer", "Data Scientist", "Backend Developer", "Frontend Developer"],
            "senior": ["Senior Software Engineer", "Senior AI Engineer", "Senior Data Scientist", "Tech Lead", "Senior Full Stack Developer"],
            "lead": ["Lead Engineer", "Engineering Manager", "Principal Engineer", "AI Research Lead", "Data Science Manager"],
            "principal": ["Principal Engineer", "Staff Engineer", "Senior Staff Engineer", "Principal AI Scientist"]
        }
        
        # Companies
        companies = [
            "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber", "Airbnb",
            "Stripe", "Shopify", "Spotify", "Adobe", "Salesforce", "Oracle", "IBM",
            "NVIDIA", "OpenAI", "Anthropic", "Hugging Face", "Databricks", "Snowflake",
            "StartupCorp", "TechFlow Inc", "AI Innovations", "DataDriven Co", "CodeCraft"
        ]
        
        # Locations
        locations = [
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA",
            "Los Angeles, CA", "Chicago, IL", "Denver, CO", "Atlanta, GA", "Portland, OR",
            "Remote, USA", "London, UK", "Toronto, Canada", "Berlin, Germany", "Amsterdam, Netherlands"
        ]
        
        # Education
        universities = [
            "Stanford University", "MIT", "UC Berkeley", "Carnegie Mellon", "Harvard",
            "Princeton", "University of Washington", "Georgia Tech", "UT Austin",
            "University of Illinois", "Caltech", "Columbia", "NYU", "UCLA"
        ]
        
        degrees = [
            "BS Computer Science", "MS Computer Science", "PhD Computer Science",
            "BS Electrical Engineering", "MS Data Science", "BS Mathematics",
            "MS Artificial Intelligence", "PhD Machine Learning", "BS Software Engineering"
        ]
        
        candidates = []
        
        for i in range(100):  # Generate 100 sample candidates
            # Determine experience level
            exp_years = random.randint(0, 15)
            if exp_years <= 2:
                level = "junior"
            elif exp_years <= 4:
                level = "mid"
            elif exp_years <= 8:
                level = "senior"
            elif exp_years <= 12:
                level = "lead"
            else:
                level = "principal"
            
            # Generate candidate
            first_names = ["Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Jamie", "Quinn", "Sage"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            name = f"{first_name} {last_name}"
            
            # Select skills (3-8 skills per candidate)
            candidate_skills = random.sample(tech_skills, random.randint(3, 8))
            
            # Add level-appropriate skills
            if level in ["senior", "lead", "principal"]:
                candidate_skills.extend(random.sample(["System Design", "Architecture", "Mentoring", "Leadership"], 2))
            
            candidate = {
                "source_id": f"db_{i:03d}",
                "name": name,
                "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
                "phone": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "location": random.choice(locations),
                "current_title": random.choice(titles_by_level[level]),
                "current_company": random.choice(companies),
                "experience_years": exp_years,
                "skills": candidate_skills,
                "education": [f"{random.choice(degrees)} - {random.choice(universities)}"],
                "certifications": random.sample(["AWS Certified", "Google Cloud Certified", "Azure Certified", "Kubernetes Certified"], random.randint(0, 2)),
                "linkedin_url": f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
                "resume_url": f"https://storage.company.com/resumes/{first_name.lower()}_{last_name.lower()}_resume.pdf",
                "status": "available",
                "raw_data": {
                    "preferred_salary": random.randint(80000, 300000),
                    "willing_to_relocate": random.choice([True, False]),
                    "remote_preference": random.choice(["remote", "hybrid", "office"]),
                    "notice_period": random.choice(["immediate", "2 weeks", "1 month"]),
                    "last_active": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                }
            }
            
            candidates.append(candidate)
        
        return candidates
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total candidates
        stats['total_candidates'] = cursor.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        
        # By experience level
        stats['by_experience'] = {}
        for level, (min_exp, max_exp) in [("Entry", (0, 2)), ("Mid", (3, 7)), ("Senior", (5, 12)), ("Lead+", (8, 20))]:
            count = cursor.execute("SELECT COUNT(*) FROM candidates WHERE experience_years BETWEEN ? AND ?", (min_exp, max_exp)).fetchone()[0]
            stats['by_experience'][level] = count
        
        # Top locations
        cursor.execute("SELECT location, COUNT(*) as count FROM candidates GROUP BY location ORDER BY count DESC LIMIT 5")
        stats['top_locations'] = dict(cursor.fetchall())
        
        # Top skills (approximate, since skills are stored as JSON)
        cursor.execute("SELECT skills FROM candidates")
        all_skills = []
        for (skills_json,) in cursor.fetchall():
            if skills_json:
                skills = json.loads(skills_json)
                all_skills.extend(skills)
        
        from collections import Counter
        skill_counts = Counter(all_skills)
        stats['top_skills'] = dict(skill_counts.most_common(10))
        
        conn.close()
        return stats

def setup_database():
    """Main function to setup and populate the database"""
    print("🗄️ Setting up Candidate Database...")
    print("=" * 50)
    
    # Create database manager
    db = CandidateDatabase()
    
    # Populate with sample data
    candidate_count = db.populate_sample_data()
    
    # Display statistics
    stats = db.get_stats()
    
    print(f"\n📊 Database Statistics:")
    print(f"Total Candidates: {stats['total_candidates']}")
    print(f"\nBy Experience Level:")
    for level, count in stats['by_experience'].items():
        print(f"  {level}: {count}")
    
    print(f"\nTop Locations:")
    for location, count in stats['top_locations'].items():
        print(f"  {location}: {count}")
    
    print(f"\nTop Skills:")
    for skill, count in list(stats['top_skills'].items())[:5]:
        print(f"  {skill}: {count}")
    
    print(f"\n✅ Database setup complete!")
    print(f"📁 Database file: {db.db_path}")
    
    return db

def test_database_search():
    """Test database search functionality"""
    print(f"\n🧪 Testing Database Search...")
    
    db = CandidateDatabase()
    
    # Test search by skills
    print(f"\n🔍 Searching for Python + Machine Learning candidates:")
    results = db.search_candidates(skills=["Python", "Machine Learning"], max_results=5)
    for candidate in results:
        print(f"  {candidate['name']} - {candidate['current_title']} - {candidate['experience_years']} years")
    
    # Test search by location
    print(f"\n🔍 Searching for candidates in San Francisco:")
    results = db.search_candidates(location="San Francisco", max_results=3)
    for candidate in results:
        print(f"  {candidate['name']} - {candidate['current_title']} - {candidate['location']}")
    
    # Test search by experience level
    print(f"\n🔍 Searching for senior-level candidates:")
    results = db.search_candidates(experience_level="senior", max_results=3)
    for candidate in results:
        print(f"  {candidate['name']} - {candidate['current_title']} - {candidate['experience_years']} years")

if __name__ == "__main__":
    # Setup database
    db = setup_database()
    
    # Test search functionality
    test_database_search()
    
    print(f"\n🎉 Database ready for use!")
    print(f"You can now run your sourcing workflow with database channel enabled.")