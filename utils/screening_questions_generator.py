# utils/screening_questions_generator.py
from typing import List, Dict, Any
import json
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

class ScreeningQuestionsGenerator:
    """Generate personalized screening questions based on job requirements and candidate profile"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.question_categories = {
            'technical': 'Technical Skills & Experience',
            'behavioral': 'Behavioral & Soft Skills',
            'experience': 'Work Experience & Background',
            'motivation': 'Motivation & Career Goals',
            'availability': 'Availability & Logistics'
        }
    
    def generate_screening_questions(self, candidate, job_description, 
                                num_questions: int = 5,
                                categories: List[str] = None) -> Dict[str, Any]:
        """
        Generate personalized screening questions for a candidate
        
        Args:
            candidate: Candidate object
            job_description: JobDescription object
            num_questions: Number of questions to generate (default 5)
            categories: List of question categories to include
            
        Returns:
            Dict containing questions and metadata
        """
        
        if categories is None:
            categories = ['technical', 'experience', 'motivation', 'availability']
        
        try:
            # Generate questions using LLM
            questions_data = self._generate_questions_with_llm(
                candidate, job_description, num_questions, categories
            )
            
            return {
                'questions': questions_data['questions'],
                'metadata': {
                    'candidate_name': candidate.name,
                    'job_title': job_description.title,
                    'company': job_description.company,
                    'categories_used': categories,
                    'total_questions': len(questions_data['questions']),
                    'generation_method': 'llm',
                    'difficulty_level': questions_data.get('difficulty_level', 'intermediate')
                },
                'scoring_rubric': questions_data.get('scoring_rubric', {}),
                'follow_up_suggestions': questions_data.get('follow_up_suggestions', [])
            }
            
        except Exception as e:
            print(f"Error generating questions with LLM: {str(e)}")
            # Fallback to template-based questions
            return self._generate_fallback_questions(candidate, job_description, num_questions, categories)
    
    def _generate_questions_with_llm(self, candidate, job_description, num_questions, categories):
        """Generate questions using LLM"""
        
        questions_prompt = PromptTemplate(
            input_variables=[
                "candidate_name", "candidate_skills", "candidate_experience", 
                "job_title", "company", "job_skills", "job_description",
                "num_questions", "categories"
            ],
            template="""
            You are an expert HR professional creating screening questions for a job candidate.
            
            CANDIDATE PROFILE:
            - Name: {candidate_name}
            - Skills: {candidate_skills}
            - Experience: {candidate_experience} years
            
            JOB DETAILS:
            - Position: {job_title}
            - Company: {company}
            - Required Skills: {job_skills}
            - Description: {job_description}
            
            REQUIREMENTS:
            - Generate {num_questions} screening questions
            - Include categories: {categories}
            - Questions should be specific to this candidate and role
            - Mix of technical and behavioral questions
            - Questions should help assess job fit
            
            INSTRUCTIONS:
            1. Create questions that are relevant to both the candidate's background and job requirements
            2. Include a mix of skill assessment, experience validation, and motivation
            3. Make questions specific, not generic
            4. Provide scoring guidance for each question
            
            Return your response as a JSON object with this exact structure:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "category": "technical|behavioral|experience|motivation|availability",
                        "question": "The actual question text",
                        "rationale": "Why this question is important for this role",
                        "expected_answer_points": ["key point 1", "key point 2", "key point 3"],
                        "red_flags": ["warning sign 1", "warning sign 2"],
                        "follow_up_questions": ["optional follow-up question"]
                    }}
                ],
                "difficulty_level": "beginner|intermediate|advanced",
                "scoring_rubric": {{
                    "excellent": "4-5 strong answers with specific examples",
                    "good": "3-4 solid answers with some specifics",
                    "fair": "2-3 adequate answers but lacking detail",
                    "poor": "0-2 weak or concerning answers"
                }},
                "follow_up_suggestions": [
                    "Suggestion for next steps based on answers"
                ]
            }}
            
            Make the questions specific to {candidate_name}'s background in {candidate_skills} for the {job_title} role.
            """
        )
        
        prompt = questions_prompt.format(
            candidate_name=candidate.name,
            candidate_skills=", ".join(candidate.skills),
            candidate_experience=candidate.experience_years,
            job_title=job_description.title,
            company=job_description.company,
            job_skills=", ".join(job_description.required_skills),
            job_description=job_description.description[:500],  # Truncate if too long
            num_questions=num_questions,
            categories=", ".join(categories)
        )
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Clean and parse the response
        content = response.content.strip()
        
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        questions_data = json.loads(content)
        
        # Validate the structure
        if 'questions' not in questions_data:
            raise ValueError("Invalid response structure: missing 'questions'")
        
        return questions_data
    
    def _generate_fallback_questions(self, candidate, job_description, num_questions, categories):
        """Generate fallback questions using templates"""
        
        questions = []
        question_id = 1
        
        # Technical questions
        if 'technical' in categories:
            tech_questions = self._get_technical_questions(candidate, job_description)
            for q in tech_questions[:max(1, num_questions // 2)]:
                questions.append({
                    'id': question_id,
                    'category': 'technical',
                    'question': q,
                    'rationale': 'Assess technical competency',
                    'expected_answer_points': ['Specific examples', 'Technical knowledge', 'Problem-solving approach'],
                    'red_flags': ['Vague answers', 'Lack of hands-on experience'],
                    'follow_up_questions': ['Can you walk me through a specific example?']
                })
                question_id += 1
        
        # Experience questions
        if 'experience' in categories:
            exp_questions = self._get_experience_questions(candidate, job_description)
            for q in exp_questions[:max(1, num_questions // 4)]:
                questions.append({
                    'id': question_id,
                    'category': 'experience',
                    'question': q,
                    'rationale': 'Validate work experience',
                    'expected_answer_points': ['Relevant experience', 'Measurable results', 'Growth trajectory'],
                    'red_flags': ['Gaps in experience', 'Lack of progression'],
                    'follow_up_questions': ['What was the impact of your work?']
                })
                question_id += 1
        
        # Motivation questions
        if 'motivation' in categories:
            motivation_questions = self._get_motivation_questions(candidate, job_description)
            for q in motivation_questions[:max(1, num_questions // 4)]:
                questions.append({
                    'id': question_id,
                    'category': 'motivation',
                    'question': q,
                    'rationale': 'Assess cultural fit and motivation',
                    'expected_answer_points': ['Clear career goals', 'Company knowledge', 'Role enthusiasm'],
                    'red_flags': ['Lack of research', 'Purely money-motivated'],
                    'follow_up_questions': ['What specifically interests you about this role?']
                })
                question_id += 1
        
        # Availability questions
        if 'availability' in categories:
            questions.append({
                'id': question_id,
                'category': 'availability',
                'question': 'What is your current notice period and availability to start?',
                'rationale': 'Confirm logistics and timing',
                'expected_answer_points': ['Clear timeline', 'Professional approach to current role'],
                'red_flags': ['Immediate availability without notice', 'Vague timelines'],
                'follow_up_questions': ['Are there any commitments that might affect your start date?']
            })
        
        return {
            'questions': questions[:num_questions],
            'metadata': {
                'generation_method': 'template-based',
                'difficulty_level': 'intermediate'
            },
            'scoring_rubric': {
                'excellent': '4-5 detailed answers with examples',
                'good': '3-4 solid answers',
                'fair': '2-3 basic answers',
                'poor': '0-2 weak answers'
            },
            'follow_up_suggestions': [
                'Schedule technical interview if answers are strong',
                'Request portfolio or code samples',
                'Discuss compensation and benefits'
            ]
        }
    
    def _get_technical_questions(self, candidate, job_description):
        """Generate technical questions based on skills overlap"""
        common_skills = set(candidate.skills) & set(job_description.required_skills)
        
        questions = []
        
        for skill in list(common_skills)[:3]:  # Top 3 overlapping skills
            questions.append(f"Can you describe your experience with {skill} and a specific project where you used it effectively?")
        
        # Add general technical questions
        questions.extend([
            f"What interests you most about working with {', '.join(job_description.required_skills[:2])}?",
            "Describe a technical challenge you faced recently and how you solved it.",
            "How do you stay updated with the latest developments in your field?"
        ])
        
        return questions
    
    def _get_experience_questions(self, candidate, job_description):
        """Generate experience-related questions"""
        return [
            f"Tell me about your {candidate.experience_years} years of experience and how it relates to this {job_description.title} role.",
            "What has been your most impactful project or achievement in your career so far?",
            "Describe a situation where you had to learn a new technology or skill quickly.",
            "What type of work environment do you thrive in?"
        ]
    
    def _get_motivation_questions(self, candidate, job_description):
        """Generate motivation and cultural fit questions"""
        return [
            f"What attracts you to the {job_description.title} position at {job_description.company}?",
            "Where do you see your career heading in the next 2-3 years?",
            "What kind of projects or challenges are you most excited to work on?",
            "How do you handle working under pressure or tight deadlines?"
        ]
    
    def format_questions_for_email(self, questions_data: Dict) -> str:
        """Format questions for inclusion in an email"""
        
        questions = questions_data['questions']
        
        email_content = f"Please take a few minutes to answer these {len(questions)} screening questions:\n\n"
        
        for i, q in enumerate(questions, 1):
            email_content += f"{i}. {q['question']}\n\n"
        
        email_content += "Please provide detailed answers and feel free to include specific examples from your experience.\n\n"
        email_content += "Thank you for taking the time to complete these questions!"
        
        return email_content
    
    def format_questions_for_interviewer(self, questions_data: Dict) -> str:
        """Format questions with guidance for interviewer use"""
        
        questions = questions_data['questions']
        metadata = questions_data['metadata']
        
        content = f"SCREENING QUESTIONS FOR {metadata['candidate_name']}\n"
        content += f"Position: {metadata['job_title']} at {metadata['company']}\n"
        content += f"Total Questions: {metadata['total_questions']}\n\n"
        
        for q in questions:
            content += f"Q{q['id']}: {q['question']}\n"
            content += f"Category: {q['category']}\n"
            content += f"Rationale: {q['rationale']}\n"
            content += f"Look for: {', '.join(q['expected_answer_points'])}\n"
            content += f"Red flags: {', '.join(q['red_flags'])}\n"
            if q.get('follow_up_questions'):
                content += f"Follow-up: {', '.join(q['follow_up_questions'])}\n"
            content += "\n" + "="*50 + "\n\n"
        
        # Add scoring rubric
        rubric = questions_data.get('scoring_rubric', {})
        if rubric:
            content += "SCORING RUBRIC:\n"
            for level, description in rubric.items():
                content += f"• {level.upper()}: {description}\n"
        
        return content