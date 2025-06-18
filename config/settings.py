import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    LLM_MODEL = "gpt-4o-mini-2024-07-18"
    EMBEDDING_MODEL = "text-embedding-ada-002"
    
    # Resume Screening Configuration
    MIN_EXPERIENCE_YEARS = 0
    MAX_RESUMES_TO_PROCESS = 100
    SIMILARITY_THRESHOLD = 0.5
    
    # File Processing
    ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt']
    MAX_FILE_SIZE_MB = 5
    
    # Scoring Weights
    EXPERIENCE_WEIGHT = 0.3
    SKILLS_WEIGHT = 0.4
    EDUCATION_WEIGHT = 0.2
    KEYWORDS_WEIGHT = 0.1

settings = Settings()