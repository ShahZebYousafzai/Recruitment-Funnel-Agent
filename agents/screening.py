from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from fuzzywuzzy import fuzz
from models.screening import ScreeningCriteria, ScreeningResult, SkillMatch, ScreeningSummary
from models.sourcing import CandidateProfile, SourceChannel
from utils import create_candidate_from_raw_data
import logging

class ScreeningAgent:
    """Agent responsible for candidate screening and scoring - FIXED VERSION"""
    
    def __init__(self):
        # Skill synonyms and related terms for better matching
        self.skill_synonyms = {
            "python": ["python", "python3", "py"],
            "machine learning": ["machine learning", "ml", "artificial intelligence", "ai"],
            "pytorch": ["pytorch", "torch", "py-torch"],
            "tensorflow": ["tensorflow", "tf", "tensor flow"],
            "nlp": ["nlp", "natural language processing", "text processing", "language models"],
            "computer vision": ["computer vision", "cv", "image processing", "opencv"],
            "javascript": ["javascript", "js", "ecmascript", "node.js", "nodejs"],
            "react": ["react", "reactjs", "react.js"],
            "java": ["java", "jvm"],
            "sql": ["sql", "mysql", "postgresql", "postgres", "database"],
            "aws": ["aws", "amazon web services", "amazon cloud"],
            "docker": ["docker", "containerization", "containers"],
            "kubernetes": ["kubernetes", "k8s", "container orchestration"],
            "git": ["git", "version control", "github", "gitlab"],
            "api": ["api", "rest api", "restful", "web services"],
            "agile": ["agile", "scrum", "kanban"],
        }
    
    def screen_candidate(self, candidate_data: Dict[str, Any], job_requirements: Dict[str, Any], 
                        screening_criteria: ScreeningCriteria) -> ScreeningResult:
        """Screen a single candidate against job requirements - FIXED VERSION"""
        
        try:
            # Create candidate profile from raw data
            source_channel = SourceChannel.DATABASE  # Default for screening stage
            if 'source' in candidate_data:
                source_map = {
                    'linkedin': SourceChannel.LINKEDIN,
                    'indeed': SourceChannel.INDEED,
                    'database': SourceChannel.DATABASE
                }
                source_channel = source_map.get(candidate_data['source'], SourceChannel.DATABASE)
            
            candidate = create_candidate_from_raw_data(candidate_data, source_channel)
            
            print(f"    🔍 Analyzing: {candidate.name} ({candidate.source_id})")
            
            # Initialize screening result with all required fields
            result = ScreeningResult(
                candidate_id=candidate.source_id,
                candidate_name=candidate.name or "Unknown",
                experience_years=candidate.experience_years,
                candidate_location=candidate.location,
                # Initialize all required fields with default values
                required_skills_score=0.0,
                preferred_skills_score=0.0,
                experience_score=0.0,
                experience_level_match="under",
                location_score=0.0,
                location_match=False,
                education_score=0.0,
                education_match=False,
                overall_score=0.0,
                weighted_score=0.0,
                passes_screening=False,
                recommended_for_shortlist=False,
                skill_matches=[],
                missing_critical_skills=[],
                strengths=[],
                concerns=[]
            )
            
            # Perform analysis
            self._analyze_skills(candidate, job_requirements, result)
            self._analyze_experience(candidate, job_requirements, screening_criteria, result)
            self._analyze_location(candidate, job_requirements, screening_criteria, result)
            self._analyze_education(candidate, job_requirements, screening_criteria, result)
            
            # Calculate scores
            self._calculate_scores(result, screening_criteria)
            
            # Make decisions
            self._make_decisions(result, screening_criteria)
            
            # Generate insights
            self._generate_insights(result, candidate)
            
            print(f"      📊 Score: {result.weighted_score:.1f} | Pass: {result.passes_screening} | Shortlist: {result.recommended_for_shortlist}")
            
            return result
            
        except Exception as e:
            logging.error(f"Error in screen_candidate: {e}", exc_info=True)
            # Return a minimal valid result on error
            return ScreeningResult(
                candidate_id=candidate_data.get('source_id', candidate_data.get('id', 'unknown')),
                candidate_name=candidate_data.get('name', 'Unknown'),
                experience_years=candidate_data.get('experience_years', 0),
                candidate_location=candidate_data.get('location', ''),
                required_skills_score=0.0,
                preferred_skills_score=0.0,
                experience_score=0.0,
                experience_level_match="under",
                location_score=0.0,
                location_match=False,
                education_score=0.0,
                education_match=False,
                overall_score=0.0,
                weighted_score=0.0,
                passes_screening=False,
                recommended_for_shortlist=False,
                skill_matches=[],
                missing_critical_skills=[],
                strengths=[],
                concerns=[f"Error during screening: {str(e)}"]
            )
    
    def _analyze_skills(self, candidate: CandidateProfile, job_requirements: Dict[str, Any], 
                       result: ScreeningResult):
        """Analyze candidate skills against job requirements"""
        
        required_skills = job_requirements.get('required_skills', [])
        preferred_skills = job_requirements.get('preferred_skills', [])
        candidate_skills = [skill.lower() for skill in candidate.skills]
        
        print(f"        Skills: {candidate.skills}")
        print(f"        Required: {required_skills}")
        
        # Analyze required skills
        required_matches = []
        missing_critical = []
        
        for skill in required_skills:
            skill_match = self._match_skill(skill, candidate_skills)
            required_matches.append(skill_match)
            
            if not skill_match.found:
                missing_critical.append(skill)
        
        # Analyze preferred skills
        preferred_matches = []
        for skill in preferred_skills:
            skill_match = self._match_skill(skill, candidate_skills)
            preferred_matches.append(skill_match)
        
        # Calculate scores
        required_score = self._calculate_skill_score(required_matches) if required_matches else 100.0
        preferred_score = self._calculate_skill_score(preferred_matches) if preferred_matches else 0.0
        
        # Update result
        result.required_skills_score = required_score
        result.preferred_skills_score = preferred_score
        result.skill_matches = required_matches + preferred_matches
        result.missing_critical_skills = missing_critical
        
        print(f"        Required skills score: {required_score:.1f}")
        print(f"        Missing: {missing_critical}")
    
    def _match_skill(self, required_skill: str, candidate_skills: List[str]) -> SkillMatch:
        """Match a required skill against candidate skills"""
        
        required_lower = required_skill.lower()
        
        # Check for exact match
        if required_lower in candidate_skills:
            return SkillMatch(
                skill_name=required_skill,
                found=True,
                match_type="exact",
                confidence=1.0
            )
        
        # Check synonyms
        synonyms = self.skill_synonyms.get(required_lower, [required_lower])
        for synonym in synonyms:
            if synonym in candidate_skills:
                return SkillMatch(
                    skill_name=required_skill,
                    found=True,
                    match_type="exact",
                    confidence=0.95
                )
        
        # Check for partial matches using fuzzy matching
        best_match_score = 0
        best_match_skill = None
        
        for candidate_skill in candidate_skills:
            # Use fuzzy matching
            similarity = fuzz.partial_ratio(required_lower, candidate_skill)
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_skill = candidate_skill
        
        # Determine match type based on similarity
        if best_match_score >= 85:
            return SkillMatch(
                skill_name=required_skill,
                found=True,
                match_type="partial",
                confidence=best_match_score / 100.0
            )
        elif best_match_score >= 70:
            return SkillMatch(
                skill_name=required_skill,
                found=True,
                match_type="related",
                confidence=best_match_score / 100.0
            )
        else:
            return SkillMatch(
                skill_name=required_skill,
                found=False,
                match_type="none",
                confidence=0.0
            )
    
    def _calculate_skill_score(self, matches: List[SkillMatch]) -> float:
        """Calculate overall skill score from matches"""
        if not matches:
            return 0.0
        
        total_score = sum(match.confidence * 100 for match in matches)
        return total_score / len(matches)
    
    def _analyze_experience(self, candidate: CandidateProfile, job_requirements: Dict[str, Any],
                           screening_criteria: ScreeningCriteria, result: ScreeningResult):
        """Analyze candidate experience"""
        
        candidate_exp = candidate.experience_years or 0
        min_required = screening_criteria.min_experience_years
        preferred_exp = screening_criteria.preferred_experience_years
        
        print(f"        Experience: {candidate_exp} years (min: {min_required}, preferred: {preferred_exp})")
        
        # Determine experience level match
        if candidate_exp < min_required:
            result.experience_level_match = "under"
            score = max(0, (candidate_exp / min_required) * 60) if min_required > 0 else 60
        elif candidate_exp >= preferred_exp:
            result.experience_level_match = "exceeds"
            score = min(100, 80 + (candidate_exp - preferred_exp) * 2)
        else:
            result.experience_level_match = "meets"
            # Linear interpolation between minimum and preferred
            if preferred_exp > min_required:
                score = 60 + ((candidate_exp - min_required) / (preferred_exp - min_required)) * 40
            else:
                score = 80  # Default good score if min == preferred
        
        result.experience_score = score
        print(f"        Experience score: {score:.1f} ({result.experience_level_match})")
    
    def _analyze_location(self, candidate: CandidateProfile, job_requirements: Dict[str, Any],
                         screening_criteria: ScreeningCriteria, result: ScreeningResult):
        """Analyze candidate location compatibility"""
        
        job_location = job_requirements.get('location', '')
        candidate_location = candidate.location or ''
        
        print(f"        Location: {candidate_location} vs {job_location}")
        
        # Check for remote work
        if screening_criteria.allow_remote or 'remote' in candidate_location.lower():
            result.location_score = 100.0
            result.location_match = True
            print(f"        Location score: 100.0 (remote allowed)")
            return
        
        # Check for exact location match
        if job_location.lower() in candidate_location.lower():
            result.location_score = 100.0
            result.location_match = True
            print(f"        Location score: 100.0 (exact match)")
            return
        
        # Check preferred locations
        for preferred in screening_criteria.preferred_locations:
            if preferred.lower() in candidate_location.lower():
                result.location_score = 90.0
                result.location_match = True
                print(f"        Location score: 90.0 (preferred location)")
                return
        
        # Check for same city/state using fuzzy matching
        if job_location and candidate_location:
            location_similarity = fuzz.partial_ratio(job_location.lower(), candidate_location.lower())
            if location_similarity >= 80:
                result.location_score = location_similarity
                result.location_match = True
                print(f"        Location score: {location_similarity:.1f} (fuzzy match)")
            else:
                result.location_score = 30.0
                result.location_match = False
                print(f"        Location score: 30.0 (no match)")
        else:
            result.location_score = 50.0  # Neutral score if missing data
            result.location_match = False
            print(f"        Location score: 50.0 (missing data)")
    
    def _analyze_education(self, candidate: CandidateProfile, job_requirements: Dict[str, Any],
                          screening_criteria: ScreeningCriteria, result: ScreeningResult):
        """Analyze candidate education"""
        
        if not screening_criteria.education_required:
            result.education_score = 100.0
            result.education_match = True
            return
        
        education_requirements = job_requirements.get('education_requirements', [])
        candidate_education = candidate.education
        
        if not education_requirements:
            result.education_score = 100.0
            result.education_match = True
            return
        
        if not candidate_education:
            result.education_score = 0.0
            result.education_match = False
            return
        
        # Check for education match
        for req_education in education_requirements:
            for candidate_edu in candidate_education:
                similarity = fuzz.partial_ratio(req_education.lower(), candidate_edu.lower())
                if similarity >= 70:
                    result.education_score = similarity
                    result.education_match = True
                    return
        
        result.education_score = 30.0  # Some credit for having education
        result.education_match = False
    
    def _calculate_scores(self, result: ScreeningResult, criteria: ScreeningCriteria):
        """Calculate overall and weighted scores"""
        
        # Overall score (simple average)
        scores = [
            result.required_skills_score,
            result.preferred_skills_score,
            result.experience_score,
            result.location_score
        ]
        
        if criteria.education_required:
            scores.append(result.education_score)
        
        result.overall_score = sum(scores) / len(scores)
        
        # Weighted score
        weighted_sum = (
            result.required_skills_score * criteria.required_skills_weight +
            result.preferred_skills_score * criteria.preferred_skills_weight +
            result.experience_score * criteria.experience_weight +
            result.location_score * criteria.location_weight +
            result.education_score * criteria.education_weight
        )
        
        total_weight = (
            criteria.required_skills_weight +
            criteria.preferred_skills_weight +
            criteria.experience_weight +
            criteria.location_weight +
            criteria.education_weight
        )
        
        result.weighted_score = weighted_sum / total_weight if total_weight > 0 else result.overall_score
    
    def _make_decisions(self, result: ScreeningResult, criteria: ScreeningCriteria):
        """Make pass/fail and shortlist decisions"""
        
        # Check for critical missing skills (auto-fail)
        if len(result.missing_critical_skills) > 2:  # Allow missing up to 2 critical skills
            result.passes_screening = False
            result.recommended_for_shortlist = False
            return
        
        # Check minimum experience requirement
        if result.experience_level_match == "under" and result.experience_score < 30:
            result.passes_screening = False
            result.recommended_for_shortlist = False
            return
        
        # Use weighted score for final decisions
        score_to_use = result.weighted_score
        
        result.passes_screening = score_to_use >= criteria.pass_threshold
        result.recommended_for_shortlist = score_to_use >= criteria.shortlist_threshold
    
    def _generate_insights(self, result: ScreeningResult, candidate: CandidateProfile):
        """Generate insights about the candidate"""
        
        strengths = []
        concerns = []
        
        # Skill insights
        if result.required_skills_score >= 80:
            strengths.append("Strong technical skills match")
        elif result.required_skills_score < 50:
            concerns.append("Missing several required skills")
        
        if result.preferred_skills_score >= 60:
            strengths.append("Good preferred skills coverage")
        
        # Experience insights
        if result.experience_level_match == "exceeds":
            strengths.append("Highly experienced candidate")
        elif result.experience_level_match == "under":
            concerns.append("Below minimum experience requirement")
        
        # Location insights
        if result.location_match:
            strengths.append("Location compatible")
        else:
            concerns.append("Location may require relocation")
        
        # Specific skill gaps
        if result.missing_critical_skills:
            concerns.append(f"Missing critical skills: {', '.join(result.missing_critical_skills[:3])}")
        
        # Overall assessment
        if result.weighted_score >= 85:
            strengths.append("Excellent overall candidate")
        elif result.weighted_score >= 70:
            strengths.append("Good candidate match")
        elif result.weighted_score < 50:
            concerns.append("Significant gaps in requirements")
        
        result.strengths = strengths
        result.concerns = concerns
    
    def generate_screening_summary(self, results: List[ScreeningResult], 
                                 processing_time: float) -> ScreeningSummary:
        """Generate summary of all screening results"""
        
        if not results:
            return ScreeningSummary(
                total_candidates=0,
                passed_screening=0,
                shortlisted=0,
                rejected=0,
                average_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
                most_common_missing_skills=[],
                experience_distribution={},
                location_distribution={},
                processing_time_seconds=processing_time,
                error_count=0
            )
        
        # Basic counts
        total = len(results)
        passed = sum(1 for r in results if r.passes_screening)
        shortlisted = sum(1 for r in results if r.recommended_for_shortlist)
        rejected = total - passed
        
        # Score statistics
        scores = [r.weighted_score for r in results]
        avg_score = sum(scores) / len(scores)
        highest_score = max(scores)
        lowest_score = min(scores)
        
        # Common missing skills
        all_missing_skills = []
        for result in results:
            all_missing_skills.extend(result.missing_critical_skills)
        
        from collections import Counter
        missing_counter = Counter(all_missing_skills)
        most_common_missing = [skill for skill, count in missing_counter.most_common(5)]
        
        # Experience distribution
        exp_distribution = {}
        for result in results:
            level = result.experience_level_match
            exp_distribution[level] = exp_distribution.get(level, 0) + 1
        
        # Location distribution
        loc_distribution = {}
        for result in results:
            if result.candidate_location:
                # Extract city from location
                city = result.candidate_location.split(',')[0].strip()
                loc_distribution[city] = loc_distribution.get(city, 0) + 1
        
        return ScreeningSummary(
            total_candidates=total,
            passed_screening=passed,
            shortlisted=shortlisted,
            rejected=rejected,
            average_score=avg_score,
            highest_score=highest_score,
            lowest_score=lowest_score,
            most_common_missing_skills=most_common_missing,
            experience_distribution=exp_distribution,
            location_distribution=dict(list(loc_distribution.items())[:5]),
            processing_time_seconds=processing_time,
            error_count=0
        )