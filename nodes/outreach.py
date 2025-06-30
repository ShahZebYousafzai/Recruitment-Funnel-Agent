import time
import uuid
from datetime import datetime
from typing import Dict, List, Any
from models.outreach import OutreachState, CandidateEmail, EmailStatus, OutreachTemplate
from agents.outreach import OutreachAgent
from utils import safe_add_message
import logging


def initialize_outreach(state: OutreachState) -> OutreachState:
    """Initialize the outreach process"""

    print("📧 Initializing Candidate Outreach...")

    # Ensure all required fields exist
    if "emails_to_send" not in state:
        state["emails_to_send"] = []
    if "sent_emails" not in state:
        state["sent_emails"] = []
    if "outreach_metrics" not in state:
        state["outreach_metrics"] = {}
    if "email_statuses" not in state:
        state["email_statuses"] = {}
    if "processing_errors" not in state:
        state["processing_errors"] = []
    if "messages" not in state:
        state["messages"] = []

    # Initialize campaign
    campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
    state["campaign_id"] = campaign_id
    state["campaign_status"] = "preparing"

    # Set processing status
    state["current_email_index"] = 0
    state["total_emails"] = len(state["shortlisted_candidates"])
    state["outreach_complete"] = False

    # Get outreach configuration
    outreach_config = state.get("outreach_config", {})
    template_id = state.get("email_template_id", "initial_outreach_v1")

    print(f"📊 Campaign: {campaign_id}")
    print(f"👥 Shortlisted candidates: {state['total_emails']}")
    print(f"📧 Template: {template_id}")

    # Validate shortlisted candidates
    if state["total_emails"] == 0:
        print("⚠️ No shortlisted candidates found for outreach")
        state["outreach_complete"] = True
        return state

    # Add initialization message
    init_message = {
        "type": "system",
        "content": f"📧 Starting outreach campaign for {state['total_emails']} shortlisted candidates",
    }
    state = safe_add_message(state, init_message)

    print(f"✅ Outreach initialization complete")

    return state


def prepare_emails(state: OutreachState) -> OutreachState:
    """Prepare personalized emails for all shortlisted candidates"""

    print("📝 Preparing personalized emails...")

    # Initialize outreach agent
    agent = OutreachAgent()

    # Get configuration
    job_requirements = state["job_requirements"]
    outreach_config = state.get("outreach_config", {})
    template_id = state.get("email_template_id", "initial_outreach_v1")

    # Default recruiter information
    default_recruiter = {
        "name": outreach_config.get("recruiter_name", "Sarah Johnson"),
        "title": outreach_config.get("recruiter_title", "Senior Technical Recruiter"),
        "email": outreach_config.get("recruiter_email", "sarah.johnson@company.com"),
        "phone": outreach_config.get("recruiter_phone", "+1-555-0123"),
        "company_name": outreach_config.get("company_name", "TechCorp Inc."),
    }

    # Get template
    template = agent.templates.get(template_id)
    if not template:
        error_msg = f"Template {template_id} not found"
        state["processing_errors"].append(error_msg)
        print(f"❌ {error_msg}")
        state["outreach_complete"] = True
        return state

    print(f"📧 Using template: {template.name}")
    print(f"👤 Recruiter: {default_recruiter['name']} ({default_recruiter['email']})")

    # Prepare emails for each candidate
    emails_to_send = []
    processing_errors = []

    for i, candidate in enumerate(state["shortlisted_candidates"]):
        try:
            candidate_name = candidate.get("name", "Unknown")
            candidate_email = candidate.get("email", "")

            print(
                f"  📝 [{i+1}/{len(state['shortlisted_candidates'])}] Preparing email for {candidate_name}"
            )

            if not candidate_email:
                error_msg = f"No email address for candidate {candidate_name}"
                processing_errors.append(error_msg)
                print(f"    ⚠️ {error_msg}")
                continue

            # Personalize email
            personalized_email = agent.personalize_email(
                template=template,
                candidate_data=candidate,
                job_data=job_requirements,
                recruiter_data=default_recruiter,
            )

            # Convert to dict for state storage
            email_dict = personalized_email.model_dump()
            emails_to_send.append(email_dict)

            print(
                f"    ✅ Email prepared: {len(personalized_email.subject)} chars subject, {len(personalized_email.body)} chars body"
            )

        except Exception as e:
            error_msg = f"Error preparing email for {candidate.get('name', 'Unknown')}: {str(e)}"
            processing_errors.append(error_msg)
            logging.error(f"Email preparation error: {e}", exc_info=True)
            print(f"    ❌ {error_msg}")

    # Update state
    state["emails_to_send"] = emails_to_send
    state["processing_errors"] = processing_errors
    state["total_emails"] = len(emails_to_send)

    print(f"✅ Email preparation complete!")
    print(f"   📧 {len(emails_to_send)} emails ready to send")
    print(f"   ❌ {len(processing_errors)} preparation errors")

    if len(emails_to_send) == 0:
        print("⚠️ No emails prepared successfully")
        state["outreach_complete"] = True

    return state


def send_outreach_emails(state: OutreachState) -> OutreachState:
    """Send all prepared emails to candidates"""

    print("📤 Sending outreach emails...")

    # Initialize outreach agent
    agent = OutreachAgent()

    # Get configuration
    outreach_config = state.get("outreach_config", {})
    stagger_seconds = outreach_config.get("stagger_seconds", 30)

    # Track processing time
    start_time = time.time()

    # Convert email dicts back to CandidateEmail objects
    emails_to_send = [
        CandidateEmail(**email_dict) for email_dict in state["emails_to_send"]
    ]

    print(f"📊 Sending {len(emails_to_send)} emails...")
    print(f"⏱️ Stagger time: {stagger_seconds} seconds between emails")

    # Send emails in batch
    batch_results = agent.send_batch_emails(emails_to_send, stagger_seconds)

    # Track email statuses
    email_statuses = {}
    sent_emails = []

    for email in emails_to_send:
        email_statuses[email.email_id] = email.status.value
        sent_emails.append(email.model_dump())

    # Calculate processing time
    processing_time = time.time() - start_time

    # Generate metrics
    metrics = agent.generate_outreach_metrics(emails_to_send, state["campaign_id"])

    # Update state
    state["sent_emails"] = sent_emails
    state["email_statuses"] = email_statuses
    state["campaign_status"] = "completed"
    state["outreach_complete"] = True

    # Update metrics
    state["outreach_metrics"] = {
        "campaign_id": state["campaign_id"],
        "total_emails": metrics.total_emails,
        "emails_sent": metrics.emails_sent,
        "emails_delivered": metrics.emails_delivered,
        "emails_failed": metrics.emails_failed,
        "delivery_rate": metrics.delivery_rate,
        "processing_time_seconds": processing_time,
        "batch_results": batch_results,
        "metrics": metrics.model_dump(),
    }

    # Add completion message
    completion_message = {
        "type": "system",
        "content": f"📧 Outreach complete: {metrics.emails_sent}/{metrics.total_emails} emails sent successfully",
    }
    state = safe_add_message(state, completion_message)

    print(f"✅ Email sending completed!")
    print(f"   📊 Sent: {metrics.emails_sent}/{metrics.total_emails}")
    print(f"   📈 Delivery rate: {metrics.delivery_rate:.1f}%")
    print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")

    return state


def track_email_responses(state: OutreachState) -> OutreachState:
    """Track and process email responses (placeholder for webhook integration)"""

    print("📊 Setting up response tracking...")

    # In a real implementation, this would:
    # 1. Set up webhooks for email opens, clicks, replies
    # 2. Parse incoming responses
    # 3. Categorize responses (interested, not interested, questions)
    # 4. Update candidate statuses
    # 5. Trigger follow-up actions

    # For now, simulate some responses for demo
    import random

    sent_emails = [CandidateEmail(**email_dict) for email_dict in state["sent_emails"]]

    # Simulate response tracking
    for email in sent_emails:
        # Simulate email opens (60% open rate)
        if random.random() < 0.6:
            email.status = EmailStatus.OPENED
            email.opened_at = datetime.now()

        # Simulate replies (15% reply rate)
        if email.status == EmailStatus.OPENED and random.random() < 0.25:
            email.status = EmailStatus.REPLIED
            email.replied_at = datetime.now()
            email.response_received = True

            # Categorize response type
            response_types = ["interested", "not_interested", "questions"]
            weights = [
                0.6,
                0.2,
                0.2,
            ]  # 60% interested, 20% not interested, 20% questions
            email.response_type = random.choices(response_types, weights=weights)[0]

            if email.response_type == "interested":
                email.response_content = "I'm very interested in this opportunity. When can we schedule a call?"
            elif email.response_type == "questions":
                email.response_content = "This sounds interesting. Can you tell me more about the team and tech stack?"
            else:
                email.response_content = "Thank you for reaching out, but I'm not looking for new opportunities at this time."

    # Update state with simulated responses
    state["sent_emails"] = [email.model_dump() for email in sent_emails]

    # Update email statuses
    for email in sent_emails:
        state["email_statuses"][email.email_id] = email.status.value

    print(f"📊 Response tracking initialized")
    print(f"   📧 Simulated opens and replies for demo")
    print(f"   🔗 In production: Webhook integration required")

    return state


def check_outreach_completion(state: OutreachState) -> str:
    """Check if outreach is complete"""
    if state.get("outreach_complete", False):
        return "outreach_complete"
    else:
        return "continue_outreach"


def finalize_outreach(state: OutreachState) -> OutreachState:
    """Finalize outreach and generate detailed report"""

    print("\n📊 Finalizing Outreach Results...")

    # Convert sent emails back to objects for analysis
    sent_emails = [CandidateEmail(**email_dict) for email_dict in state["sent_emails"]]

    # Initialize outreach agent for metrics
    agent = OutreachAgent()

    # Calculate processing time
    processing_time = state["outreach_metrics"].get("processing_time_seconds", 0)

    # Generate summary
    summary = agent.generate_outreach_summary(
        emails=sent_emails,
        campaign_id=state["campaign_id"],
        job_title=state["job_requirements"].get("job_title", "Unknown Position"),
        processing_time=processing_time,
    )

    # Update metrics with summary
    state["outreach_metrics"]["summary"] = summary.model_dump()

    # Display detailed results
    print(f"\n{'='*60}")
    print(f"📧 OUTREACH STAGE COMPLETE")
    print(f"{'='*60}")

    print(f"📊 Campaign Summary:")
    print(f"   Campaign ID: {state['campaign_id']}")
    print(f"   Job Title: {summary.job_title}")
    print(f"   Total Candidates: {summary.total_candidates}")
    print(f"   Emails Sent: {summary.emails_sent}")
    print(f"   Successful Deliveries: {summary.successful_deliveries}")
    print(f"   Failed Deliveries: {summary.failed_deliveries}")
    print(f"   Processing Time: {summary.processing_time_seconds:.2f} seconds")

    print(f"\n📈 Engagement Metrics:")
    print(f"   Emails Opened: {summary.emails_opened}")
    print(f"   Emails Replied: {summary.emails_replied}")
    print(f"   Response Rate: {summary.response_rate:.1f}%")

    print(f"\n📋 Response Breakdown:")
    print(f"   😊 Interested: {summary.interested_candidates}")
    print(f"   ❓ Have Questions: {summary.questions_candidates}")
    print(f"   😐 Not Interested: {summary.not_interested_candidates}")
    print(f"   📭 No Response: {summary.no_response_candidates}")

    print(f"\n🎯 Next Steps:")
    print(f"   📞 Candidates for Interview: {summary.candidates_for_interview}")
    print(f"   📬 Follow-ups Needed: {summary.follow_ups_needed}")

    # Show individual responses
    if summary.emails_replied > 0:
        print(f"\n📩 Recent Responses:")

        responded_emails = [email for email in sent_emails if email.response_received]
        for i, email in enumerate(responded_emails[:5]):  # Show first 5 responses
            status_emoji = (
                "😊"
                if email.response_type == "interested"
                else "❓" if email.response_type == "questions" else "😐"
            )
            print(f"   {status_emoji} {email.candidate_name}: {email.response_type}")
            if email.response_content:
                preview = (
                    email.response_content[:100] + "..."
                    if len(email.response_content) > 100
                    else email.response_content
                )
                print(f'      "{preview}"')

    # Show any errors
    if state.get("processing_errors"):
        print(f"\n⚠️ Processing Issues ({len(state['processing_errors'])}):")
        for error in state["processing_errors"][:3]:
            print(f"   • {error}")

    # Add final summary message
    final_message = {
        "type": "system",
        "content": f"📧 Outreach finalized: {summary.candidates_for_interview} candidates ready for interviews",
    }
    state = safe_add_message(state, final_message)

    print(f"\n🎉 Outreach stage completed successfully!")
    print(
        f"📞 {summary.candidates_for_interview} candidates ready for interview scheduling"
    )
    print(f"📬 {summary.follow_ups_needed} candidates need follow-up")

    return state


def generate_outreach_report(state: OutreachState) -> Dict[str, Any]:
    """Generate a detailed outreach report"""

    sent_emails = [CandidateEmail(**email_dict) for email_dict in state["sent_emails"]]
    metrics = state["outreach_metrics"]
    summary = metrics.get("summary", {})

    # Detailed email analysis
    email_details = []
    for email in sent_emails:
        email_details.append(
            {
                "candidate_name": email.candidate_name,
                "candidate_email": email.candidate_email,
                "email_status": email.status.value,
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "opened_at": email.opened_at.isoformat() if email.opened_at else None,
                "replied_at": (
                    email.replied_at.isoformat() if email.replied_at else None
                ),
                "response_type": email.response_type,
                "response_received": email.response_received,
                "next_action": _determine_next_action(email),
            }
        )

    # Sort by priority (responses first, then opens, then sent)
    email_details.sort(
        key=lambda x: (
            x["response_received"],
            x["opened_at"] is not None,
            x["sent_at"] is not None,
        ),
        reverse=True,
    )

    report = {
        "stage": "Automated Outreach",
        "generated_at": datetime.now().isoformat(),
        "campaign_id": state["campaign_id"],
        "summary": {
            "total_candidates": summary.get("total_candidates", 0),
            "emails_sent": summary.get("emails_sent", 0),
            "delivery_rate": f"{metrics.get('delivery_rate', 0):.1f}%",
            "open_rate": f"{summary.get('emails_opened', 0) / max(summary.get('successful_deliveries', 1), 1) * 100:.1f}%",
            "response_rate": f"{summary.get('response_rate', 0):.1f}%",
            "processing_time": f"{summary.get('processing_time_seconds', 0):.2f} seconds",
        },
        "responses": {
            "interested": summary.get("interested_candidates", 0),
            "questions": summary.get("questions_candidates", 0),
            "not_interested": summary.get("not_interested_candidates", 0),
            "no_response": summary.get("no_response_candidates", 0),
        },
        "next_steps": {
            "interview_ready": summary.get("candidates_for_interview", 0),
            "follow_up_needed": summary.get("follow_ups_needed", 0),
            "priority_candidates": [
                email
                for email in email_details
                if email["response_type"] in ["interested", "questions"]
            ][:10],
        },
        "email_details": email_details,
        "recommendations": _generate_outreach_recommendations(state),
        "errors": state.get("processing_errors", []),
    }

    return report


def _determine_next_action(email: CandidateEmail) -> str:
    """Determine next action for a candidate based on email status"""

    if email.response_type == "interested":
        return "Schedule interview immediately"
    elif email.response_type == "questions":
        return "Respond to questions and schedule call"
    elif email.response_type == "not_interested":
        return "Add to future opportunities list"
    elif email.status == EmailStatus.OPENED:
        return "Follow up in 3-5 days"
    elif email.status == EmailStatus.DELIVERED:
        return "Follow up in 1 week"
    elif email.status == EmailStatus.FAILED:
        return "Find alternative contact method"
    else:
        return "Monitor delivery status"


def _generate_outreach_recommendations(state: OutreachState) -> List[str]:
    """Generate recommendations based on outreach results"""

    recommendations = []
    metrics = state["outreach_metrics"]
    summary = metrics.get("summary", {})

    # Delivery rate analysis
    delivery_rate = metrics.get("delivery_rate", 0)
    if delivery_rate < 90:
        recommendations.append(
            "Review email addresses for accuracy - low delivery rate detected"
        )

    # Response rate analysis
    response_rate = summary.get("response_rate", 0)
    if response_rate < 10:
        recommendations.append(
            "Consider improving email personalization or subject lines"
        )
    elif response_rate > 25:
        recommendations.append(
            "Excellent response rate - consider using this template for future campaigns"
        )

    # Interest level analysis
    interested = summary.get("interested_candidates", 0)
    total_responses = summary.get("emails_replied", 1)
    interest_rate = interested / total_responses * 100 if total_responses > 0 else 0

    if interest_rate > 60:
        recommendations.append(
            "High interest rate - prioritize quick interview scheduling"
        )
    elif interest_rate < 30:
        recommendations.append(
            "Low interest rate - review job positioning and requirements"
        )

    # Follow-up recommendations
    no_response = summary.get("no_response_candidates", 0)
    if no_response > 0:
        recommendations.append(
            f"Schedule follow-up campaign for {no_response} non-responders"
        )

    # Processing efficiency
    errors = len(state.get("processing_errors", []))
    if errors > 0:
        recommendations.append(
            "Review candidate data quality to reduce processing errors"
        )

    if not recommendations:
        recommendations.append(
            "Outreach campaign completed successfully with good results"
        )

    return recommendations
