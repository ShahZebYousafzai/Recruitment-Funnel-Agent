# 💼Recruitment Funnel Agent
## 🧠 Goal
Build an AI-powered multi-agent system that automates the recruitment process—from resume screening to interview scheduling and final candidate follow-up—reducing human overhead and bias.

## 🔧 Core Modules / Agents
### 1. Resume Screener Agent
Input: Uploaded resumes or LinkedIn profiles.


Tasks:


Extracts key information (skills, experience, education). ✅


Scores and ranks resumes based on job description fit. ✅


Filters out unqualified candidates. ✅


Tech: LLM (for extraction), keyword similarity, embedding-based matching.


### 2. Candidate Interview Agent
Input: Qualified candidate info.


Tasks:


Sends introductory emails. ✅


Conducts pre-screening Q&A via chat/email.


Flags responses needing human review.


Tech: Email API (Gmail/Outlook), LLM for Q&A, memory to track history.



### 3. Scheduler Agent
Input: Interviewer and candidate availability.


Tasks:


Integrates with calendar APIs.


Proposes slots.


Sends invites and reminders.


Tech: Google Calendar API / Outlook API, datetime management.



### 4. Feedback Aggregator Agent
Input: Interview notes or ratings from human panel.


Tasks:


Summarizes feedback.


Classifies candidate as move forward, hold, or reject.


Tech: Form input + LLM summarization + scoring rules.



### 5. Follow-Up Agent
Input: Candidate status.


Tasks:


Sends rejection, offer, or next-step emails.


Updates HR system or dashboard.


Tech: Email templates + trigger-based actions.


## 🧰 Tech Stack Suggestions
* LangChain
* OpenAI / HuggingFace
* Pinecone / Chroma / Weaviate

## 🚀 Example User Flow
HR uploads job description.


System invites candidates to submit resumes.


Screener Agent evaluates and filters candidates.


Qualified candidates go through automated Q&A.


Scheduler Agent arranges interviews.


Post-interview, Feedback Agent summarizes decisions.


Follow-Up Agent communicates outcomes.

## Next Steps (we'll implement these incrementally):

* Email configuration (SMTP settings, credentials) ✅
* Actual email sending functionality ✅
* Screening questions generation and sending
* Response processing and analysis
* Conversation tracking and memory
