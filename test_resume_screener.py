# test_resume_screener.py
import os
from models.job_description import JobDescription
from agents.resume_screener import ResumeScreenerAgent

def test_resume_screener():
    """Test the Resume Screener Agent with sample data"""
    
    # Create a sample job description
    job_description = JobDescription(
        title="Senior Python Developer",
        company="Tech Solutions Inc.",
        description="""
        We are looking for a Senior Python Developer with strong experience in web development,
        machine learning, and cloud technologies. The ideal candidate should have experience
        with Django, Flask, AWS, and data science libraries like Pandas and Scikit-learn.
        """,
        required_skills=[
            "Python", "Django", "Flask", "AWS", "Machine Learning", 
            "Pandas", "Scikit-learn", "REST API", "PostgreSQL"
        ],
        preferred_skills=["Docker", "Kubernetes", "TensorFlow", "React"],
        min_experience=3.0,
        education_requirements=["Bachelor's degree in Computer Science or related field"],
        location="Remote",
        job_type="full-time"
    )
    
    # Initialize the Resume Screener Agent
    screener_agent = ResumeScreenerAgent()
    
    # Test with a sample resume (you would replace this with actual file path)
    sample_resume_text = """
    John Doe
    Senior Software Engineer
    Email: john.doe@email.com
    Phone: (555) 123-4567
    
    EXPERIENCE:
    Senior Software Engineer at TechCorp (2019-2024)
    - Developed web applications using Python, Django, and Flask
    - Built machine learning models using Scikit-learn and Pandas
    - Deployed applications on AWS using Docker containers
    - Led a team of 5 developers in agile environment
    - Built REST APIs serving 1M+ requests per day
    
    Software Engineer at StartupXYZ (2017-2019)
    - Full-stack development using Python and React
    - Database design and optimization with PostgreSQL
    - Implemented CI/CD pipelines using Jenkins
    
    EDUCATION:
    Bachelor of Science in Computer Science
    University of Technology (2013-2017)
    
    SKILLS:
    Python, Django, Flask, AWS, Docker, Machine Learning, Pandas, 
    Scikit-learn, PostgreSQL, REST API, React, Git, Agile, Scrum
    """
    
    # Save sample resume to a temp file for testing
    temp_resume_path = "temp_resume.txt"
    with open(temp_resume_path, 'w') as f:
        f.write(sample_resume_text)
    
    try:
        # Test the screening process
        input_data = {
            'job_description': job_description,
            'resume_file_path': temp_resume_path,
            'candidate_info': {
                'name': 'John Doe',
                'email': 'john.doe@email.com'
            }
        }
        
        result = screener_agent.execute(input_data)
        
        # Print results
        print("=== RESUME SCREENING RESULTS ===")
        print(f"Candidate: {result['candidate'].name}")
        print(f"Email: {result['candidate'].email}")
        print(f"Status: {result['candidate'].status}")
        print(f"Screening Score: {result['score']:.2f}")
        print(f"Qualified: {'Yes' if result['qualified'] else 'No'}")
        print(f"Experience Years: {result['candidate'].experience_years}")
        print(f"Skills Found: {', '.join(result['candidate'].skills[:10])}...")  # Show first 10 skills
        print(f"Feedback: {result['feedback']}")
        print("\n=== DETAILED ANALYSIS ===")
        print(f"Education Level: {result['analysis'].education_level}")
        print(f"Previous Companies: {', '.join(result['analysis'].previous_companies)}")
        print(f"Key Achievements: {result['analysis'].key_achievements[:3]}...")  # Show first 3
        print(f"Summary: {result['analysis'].summary}")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_resume_path):
            os.remove(temp_resume_path)

def test_batch_screening():
    """Test batch screening functionality"""
    
    # Create job description
    job_description = JobDescription(
        title="Data Scientist",
        company="AI Research Labs",
        description="""
        Looking for a Data Scientist with strong Python skills, machine learning experience,
        and expertise in statistical analysis. Experience with TensorFlow, PyTorch, and
        cloud platforms is preferred.
        """,
        required_skills=["Python", "Machine Learning", "Statistics", "Data Analysis"],
        preferred_skills=["TensorFlow", "PyTorch", "AWS", "Jupyter"],
        min_experience=2.0
    )
    
    # Create sample resumes
    resumes = [
        {
            "filename": "candidate1_highly_qualified.txt",
            "content": """
            Dr. Sarah Chen - Senior Data Scientist
            sarah.chen@email.com | (555) 123-4567 | LinkedIn: /in/sarahchen
            San Francisco, CA
            
            PROFESSIONAL SUMMARY:
            Accomplished Data Scientist with 6+ years of experience building production ML systems.
            PhD in Statistics with expertise in deep learning, statistical modeling, and MLOps.
            Led data science teams and delivered $10M+ business impact through AI/ML solutions.
            
            EXPERIENCE:
            Senior Data Scientist | Netflix (2022-2024)
            * Built recommendation systems serving 230M+ users using TensorFlow and PyTorch
            * Developed deep learning models for content personalization with 25% engagement improvement
            * Led cross-functional team of 8 engineers implementing MLOps pipelines on AWS
            * Published 3 research papers on recommender systems at top-tier conferences
            
            Data Scientist | Uber (2020-2022)
            * Created demand forecasting models using time series analysis and LSTM networks
            * Implemented A/B testing framework reducing experimentation time by 40%
            * Built real-time fraud detection system processing 1M+ transactions daily
            * Collaborated with product teams to integrate ML models into mobile applications
            
            Junior Data Scientist | Airbnb (2018-2020)
            * Developed pricing optimization models using gradient boosting and neural networks
            * Performed statistical analysis and hypothesis testing for product features
            * Built data pipelines using Python, Spark, and SQL processing TB-scale datasets
            * Created interactive dashboards using Tableau and Plotly for stakeholder reporting
            
            EDUCATION:
            PhD in Statistics | Stanford University (2018)
            * Dissertation: "Deep Learning Approaches for Time Series Forecasting"
            * Relevant Coursework: Machine Learning, Bayesian Statistics, Optimization
            
            Master of Science in Data Science | UC Berkeley (2015)
            Bachelor of Science in Mathematics | MIT (2013)
            
            TECHNICAL SKILLS:
            Programming: Python, R, SQL, Scala, Java
            ML/DL Frameworks: TensorFlow, PyTorch, Scikit-learn, XGBoost, LightGBM
            Cloud Platforms: AWS (SageMaker, EC2, S3, Lambda), GCP, Azure
            Big Data: Apache Spark, Hadoop, Kafka, Airflow
            Databases: PostgreSQL, MongoDB, Cassandra, Redis
            Visualization: Tableau, Plotly, Matplotlib, Seaborn, D3.js
            MLOps: Docker, Kubernetes, MLflow, Kubeflow, Jenkins
            Statistics: Hypothesis Testing, Bayesian Analysis, A/B Testing, Causal Inference
            
            ACHIEVEMENTS:
            * Led ML project that increased customer retention by 30% ($5M annual impact)
            * Published 8 peer-reviewed papers in machine learning and statistics journals
            * Speaker at PyData, Strata Data Conference, and NeurIPS workshops
            * Mentor for Google Summer of Code and Kaggle competitions
            * Patent holder for "Real-time Anomaly Detection in Streaming Data"
            """
        },
        {
            "filename": "candidate2_qualified.txt", 
            "content": """
            Michael Rodriguez - Data Scientist
            m.rodriguez@email.com | (555) 987-6543
            Austin, TX
            
            PROFESSIONAL SUMMARY:
            Data Scientist with 3.5 years of experience in machine learning and analytics.
            Strong background in Python, statistical modeling, and data visualization.
            Experience working with large datasets and deploying models in production.
            
            EXPERIENCE:
            Data Scientist | Dell Technologies (2021-2024)
            * Developed predictive models for supply chain optimization using Python and Scikit-learn
            * Built customer churn prediction model achieving 85% accuracy with Random Forest
            * Created automated reporting dashboards using Tableau and Python
            * Collaborated with business teams to translate requirements into analytical solutions
            * Performed exploratory data analysis on customer behavior datasets (500K+ records)
            
            Business Analyst | Capital One (2020-2021)
            * Conducted statistical analysis for credit risk assessment using R and SQL
            * Built linear regression models for loan default prediction
            * Created data visualizations and presented insights to senior management
            * Automated daily reporting processes reducing manual work by 60%
            
            Data Analyst Intern | IBM (Summer 2020)
            * Analyzed customer data using Python Pandas and NumPy
            * Assisted in building machine learning prototypes for text classification
            * Created data quality checks and validation scripts
            * Participated in agile development processes and code reviews
            
            EDUCATION:
            Master of Science in Data Analytics | University of Texas at Austin (2020)
            * Capstone Project: "Predicting Customer Lifetime Value using ML Techniques"
            * GPA: 3.8/4.0
            
            Bachelor of Science in Computer Science | UT Austin (2018)
            * Minor in Statistics
            * Relevant Coursework: Machine Learning, Database Systems, Algorithms
            
            TECHNICAL SKILLS:
            Languages: Python, R, SQL, Java
            ML Libraries: Scikit-learn, Pandas, NumPy, Matplotlib, Seaborn
            Databases: MySQL, PostgreSQL, MongoDB
            Tools: Jupyter, Git, Tableau, Excel, SPSS
            Cloud: AWS (basic), Azure (basic)
            Statistics: Regression Analysis, Hypothesis Testing, Time Series Analysis
            
            PROJECTS:
            * E-commerce Recommendation System: Built collaborative filtering model using Python
            * Stock Price Prediction: Implemented LSTM model for time series forecasting
            * Customer Segmentation: Applied K-means clustering on retail dataset
            * Sentiment Analysis: Developed NLP model for social media data classification
            
            CERTIFICATIONS:
            * AWS Certified Cloud Practitioner (2023)
            * Google Analytics Individual Qualification (2022)
            * Tableau Desktop Specialist (2021)
            """
        },
        {
            "filename": "candidate3_entry_level_qualified.txt",
            "content": """
            Emma Thompson - Junior Data Scientist
            emma.thompson@email.com | (555) 456-7890
            Chicago, IL
            
            PROFESSIONAL SUMMARY:
            Recent graduate with Master's in Data Science and 1 year of professional experience.
            Strong foundation in machine learning, Python programming, and statistical analysis.
            Passionate about applying data science to solve real-world business problems.
            
            EXPERIENCE:
            Junior Data Scientist | Accenture (2023-2024)
            * Developed machine learning models for client projects using Python and Scikit-learn
            * Performed data cleaning and preprocessing on datasets with 100K+ records
            * Created data visualizations and reports for stakeholder presentations
            * Collaborated with senior data scientists on model validation and testing
            * Gained experience with cloud platforms (AWS) and version control (Git)
            
            Data Science Intern | JPMorgan Chase (Summer 2023)
            * Built predictive models for fraud detection using logistic regression
            * Conducted exploratory data analysis on financial transaction data
            * Created automated data pipelines using Python and SQL
            * Presented findings to management team and received excellent feedback
            
            Research Assistant | Northwestern University (2022-2023)
            * Assisted professor with machine learning research on healthcare data
            * Implemented deep learning models using TensorFlow for medical image analysis
            * Performed statistical analysis and hypothesis testing on clinical trial data
            * Co-authored research paper submitted to IEEE conference
            
            EDUCATION:
            Master of Science in Data Science | Northwestern University (2023)
            * GPA: 3.9/4.0, Summa Cum Laude
            * Thesis: "Ensemble Methods for Medical Diagnosis Prediction"
            * Relevant Coursework: Machine Learning, Deep Learning, Statistical Inference, Big Data Analytics
            
            Bachelor of Science in Mathematics | University of Illinois (2021)
            * Minor in Computer Science
            * GPA: 3.7/4.0, Dean's List (4 semesters)
            
            TECHNICAL SKILLS:
            Programming: Python, R, SQL, MATLAB
            ML/DL: Scikit-learn, TensorFlow, Keras, XGBoost
            Data Analysis: Pandas, NumPy, SciPy, Statsmodels
            Visualization: Matplotlib, Seaborn, Plotly, Tableau
            Databases: PostgreSQL, MySQL, SQLite
            Tools: Jupyter Notebooks, Git, Docker (basic)
            Cloud: AWS (EC2, S3), Google Colab
            Statistics: Regression, ANOVA, Bayesian Methods, Time Series
            
            PROJECTS:
            * COVID-19 Spread Prediction: Built LSTM model achieving 92% accuracy
            * Customer Churn Analysis: Developed ensemble model with 88% precision
            * Movie Recommendation System: Implemented collaborative filtering algorithm
            * Housing Price Prediction: Created regression model using feature engineering
            * Social Media Sentiment Analysis: Built NLP pipeline with 85% accuracy
            
            ACHIEVEMENTS:
            * Winner of Northwestern University Data Science Competition (2023)
            * Published research paper: "ML Approaches for Early Disease Detection"
            * Kaggle Competition: Top 10% in "House Prices Prediction Challenge"
            * Teaching Assistant for "Introduction to Machine Learning" course
            
            CERTIFICATIONS:
            * Google Data Analytics Professional Certificate (2022)
            * Microsoft Azure AI Fundamentals (2023)
            * Coursera Machine Learning Specialization (Andrew Ng) (2022)
            """
        },
        {
            "filename": "candidate4_unqualified_wrong_field.txt",
            "content": """
            David Wilson - Marketing Manager
            david.wilson@email.com | (555) 321-9876
            New York, NY
            
            PROFESSIONAL SUMMARY:
            Experienced Marketing Manager with 5 years in digital marketing and brand management.
            Strong background in campaign development, social media strategy, and customer acquisition.
            Proven track record of increasing brand awareness and driving sales growth.
            
            EXPERIENCE:
            Senior Marketing Manager | Coca-Cola (2022-2024)
            * Led digital marketing campaigns with budgets exceeding $2M annually
            * Developed social media strategies increasing follower engagement by 40%
            * Managed cross-functional teams of 6 marketing professionals
            * Analyzed campaign performance using Google Analytics and Facebook Insights
            * Collaborated with creative agencies for brand campaign development
            
            Marketing Specialist | Nike (2020-2022)
            * Created content marketing strategies for product launches
            * Managed influencer partnerships and sponsorship deals
            * Conducted market research and competitor analysis
            * Developed email marketing campaigns with 25% open rates
            * Coordinated trade show participation and event marketing
            
            Junior Marketing Associate | Starbucks (2019-2020)
            * Assisted in developing promotional campaigns for seasonal products
            * Managed social media accounts and customer engagement
            * Created marketing materials and presentations for internal use
            * Supported market research initiatives and customer surveys
            
            EDUCATION:
            MBA in Marketing | NYU Stern School of Business (2019)
            * Concentration: Digital Marketing and Consumer Behavior
            * GPA: 3.6/4.0
            
            Bachelor of Arts in Communications | University of Southern California (2017)
            * Minor in Business Administration
            * Captain of University Debate Team
            
            SKILLS:
            Marketing: Digital Marketing, Brand Management, Content Strategy, SEO/SEM
            Analytics: Google Analytics, Facebook Analytics, Adobe Analytics
            Tools: HubSpot, Salesforce, Mailchimp, Hootsuite, Canva
            Software: Microsoft Office Suite, Adobe Creative Suite, Slack
            Languages: English (Native), Spanish (Fluent), French (Conversational)
            
            ACHIEVEMENTS:
            * Increased brand awareness by 35% through innovative social media campaigns
            * Led campaign that generated $5M in additional revenue
            * Recipient of "Marketing Excellence Award" at Nike (2021)
            * Featured speaker at Digital Marketing Conference 2023
            * Managed successful product launch reaching 2M customers in first month
            
            CERTIFICATIONS:
            * Google Ads Certification (2023)
            * Facebook Blueprint Certification (2022)
            * HubSpot Content Marketing Certification (2021)
            * Google Analytics Individual Qualification (2020)
            """
        },
        {
            "filename": "candidate5_partially_qualified.txt",
            "content": """
            Jennifer Lee - Business Intelligence Analyst
            jennifer.lee@email.com | (555) 654-3210
            Seattle, WA
            
            PROFESSIONAL SUMMARY:
            Business Intelligence Analyst with 2.5 years of experience in data analysis and reporting.
            Skilled in SQL, Excel, and basic Python. Strong background in business analytics
            and data visualization. Looking to transition into data science role.
            
            EXPERIENCE:
            Senior BI Analyst | Microsoft (2022-2024)
            * Created executive dashboards and KPI reports using Power BI and Tableau
            * Performed data analysis on sales and customer data (1M+ records)
            * Automated reporting processes reducing manual work by 50%
            * Collaborated with business stakeholders to define metrics and requirements
            * Conducted ad-hoc analysis to support strategic business decisions
            
            Business Analyst | Amazon (2021-2022)
            * Analyzed customer behavior data to identify trends and patterns
            * Created SQL queries to extract data from large databases
            * Built Excel models for financial forecasting and budgeting
            * Supported A/B testing initiatives for website optimization
            * Presented insights to management team through data visualizations
            
            Data Analyst Intern | Tesla (Summer 2021)
            * Assisted in analyzing manufacturing data for quality improvement
            * Created basic statistical models using Excel and R
            * Performed data cleaning and validation on production datasets
            * Developed charts and graphs for operations reporting
            * Learned fundamental data analysis techniques and tools
            
            EDUCATION:
            Master of Business Administration | University of Washington (2021)
            * Concentration: Business Analytics
            * GPA: 3.5/4.0
            * Capstone: "Predictive Analytics for Customer Retention"
            
            Bachelor of Science in Economics | UCLA (2019)
            * Minor in Statistics
            * Relevant Coursework: Econometrics, Statistical Analysis, Business Statistics
            
            TECHNICAL SKILLS:
            Languages: SQL (Advanced), Python (Basic), R (Basic), VBA
            Analytics: Excel (Advanced), Power BI, Tableau, Google Analytics
            Databases: SQL Server, Oracle, MySQL
            Tools: Jupyter Notebooks (Basic), Git (Basic), SPSS
            Cloud: Azure (Basic knowledge)
            Statistics: Descriptive Statistics, Basic Regression, Hypothesis Testing
            
            PROJECTS:
            * Customer Segmentation Analysis: Used K-means clustering in Python
            * Sales Forecasting Model: Built time series model using Excel and basic R
            * Website Performance Analysis: Created dashboard tracking user behavior
            * Market Research Analysis: Performed statistical analysis on survey data
            
            RECENT LEARNING:
            * Currently taking online course: "Machine Learning with Python" (Coursera)
            * Completed: "Introduction to Data Science" (edX) - 2024
            * Self-studying: Scikit-learn and Pandas through online tutorials
            * Attending local Data Science meetups and workshops
            
            ACHIEVEMENTS:
            * Improved reporting efficiency by 40% through process automation
            * Identified $2M cost savings opportunity through data analysis
            * Recognized as "Analyst of the Quarter" at Microsoft (Q3 2023)
            * Led cross-departmental project improving data quality by 25%
            
            CERTIFICATIONS:
            * Microsoft Power BI Data Analyst Associate (2023)
            * Tableau Desktop Specialist (2022)
            * Google Analytics Individual Qualification (2021)
            * SQL Server Certification (2022)
            """
        }
    ]
    
    # Save sample resumes
    resume_files = []
    for resume in resumes:
        with open(resume["filename"], 'w') as f:
            f.write(resume["content"])
        resume_files.append(resume["filename"])
    
    try:
        # Initialize screener
        screener_agent = ResumeScreenerAgent()
        
        # Run batch screening
        results = screener_agent.batch_screen_resumes(job_description, resume_files)
        
        print("\n=== BATCH SCREENING RESULTS ===")
        for i, result in enumerate(results, 1):
            candidate = result['candidate']
            print(f"\n{i}. {candidate.name}")
            print(f"   Score: {result['score']:.2f}")
            print(f"   Status: {candidate.status}")
            print(f"   Experience: {candidate.experience_years} years")
            print(f"   Top Skills: {', '.join(candidate.skills[:5])}")
            print(f"   Feedback: {result['feedback']}")
            
    except Exception as e:
        print(f"Error during batch testing: {str(e)}")
    
    finally:
        # Clean up temp files
        for filename in resume_files:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == "__main__":
    print("Testing Resume Screener Agent...")
    print("="*50)
    
    # Test single resume screening
    test_resume_screener()
    
    # Test batch screening
    test_batch_screening()
    
    print("\n" + "="*50)
    print("Testing completed!")