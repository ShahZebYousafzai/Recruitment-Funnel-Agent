# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    LLM_MODEL = "gpt-4o-mini-2024-07-18"
    EMBEDDING_MODEL = "text-embedding-ada-002"
    
    # Email Configuration
    EMAIL_HOST = os.getenv("EMAIL_HOST", "zebshah7851@gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")  # Your email address
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")  # App password
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AI Recruitment Team")
    
    # Email Templates Configuration
    EMAIL_SIGNATURE = os.getenv("EMAIL_SIGNATURE", """
Best regards,
{from_name}
AI Recruitment System

---
This is an automated message from our recruitment system.
If you have any questions, please reply to this email.
""")
    
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
    
    # Validation
    @classmethod
    def validate_email_config(cls):
        """Validate email configuration"""
        missing = []
        if not cls.EMAIL_HOST_USER:
            missing.append("EMAIL_HOST_USER")
        if not cls.EMAIL_HOST_PASSWORD:
            missing.append("EMAIL_HOST_PASSWORD")
        
        if missing:
            print(f"Warning: Missing email configuration: {', '.join(missing)}")
            print("Email sending will be disabled. Please set these environment variables:")
            for var in missing:
                print(f"  {var}=your_value")
            return False
        return True

settings = Settings()