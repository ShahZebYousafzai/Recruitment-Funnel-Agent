# agents/resume_screener.py
from typing import List, Dict, Tuple
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import json

from agents.base_agent import BaseAgent
from models.candidate import Candidate, ResumeAnalysis, CandidateStatus
from models.job_description import JobDescription
from utils.text_processing import TextProcessor
from utils.pdf_parser import DocumentParser
from config.settings import settings

class ResumeScreenerAgent(BaseAgent):
    """Agent responsible for screening and ranking resumes"""
    
    def __init__(self):
        super().__init__("Resume Screener Agent")
        self.text_processor = TextProcessor()
        self.doc_parser = DocumentParser()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.skill_keywords = self._load_skill_keywords()
        
    def _load_skill_keywords(self) -> List[str]:
        """Load common technical skills for matching"""
        return [
            # Programming Languages
            "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", "Go", "Rust", "Swift",
            "Kotlin", "TypeScript", "SQL", "R", "Scala", "Perl", "Shell", "Bash",
            
            # Frameworks & Libraries
            "React", "Angular", "Vue.js", "Django", "Flask", "FastAPI", "Spring", "Express.js",
            "Node.js", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            
            # Technologies & Tools
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Jenkins", "CI/CD",
            "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "Apache Kafka",
            
            # Skills
            "Machine Learning", "Deep Learning", "Data Science", "DevOps", "Cloud Computing",
            "Microservices", "API Development", "Database Design", "System Design",
            "Agile", "Scrum", "Project Management"
        ]
    
    def execute(self, input_data: Dict) -> Dict:
        """
        Main execution method for resume screening
        
        Args:
            input_data: {
                'job_description': JobDescription,
                'resume_file_path': str,
                'candidate_info': Dict (optional)
            }
        
        Returns:
            Dict containing screening results
        """
        try:
            job_description = input_data['job_description']
            resume_file_path = input_data['resume_file_path']
            candidate_info = input_data.get('candidate_info', {})
            
            self.log(f"Starting resume screening for job: {job_description.title}")
            
            # Step 1: Extract text from resume
            resume_text = self._extract_resume_text(resume_file_path)
            
            # Step 2: Analyze resume content
            analysis = self._analyze_resume(resume_text)
            
            # Step 3: Create candidate object
            candidate = self._create_candidate(analysis, candidate_info, resume_text)
            
            # Step 4: Score candidate against job description
            score, feedback = self._score_candidate(candidate, job_description)
            
            # Step 5: Update candidate with screening results
            candidate.screening_score = score
            candidate.screening_feedback = feedback
            candidate.status = CandidateStatus.QUALIFIED if score >= settings.SIMILARITY_THRESHOLD else CandidateStatus.REJECTED
            
            self.log(f"Resume screening completed. Score: {score:.2f}")
            
            return {
                'candidate': candidate,
                'analysis': analysis,
                'qualified': score >= settings.SIMILARITY_THRESHOLD,
                'score': score,
                'feedback': feedback
            }
            
        except Exception as e:
            self.log(f"Error during resume screening: {str(e)}")
            raise e
    
    def _extract_resume_text(self, file_path: str) -> str:
        """Extract text from resume file based on file type"""
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return self.doc_parser.extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            return self.doc_parser.extract_text_from_docx(file_path)
        elif file_extension == 'txt':
            return self.doc_parser.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _analyze_resume(self, resume_text: str) -> ResumeAnalysis:
        """Analyze resume content using LLM"""
        
        analysis_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            Analyze the following resume and extract key information. Return the response as a JSON object with the following structure:
            
            {{
                "skills": ["list of technical skills found"],
                "experience_years": "estimated years of experience as a number",
                "education_level": "highest education level (e.g., Bachelor's, Master's, PhD, High School)",
                "previous_companies": ["list of previous companies"],
                "key_achievements": ["list of notable achievements or accomplishments"],
                "contact_info": {{"email": "email if found", "phone": "phone if found", "name": "full name"}},
                "summary": "brief professional summary of the candidate"
            }}
            
            Resume Text:
            {resume_text}
            
            Important: Return only valid JSON format without any additional text or formatting.
            """
        )
        
        try:
            prompt = analysis_prompt.format(resume_text=resume_text)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse LLM response
            analysis_data = json.loads(response.content)
            
            # Also extract skills using keyword matching as backup
            extracted_skills = self.text_processor.extract_skills(resume_text, self.skill_keywords)
            
            # Combine LLM-extracted skills with keyword-matched skills
            all_skills = list(set(analysis_data.get('skills', []) + extracted_skills))
            
            return ResumeAnalysis(
                candidate_id="",  # Will be set later
                extracted_skills=all_skills,
                experience_years=float(analysis_data.get('experience_years', 0)),
                education_level=analysis_data.get('education_level', ''),
                previous_companies=analysis_data.get('previous_companies', []),
                key_achievements=analysis_data.get('key_achievements', []),
                contact_info=analysis_data.get('contact_info', {}),
                summary=analysis_data.get('summary', '')
            )
            
        except Exception as e:
            self.log(f"Error in LLM analysis, falling back to rule-based extraction: {str(e)}")
            return self._fallback_analysis(resume_text)
    
    def _fallback_analysis(self, resume_text: str) -> ResumeAnalysis:
        """Fallback analysis using rule-based methods"""
        return ResumeAnalysis(
            candidate_id="",
            extracted_skills=self.text_processor.extract_skills(resume_text, self.skill_keywords),
            experience_years=self.text_processor.extract_experience_years(resume_text),
            education_level="Not specified",
            previous_companies=[],
            key_achievements=[],
            contact_info={
                "email": self.text_processor.extract_email(resume_text),
                "phone": self.text_processor.extract_phone(resume_text),
                "name": "Not specified"
            },
            summary="Generated from rule-based analysis"
        )
    
    def _create_candidate(self, analysis: ResumeAnalysis, candidate_info: Dict, resume_text: str) -> Candidate:
        """Create candidate object from analysis"""
        contact_info = analysis.contact_info
        
        return Candidate(
            name=candidate_info.get('name', contact_info.get('name', 'Unknown')),
            email=candidate_info.get('email', contact_info.get('email', '')),
            phone=candidate_info.get('phone', contact_info.get('phone', '')),
            resume_text=resume_text,
            skills=analysis.extracted_skills,
            experience_years=analysis.experience_years,
            education=[analysis.education_level] if analysis.education_level else [],
            previous_roles=analysis.previous_companies
        )
    
    def _score_candidate(self, candidate: Candidate, job_description: JobDescription) -> Tuple[float, str]:
        """Score candidate against job description"""
        
        # 1. Skills matching score
        skills_score = self._calculate_skills_score(candidate.skills, job_description.required_skills)
        
        # 2. Experience score
        experience_score = self._calculate_experience_score(candidate.experience_years, job_description.min_experience)
        
        # 3. Semantic similarity score
        semantic_score = self._calculate_semantic_similarity(candidate.resume_text, job_description.description)
        
        # 4. Calculate weighted final score
        final_score = (
            skills_score * settings.SKILLS_WEIGHT +
            experience_score * settings.EXPERIENCE_WEIGHT +
            semantic_score * settings.KEYWORDS_WEIGHT
        )
        
        # Generate feedback
        feedback = self._generate_feedback(candidate, job_description, skills_score, experience_score, semantic_score)
        
        return final_score, feedback
    
    def _calculate_skills_score(self, candidate_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skills matching score"""
        if not required_skills:
            return 1.0
        
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matched_skills = sum(1 for skill in required_skills_lower if skill in candidate_skills_lower)
        return matched_skills / len(required_skills)
    
    def _calculate_experience_score(self, candidate_experience: float, required_experience: float) -> float:
        """Calculate experience score"""
        if required_experience == 0:
            return 1.0
        
        if candidate_experience >= required_experience:
            return 1.0
        else:
            # Partial credit for some experience
            return candidate_experience / required_experience
    
    def _calculate_semantic_similarity(self, resume_text: str, job_description: str) -> float:
        """Calculate semantic similarity between resume and job description"""
        try:
            # Use sentence transformers for semantic similarity
            resume_embedding = self.embedding_model.encode([resume_text])
            job_embedding = self.embedding_model.encode([job_description])
            
            similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
            return max(0.0, similarity)  # Ensure non-negative
            
        except Exception as e:
            self.log(f"Error calculating semantic similarity: {str(e)}")
            # Fallback to TF-IDF similarity
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return max(0.0, similarity)
    
    def _generate_feedback(self, candidate: Candidate, job_description: JobDescription, 
                          skills_score: float, experience_score: float, semantic_score: float) -> str:
        """Generate detailed feedback for the candidate"""
        
        feedback_parts = []
        
        # Skills feedback
        if skills_score >= 0.8:
            feedback_parts.append("✅ Strong skills match for the position")
        elif skills_score >= 0.5:
            feedback_parts.append("⚠️ Partial skills match - some key skills missing")
        else:
            feedback_parts.append("❌ Limited skills match for the position")
        
        # Experience feedback
        if experience_score >= 1.0:
            feedback_parts.append("✅ Meets experience requirements")
        elif experience_score >= 0.5:
            feedback_parts.append("⚠️ Has some relevant experience but below requirements")
        else:
            feedback_parts.append("❌ Insufficient experience for the role")
        
        # Overall semantic match
        if semantic_score >= 0.6:
            feedback_parts.append("✅ Good overall fit for the role")
        elif semantic_score >= 0.4:
            feedback_parts.append("⚠️ Moderate fit for the role")
        else:
            feedback_parts.append("❌ Limited fit for the role requirements")
        
        return " | ".join(feedback_parts)
    
    def batch_screen_resumes(self, job_description: JobDescription, resume_files: List[str]) -> List[Dict]:
        """Screen multiple resumes in batch"""
        results = []
        
        for resume_file in resume_files:
            try:
                input_data = {
                    'job_description': job_description,
                    'resume_file_path': resume_file
                }
                result = self.execute(input_data)
                results.append(result)
            except Exception as e:
                self.log(f"Error screening {resume_file}: {str(e)}")
                continue
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results