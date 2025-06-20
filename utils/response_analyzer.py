# utils/response_analyzer.py - FIXED VERSION

from typing import Dict, List, Any, Tuple
import json
import re
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from dataclasses import dataclass
from enum import Enum

class ResponseQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class FitLevel(str, Enum):
    STRONG_FIT = "strong_fit"
    GOOD_FIT = "good_fit"
    MODERATE_FIT = "moderate_fit"
    POOR_FIT = "poor_fit"

@dataclass
class ResponseAnalysis:
    """Data class for storing response analysis results"""
    candidate_id: str
    overall_score: float  # 0.0 to 1.0
    quality: ResponseQuality
    fit_level: FitLevel
    strengths: List[str]
    concerns: List[str]
    key_points: List[str]
    technical_competency: float
    communication_quality: float
    motivation_level: float
    availability_status: str
    red_flags: List[str]
    recommendation: str
    next_steps: List[str]
    confidence_score: float

class ResponseAnalyzer:
    """Analyzes candidate responses to screening questions"""
    
    def __init__(self, llm=None):
        self.llm = llm
        
    def analyze_response(self, 
                        candidate_response: str,
                        original_questions: List[Dict],
                        candidate_profile: Dict,
                        job_requirements: Dict) -> ResponseAnalysis:
        """
        Analyze candidate's response to screening questions
        """
        
        try:
            # Step 1: Parse and extract answers from response
            parsed_answers = self._parse_response_text(candidate_response, original_questions)
            
            # Step 2: Analyze response with LLM if available
            if self.llm:
                llm_analysis = self._analyze_with_llm(
                    parsed_answers, original_questions, candidate_profile, job_requirements
                )
                
                # Step 3: Calculate scores and create analysis object
                analysis = self._create_analysis_object(
                    llm_analysis, candidate_profile['id'], candidate_response
                )
            else:
                # Use rule-based analysis if no LLM
                analysis = self._create_rule_based_analysis(
                    candidate_profile['id'], candidate_response, parsed_answers
                )
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing response: {str(e)}")
            return self._create_fallback_analysis(candidate_profile['id'], candidate_response)
    
    def _parse_response_text(self, response_text: str, original_questions: List[Dict]) -> Dict[str, str]:
        """Parse candidate response and map answers to questions"""
        
        # Clean the response text
        response_text = self._clean_response_text(response_text)
        
        # Try to identify answers to specific questions
        parsed_answers = {}
        
        # Look for numbered answers (1., 2., etc.)
        try:
            numbered_pattern = r'(\d+)\.?\s*([^0-9]*?)(?=\d+\.|$)'
            numbered_matches = re.findall(numbered_pattern, response_text, re.DOTALL)
            
            if numbered_matches and len(numbered_matches) >= len(original_questions) // 2:
                # If we found numbered answers
                for i, (num, answer) in enumerate(numbered_matches):
                    if i < len(original_questions):
                        question_id = original_questions[i].get('id', i + 1)
                        parsed_answers[f"question_{question_id}"] = answer.strip()
            else:
                # If no clear numbering, try to split by paragraphs or logical breaks
                paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
                
                for i, paragraph in enumerate(paragraphs[:len(original_questions)]):
                    if i < len(original_questions):
                        question_id = original_questions[i].get('id', i + 1)
                        parsed_answers[f"question_{question_id}"] = paragraph
        except Exception as e:
            print(f"Error parsing numbered responses: {str(e)}")
        
        # If we still don't have enough answers, treat the whole response as a single answer
        if len(parsed_answers) < len(original_questions) // 2:
            parsed_answers["full_response"] = response_text
        
        return parsed_answers
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and normalize response text"""
        if not text:
            return ""
        
        try:
            # Remove email signatures and footers
            text = re.sub(r'(Best regards|Sincerely|Thanks|Thank you).*$', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'Sent from my.*$', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'On.*wrote:.*$', '', text, flags=re.DOTALL)
            
            # Remove excessive whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            return text.strip()
        except Exception as e:
            print(f"Error cleaning text: {str(e)}")
            return text
    
    def _analyze_with_llm(self, parsed_answers: Dict[str, str], 
                         original_questions: List[Dict],
                         candidate_profile: Dict,
                         job_requirements: Dict) -> Dict:
        """Use LLM to analyze the candidate's responses"""
        
        analysis_prompt = PromptTemplate(
            input_variables=[
                "candidate_name", "candidate_background", "job_title", "job_requirements",
                "questions_and_answers", "job_description"
            ],
            template="""
            You are an expert HR professional analyzing a candidate's responses to screening questions.
            
            CANDIDATE PROFILE:
            Name: {candidate_name}
            Background: {candidate_background}
            
            JOB DETAILS:
            Position: {job_title}
            Requirements: {job_requirements}
            Description: {job_description}
            
            CANDIDATE'S RESPONSES:
            {questions_and_answers}
            
            ANALYSIS REQUIREMENTS:
            Evaluate the candidate's responses across these dimensions:
            1. Technical Competency (0.0-1.0)
            2. Communication Quality (0.0-1.0)
            3. Motivation Level (0.0-1.0)
            4. Job Fit (0.0-1.0)
            5. Overall Assessment (0.0-1.0)
            
            Return your analysis as a JSON object with this structure:
            {{
                "overall_score": 0.85,
                "technical_competency": 0.9,
                "communication_quality": 0.8,
                "motivation_level": 0.9,
                "job_fit_score": 0.85,
                "quality_assessment": "excellent|good|fair|poor",
                "fit_level": "strong_fit|good_fit|moderate_fit|poor_fit",
                "strengths": [
                    "Strong technical background in required skills",
                    "Clear communication style",
                    "Genuine enthusiasm for the role"
                ],
                "concerns": [
                    "Limited experience with specific technology X",
                    "Unclear about availability timeline"
                ],
                "key_points": [
                    "5 years experience with Python and ML",
                    "Led team of 3 developers",
                    "Available to start in 2 weeks"
                ],
                "red_flags": [],
                "availability_status": "Available in 2 weeks",
                "recommendation": "Move forward with technical interview",
                "next_steps": [
                    "Schedule technical interview",
                    "Request portfolio/code samples"
                ],
                "confidence_score": 0.85
            }}
            
            Focus on:
            - Specific examples and concrete details in answers
            - Alignment between candidate background and job requirements
            - Quality of communication and professionalism
            - Red flags or concerning responses
            - Evidence of genuine interest and motivation
            
            Be thorough but fair in your assessment.
            """
        )
        
        try:
            # Format questions and answers for the prompt
            qa_text = self._format_questions_and_answers(original_questions, parsed_answers)
            
            prompt = analysis_prompt.format(
                candidate_name=candidate_profile.get('name', 'Unknown'),
                candidate_background=self._format_candidate_background(candidate_profile),
                job_title=job_requirements.get('title', 'Unknown Position'),
                job_requirements=', '.join(job_requirements.get('required_skills', [])),
                job_description=job_requirements.get('description', '')[:500],
                questions_and_answers=qa_text
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse LLM response
            try:
                # Clean and extract JSON from response
                content = response.content.strip()
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group()
                
                analysis_data = json.loads(content)
                return analysis_data
                
            except Exception as e:
                print(f"Error parsing LLM response: {str(e)}")
                return self._get_fallback_llm_analysis()
                
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            return self._get_fallback_llm_analysis()
    
    def _create_rule_based_analysis(self, candidate_id: str, response_text: str, 
                                   parsed_answers: Dict[str, str]) -> ResponseAnalysis:
        """Create analysis using rule-based approach when LLM is not available"""
        
        # Calculate basic metrics
        response_length = len(response_text.split()) if response_text else 0
        
        # Look for positive indicators
        positive_indicators = [
            r'experience',
            r'project',
            r'built',
            r'developed',
            r'led',
            r'team',
            r'years',
            r'interested',
            r'excited',
            r'passion'
        ]
        
        positive_score = 0
        for indicator in positive_indicators:
            if re.search(indicator, response_text, re.IGNORECASE):
                positive_score += 0.1
        
        # Calculate scores
        length_score = min(response_length / 100, 1.0)  # Normalize to 100 words = 1.0
        content_score = min(positive_score, 1.0)
        
        overall_score = (length_score * 0.3 + content_score * 0.7)
        
        # Determine quality and fit level
        if overall_score >= 0.8:
            quality = ResponseQuality.EXCELLENT
            fit_level = FitLevel.STRONG_FIT
            recommendation = "Move forward with technical interview"
        elif overall_score >= 0.6:
            quality = ResponseQuality.GOOD
            fit_level = FitLevel.GOOD_FIT
            recommendation = "Schedule follow-up call"
        elif overall_score >= 0.4:
            quality = ResponseQuality.FAIR
            fit_level = FitLevel.MODERATE_FIT
            recommendation = "Request additional information"
        else:
            quality = ResponseQuality.POOR
            fit_level = FitLevel.POOR_FIT
            recommendation = "Pass on candidate"
        
        return ResponseAnalysis(
            candidate_id=candidate_id,
            overall_score=overall_score,
            quality=quality,
            fit_level=fit_level,
            strengths=self._extract_strengths(response_text),
            concerns=self._extract_concerns(response_text, overall_score),
            key_points=self._extract_key_points(response_text),
            technical_competency=min(overall_score + 0.1, 1.0),
            communication_quality=length_score,
            motivation_level=content_score,
            availability_status=self._extract_availability(response_text),
            red_flags=self._extract_red_flags(response_text),
            recommendation=recommendation,
            next_steps=self._generate_next_steps(overall_score),
            confidence_score=0.7  # Medium confidence for rule-based analysis
        )
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract strengths from response text"""
        strengths = []
        
        if re.search(r'\d+\s*(years?|yrs?)', text, re.IGNORECASE):
            strengths.append("Has quantified experience")
        
        if re.search(r'(project|built|developed|created)', text, re.IGNORECASE):
            strengths.append("Mentions specific projects or achievements")
        
        if re.search(r'(team|collaboration|worked with)', text, re.IGNORECASE):
            strengths.append("Shows teamwork experience")
        
        if re.search(r'(excited|interested|passion|love)', text, re.IGNORECASE):
            strengths.append("Demonstrates enthusiasm")
        
        if len(text.split()) > 150:
            strengths.append("Provided detailed responses")
        
        return strengths if strengths else ["Provided response to screening questions"]
    
    def _extract_concerns(self, text: str, score: float) -> List[str]:
        """Extract concerns from response text"""
        concerns = []
        
        if len(text.split()) < 50:
            concerns.append("Response is quite brief")
        
        if score < 0.5:
            concerns.append("Limited alignment with role requirements")
        
        if not re.search(r'\d+', text):
            concerns.append("Lacks specific metrics or timeframes")
        
        return concerns
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from response text"""
        key_points = []
        
        # Look for years of experience
        years_match = re.search(r'(\d+)\s*(years?|yrs?)', text, re.IGNORECASE)
        if years_match:
            key_points.append(f"{years_match.group(1)} years of experience mentioned")
        
        # Look for technologies mentioned
        tech_keywords = ['Python', 'Django', 'React', 'JavaScript', 'AWS', 'SQL', 'Git']
        mentioned_tech = [tech for tech in tech_keywords if tech.lower() in text.lower()]
        if mentioned_tech:
            key_points.append(f"Technologies mentioned: {', '.join(mentioned_tech)}")
        
        # Look for availability
        if re.search(r'(available|start|notice)', text, re.IGNORECASE):
            key_points.append("Discussed availability")
        
        return key_points if key_points else [f"Response length: {len(text.split())} words"]
    
    def _extract_availability(self, text: str) -> str:
        """Extract availability information"""
        
        if re.search(r'immediately|right away|asap', text, re.IGNORECASE):
            return "Immediate"
        elif re.search(r'(\d+)\s*(weeks?|days?)', text, re.IGNORECASE):
            match = re.search(r'(\d+)\s*(weeks?|days?)', text, re.IGNORECASE)
            return f"Available in {match.group(1)} {match.group(2)}"
        elif re.search(r'notice', text, re.IGNORECASE):
            return "Needs to give notice"
        else:
            return "Unclear"
    
    def _extract_red_flags(self, text: str) -> List[str]:
        """Extract potential red flags"""
        red_flags = []
        
        if len(text.split()) < 20:
            red_flags.append("Extremely brief response")
        
        if not re.search(r'[.!?]', text):
            red_flags.append("Poor punctuation/formatting")
        
        negative_words = ['hate', 'dislike', 'terrible', 'awful', 'worst']
        if any(word in text.lower() for word in negative_words):
            red_flags.append("Negative language detected")
        
        return red_flags
    
    def _generate_next_steps(self, score: float) -> List[str]:
        """Generate next steps based on score"""
        
        if score >= 0.8:
            return ["Schedule technical interview", "Request portfolio/code samples"]
        elif score >= 0.6:
            return ["Schedule follow-up call", "Ask clarifying questions"]
        elif score >= 0.4:
            return ["Request additional information", "Consider for manual review"]
        else:
            return ["Send polite rejection", "Keep profile for future opportunities"]
    
    def _format_questions_and_answers(self, questions: List[Dict], answers: Dict[str, str]) -> str:
        """Format questions and answers for LLM analysis"""
        
        formatted = ""
        
        for i, question in enumerate(questions):
            q_id = question.get('id', i + 1)
            question_text = question.get('question', f'Question {i + 1}')
            answer_key = f"question_{q_id}"
            
            answer = answers.get(answer_key, answers.get('full_response', 'No clear answer provided'))
            
            formatted += f"Q{q_id}: {question_text}\n"
            formatted += f"A{q_id}: {answer}\n\n"
        
        return formatted
    
    def _format_candidate_background(self, candidate_profile: Dict) -> str:
        """Format candidate background for LLM prompt"""
        
        background_parts = []
        
        if candidate_profile.get('skills'):
            background_parts.append(f"Skills: {', '.join(candidate_profile['skills'])}")
        
        if candidate_profile.get('experience_years'):
            background_parts.append(f"Experience: {candidate_profile['experience_years']} years")
        
        if candidate_profile.get('education'):
            background_parts.append(f"Education: {', '.join(candidate_profile['education'])}")
        
        return ' | '.join(background_parts) if background_parts else 'Limited background information available'
    
    def _create_analysis_object(self, llm_analysis: Dict, candidate_id: str, 
                               original_response: str) -> ResponseAnalysis:
        """Create ResponseAnalysis object from LLM analysis"""
        
        return ResponseAnalysis(
            candidate_id=candidate_id,
            overall_score=llm_analysis.get('overall_score', 0.5),
            quality=ResponseQuality(llm_analysis.get('quality_assessment', 'fair')),
            fit_level=FitLevel(llm_analysis.get('fit_level', 'moderate_fit')),
            strengths=llm_analysis.get('strengths', []),
            concerns=llm_analysis.get('concerns', []),
            key_points=llm_analysis.get('key_points', []),
            technical_competency=llm_analysis.get('technical_competency', 0.5),
            communication_quality=llm_analysis.get('communication_quality', 0.5),
            motivation_level=llm_analysis.get('motivation_level', 0.5),
            availability_status=llm_analysis.get('availability_status', 'Unclear'),
            red_flags=llm_analysis.get('red_flags', []),
            recommendation=llm_analysis.get('recommendation', 'Request additional information'),
            next_steps=llm_analysis.get('next_steps', []),
            confidence_score=llm_analysis.get('confidence_score', 0.5)
        )
    
    def _create_fallback_analysis(self, candidate_id: str, response_text: str) -> ResponseAnalysis:
        """Create basic analysis when LLM analysis fails"""
        
        # Basic heuristics for fallback analysis
        response_length = len(response_text.split()) if response_text else 0
        has_examples = bool(re.search(r'(example|project|experience|worked on)', response_text, re.IGNORECASE)) if response_text else False
        
        score = 0.3  # Base score
        if response_length > 50:
            score += 0.2
        if has_examples:
            score += 0.2
        if response_length > 100:
            score += 0.1
        
        return ResponseAnalysis(
            candidate_id=candidate_id,
            overall_score=min(score, 1.0),
            quality=ResponseQuality.FAIR,
            fit_level=FitLevel.MODERATE_FIT,
            strengths=["Provided response to screening questions"],
            concerns=["Analysis incomplete due to system limitations"],
            key_points=[f"Response length: {response_length} words"],
            technical_competency=0.5,
            communication_quality=0.5,
            motivation_level=0.5,
            availability_status="Unclear",
            red_flags=[],
            recommendation="Manual review required",
            next_steps=["Human recruiter should review response"],
            confidence_score=0.3
        )
    
    def _get_fallback_llm_analysis(self) -> Dict:
        """Fallback analysis data when LLM parsing fails"""
        return {
            'overall_score': 0.5,
            'technical_competency': 0.5,
            'communication_quality': 0.5,
            'motivation_level': 0.5,
            'job_fit_score': 0.5,
            'quality_assessment': 'fair',
            'fit_level': 'moderate_fit',
            'strengths': ['Provided response'],
            'concerns': ['Response analysis incomplete'],
            'key_points': [],
            'red_flags': [],
            'availability_status': 'Unclear',
            'recommendation': 'Manual review required',
            'next_steps': ['Human review needed'],
            'confidence_score': 0.3
        }
    
    def generate_response_summary(self, analysis: ResponseAnalysis) -> str:
        """Generate a human-readable summary of the analysis"""
        
        summary = f"**Response Analysis for Candidate {analysis.candidate_id}**\n\n"
        summary += f"**Overall Score:** {analysis.overall_score:.2f}/1.0 ({analysis.quality.value})\n"
        summary += f"**Fit Level:** {analysis.fit_level.value.replace('_', ' ').title()}\n"
        summary += f"**Recommendation:** {analysis.recommendation}\n\n"
        
        if analysis.strengths:
            summary += "**Strengths:**\n"
            for strength in analysis.strengths:
                summary += f"• {strength}\n"
            summary += "\n"
        
        if analysis.concerns:
            summary += "**Concerns:**\n"
            for concern in analysis.concerns:
                summary += f"• {concern}\n"
            summary += "\n"
        
        if analysis.red_flags:
            summary += "**⚠️ Red Flags:**\n"
            for flag in analysis.red_flags:
                summary += f"• {flag}\n"
            summary += "\n"
        
        summary += "**Detailed Scores:**\n"
        summary += f"• Technical Competency: {analysis.technical_competency:.2f}\n"
        summary += f"• Communication Quality: {analysis.communication_quality:.2f}\n"
        summary += f"• Motivation Level: {analysis.motivation_level:.2f}\n"
        summary += f"• Availability: {analysis.availability_status}\n\n"
        
        if analysis.next_steps:
            summary += "**Recommended Next Steps:**\n"
            for step in analysis.next_steps:
                summary += f"• {step}\n"
        
        return summary