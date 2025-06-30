import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from models.response import (
    ResponseManagementState, ResponseConfig, CandidateResponse, 
    ResponseType, FollowUpAction, InterviewSlot, InterviewType
)
from agents.response import ResponseManagementAgent
from utils import safe_add_message
import logging

def initialize_response_management(state: ResponseManagementState) -> ResponseManagementState:
    """Initialize the response management process"""
    
    print("📨 Initializing Response Management...")
    
    # Ensure all required fields exist
    if "incoming_responses" not in state:
        state["incoming_responses"] = []
    if "processed_responses" not in state:
        state["processed_responses"] = []
    if "analysis_results" not in state:
        state["analysis_results"] = []
    if "scheduled_interviews" not in state:
        state["scheduled_interviews"] = []
    if "follow_up_emails" not in state:
        state["follow_up_emails"] = []
    if "pending_actions" not in state:
        state["pending_actions"] = []
    if "response_metrics" not in state:
        state["response_metrics"] = {}
    if "processing_errors" not in state:
        state["processing_errors"] = []
    if "messages" not in state:
        state["messages"] = []
    
    # Get configuration
    config = ResponseConfig()
    if "response_config" in state:
        config_dict = state["response_config"]
        config = ResponseConfig(**config_dict)
    state["response_config"] = config.model_dump()
    
    # Simulate incoming responses (in real implementation, these would come from email webhooks)
    if not state["incoming_responses"]:
        state["incoming_responses"] = simulate_candidate_responses(state["sent_emails"])
    
    # Set processing status
    state["current_response_index"] = 0
    state["total_responses"] = len(state["incoming_responses"])
    state["processing_complete"] = False
    state["response_management_complete"] = False
    
    # Generate available interview slots
    state["available_interview_slots"] = generate_interview_slots().model_dump()
    
    print(f"📊 Response Management Initialized:")
    print(f"   📧 Responses to process: {state['total_responses']}")
    print(f"   📅 Available interview slots: {len(state['available_interview_slots'])}")
    print(f"   🤖 LLM Model: {config.llm_model}")
    
    # Add initialization message
    init_message = {
        "type": "system",
        "content": f"📨 Starting response management for {state['total_responses']} candidate responses"
    }
    state = safe_add_message(state, init_message)
    
    if state["total_responses"] == 0:
        print("⚠️ No responses found to process")
        state["processing_complete"] = True
        state["response_management_complete"] = True
    
    return state

def collect_candidate_responses(state: ResponseManagementState) -> ResponseManagementState:
    """Collect and validate incoming candidate responses"""
    
    print("📬 Collecting candidate responses...")
    
    # In real implementation, this would:
    # 1. Connect to email service (Gmail API, Outlook API, etc.)
    # 2. Fetch replies to sent recruitment emails
    # 3. Parse email content and metadata
    # 4. Match responses to original outreach emails
    
    # For now, we'll use simulated responses
    validated_responses = []
    
    for response in state["incoming_responses"]:
        try:
            # Validate response has required fields
            if all(key in response for key in ['content', 'from_email', 'subject']):
                validated_responses.append(response)
            else:
                error_msg = f"Invalid response format: missing required fields"
                state["processing_errors"].append(error_msg)
                print(f"   ⚠️ {error_msg}")
                
        except Exception as e:
            error_msg = f"Error validating response: {str(e)}"
            state["processing_errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
    
    state["incoming_responses"] = validated_responses
    state["total_responses"] = len(validated_responses)
    
    print(f"✅ Collected {len(validated_responses)} valid responses")
    
    return state

def analyze_responses_with_llm(state: ResponseManagementState) -> ResponseManagementState:
    """Analyze candidate responses using LLM"""
    
    print("🤖 Analyzing responses with LLM...")
    
    # Initialize response agent
    config = ResponseConfig(**state["response_config"])
    agent = ResponseManagementAgent(config=config)
    
    # Get job context
    job_context = state["job_requirements"]
    
    # Track processing time
    start_time = time.time()
    
    processed_responses = []
    analysis_results = []
    processing_errors = []
    
    for i, raw_response in enumerate(state["incoming_responses"]):
        try:
            print(f"  🔍 [{i+1}/{len(state['incoming_responses'])}] Analyzing response from {raw_response.get('from_email', 'Unknown')}")
            
            # Find corresponding email context
            email_context = find_email_context(raw_response, state["sent_emails"])
            
            # Process the response
            candidate_response = agent.process_candidate_response(
                raw_response=raw_response,
                email_context=email_context,
                job_context=job_context
            )
            
            # Convert to dict for state storage
            response_dict = candidate_response.model_dump()
            processed_responses.append(response_dict)
            
            # Show analysis results
            print(f"      📊 Type: {candidate_response.response_type}")
            print(f"      😊 Sentiment: {candidate_response.sentiment}")
            print(f"      🎯 Action: {candidate_response.follow_up_action}")
            print(f"      ⭐ Priority: {candidate_response.priority_level}")
            
            if candidate_response.questions:
                print(f"      ❓ Questions: {len(candidate_response.questions)}")
            
            if candidate_response.human_review_needed:
                print(f"      👤 Human review required")
            
            # Update progress
            state["current_response_index"] = i + 1
            
        except Exception as e:
            error_msg = f"Error analyzing response {i+1}: {str(e)}"
            processing_errors.append(error_msg)
            logging.error(f"Response analysis error: {e}", exc_info=True)
            print(f"    ❌ {error_msg}")
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Update state
    state["processed_responses"] = processed_responses
    state["processing_errors"].extend(processing_errors)
    
    # Generate metrics
    responses_objects = [CandidateResponse(**resp) for resp in processed_responses]
    metrics = agent.generate_response_metrics(responses_objects, "response_mgmt_001")
    metrics.avg_processing_time_seconds = processing_time / len(processed_responses) if processed_responses else 0
    
    state["response_metrics"] = metrics.model_dump()
    
    print(f"✅ LLM Analysis Complete!")
    print(f"   📊 Processed: {len(processed_responses)}/{len(state['incoming_responses'])}")
    print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
    print(f"   🤖 Auto-processed: {metrics.auto_processed}")
    print(f"   👤 Need review: {metrics.human_review_needed}")
    
    return state

def execute_follow_up_actions(state: ResponseManagementState) -> ResponseManagementState:
    """Execute follow-up actions based on response analysis"""
    
    print("⚡ Executing follow-up actions...")
    
    # Initialize agent
    config = ResponseConfig(**state["response_config"])
    agent = ResponseManagementAgent(config=config)
    
    # Get available interview slots
    available_slots = [InterviewSlot(**slot) for slot in state["available_interview_slots"]]
    
    follow_up_emails = []
    scheduled_interviews = []
    pending_actions = []
    
    for response_dict in state["processed_responses"]:
        response = CandidateResponse(**response_dict)
        
        try:
            print(f"  🎯 Processing action for {response.candidate_name}: {response.follow_up_action}")
            
            if response.follow_up_action == FollowUpAction.SCHEDULE_INTERVIEW:
                # Schedule interview
                if available_slots and response.interview_type:
                    # Find suitable slot
                    suitable_slot = find_suitable_interview_slot(
                        available_slots, response.interview_type, response.availability
                    )
                    
                    if suitable_slot:
                        # Schedule the interview
                        interviewer_details = {"email": "recruiter@company.com"}
                        interview = agent.schedule_interview(response, suitable_slot, interviewer_details)
                        scheduled_interviews.append(interview.model_dump())
                        
                        # Generate confirmation email
                        confirmation_email = agent.generate_interview_confirmation_email(interview)
                        confirmation_email["recipient"] = response.candidate_email
                        confirmation_email["response_id"] = response.response_id
                        follow_up_emails.append(confirmation_email)
                        
                        # Mark slot as used
                        available_slots.remove(suitable_slot)
                        
                        print(f"      📅 Interview scheduled for {interview.scheduled_time}")
                    else:
                        print(f"      ⚠️ No suitable interview slots available")
                        pending_actions.append({
                            "response_id": response.response_id,
                            "action": "find_interview_slot",
                            "reason": "No suitable slots available"
                        })
                
            elif response.follow_up_action in [FollowUpAction.ANSWER_QUESTIONS, FollowUpAction.SEND_INFO]:
                # Generate follow-up email
                if config.auto_respond_to_questions:
                    follow_up_email = agent.generate_follow_up_email(response)
                    follow_up_email["recipient"] = response.candidate_email
                    follow_up_email["response_id"] = response.response_id
                    follow_up_emails.append(follow_up_email)
                    
                    print(f"      📧 Follow-up email generated")
                else:
                    pending_actions.append({
                        "response_id": response.response_id,
                        "action": "manual_response",
                        "reason": "Auto-response disabled for questions"
                    })
            
            elif response.follow_up_action == FollowUpAction.ADD_TO_FUTURE_POOL:
                # Generate polite response for future opportunities
                future_email = agent.generate_follow_up_email(response)
                future_email["recipient"] = response.candidate_email
                future_email["response_id"] = response.response_id
                follow_up_emails.append(future_email)
                
                print(f"      📝 Added to future opportunities")
            
            elif response.follow_up_action == FollowUpAction.ESCALATE_TO_HUMAN:
                pending_actions.append({
                    "response_id": response.response_id,
                    "action": "human_review",
                    "reason": "Escalated for human review"
                })
                print(f"      👤 Escalated for human review")
            
            elif response.follow_up_action == FollowUpAction.NO_ACTION:
                print(f"      ✅ No action required")
            
        except Exception as e:
            error_msg = f"Error executing action for {response.candidate_name}: {str(e)}"
            state["processing_errors"].append(error_msg)
            logging.error(f"Action execution error: {e}", exc_info=True)
            print(f"      ❌ {error_msg}")
    
    # Update state
    state["follow_up_emails"] = follow_up_emails
    state["scheduled_interviews"] = scheduled_interviews
    state["pending_actions"] = pending_actions
    state["available_interview_slots"] = [slot.model_dump() for slot in available_slots]
    
    print(f"✅ Follow-up actions executed!")
    print(f"   📧 Follow-up emails generated: {len(follow_up_emails)}")
    print(f"   📅 Interviews scheduled: {len(scheduled_interviews)}")
    print(f"   ⏳ Actions pending: {len(pending_actions)}")
    
    return state

def send_follow_up_communications(state: ResponseManagementState) -> ResponseManagementState:
    """Send follow-up emails and communications"""
    
    print("📤 Sending follow-up communications...")
    
    # In real implementation, this would:
    # 1. Connect to email service
    # 2. Send follow-up emails
    # 3. Create calendar events for interviews
    # 4. Send SMS notifications if configured
    # 5. Update CRM/ATS systems
    
    sent_count = 0
    failed_count = 0
    
    for email in state["follow_up_emails"]:
        try:
            # Simulate email sending
            print(f"  📧 Sending to {email['recipient']}: {email['subject']}")
            
            # Mark as sent (simulate)
            time.sleep(0.5)  # Simulate processing time
            sent_count += 1
            
        except Exception as e:
            error_msg = f"Failed to send email to {email['recipient']}: {str(e)}"
            state["processing_errors"].append(error_msg)
            failed_count += 1
            print(f"    ❌ {error_msg}")
    
    # Create calendar events for scheduled interviews
    calendar_events_created = 0
    for interview_dict in state["scheduled_interviews"]:
        try:
            print(f"  📅 Creating calendar event for {interview_dict['candidate_name']}")
            # Simulate calendar event creation
            calendar_events_created += 1
            
        except Exception as e:
            error_msg = f"Failed to create calendar event: {str(e)}"
            state["processing_errors"].append(error_msg)
            print(f"    ❌ {error_msg}")
    
    print(f"✅ Communications sent!")
    print(f"   📧 Emails sent: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📅 Calendar events: {calendar_events_created}")
    
    return state

def finalize_response_management(state: ResponseManagementState) -> ResponseManagementState:
    """Finalize response management and generate summary"""
    
    print("\n📊 Finalizing Response Management...")
    
    # Mark as complete
    state["processing_complete"] = True
    state["response_management_complete"] = True
    
    # Get metrics
    metrics = state["response_metrics"]
    
    # Display detailed results
    print(f"\n{'='*60}")
    print(f"📨 RESPONSE MANAGEMENT COMPLETE")
    print(f"{'='*60}")
    
    print(f"📊 Processing Summary:")
    print(f"   Total Responses: {metrics['total_responses']}")
    print(f"   Successfully Processed: {metrics['responses_processed']}")
    print(f"   Auto-processed: {metrics['auto_processed']}")
    print(f"   Human Review Needed: {metrics['human_review_needed']}")
    print(f"   Processing Errors: {len(state['processing_errors'])}")
    
    print(f"\n📈 Response Breakdown:")
    print(f"   😊 Interested: {metrics['interested_responses']}")
    print(f"   ❓ Questions: {metrics['questions_responses']}")
    print(f"   😐 Not Interested: {metrics['not_interested_responses']}")
    print(f"   🔄 Other: {metrics['other_responses']}")
    
    print(f"\n⚡ Actions Taken:")
    print(f"   📅 Interviews Scheduled: {len(state['scheduled_interviews'])}")
    print(f"   📧 Follow-up Emails Sent: {len(state['follow_up_emails'])}")
    print(f"   ⏳ Actions Pending: {len(state['pending_actions'])}")
    
    # Show scheduled interviews
    if state["scheduled_interviews"]:
        print(f"\n📅 Scheduled Interviews:")
        for interview in state["scheduled_interviews"][:5]:
            name = interview["candidate_name"]
            time = interview["scheduled_time"]
            type_str = interview["interview_type"].replace("_", " ").title()
            print(f"   • {name} - {type_str} on {time}")
    
    # Show pending actions
    if state["pending_actions"]:
        print(f"\n⏳ Pending Actions:")
        for action in state["pending_actions"][:5]:
            print(f"   • {action['action']}: {action['reason']}")
    
    # Show errors if any
    if state["processing_errors"]:
        print(f"\n❌ Processing Issues ({len(state['processing_errors'])}):")
        for error in state["processing_errors"][:3]:
            print(f"   • {error}")
    
    # Add final message
    final_message = {
        "type": "system",
        "content": f"📨 Response management complete: {len(state['scheduled_interviews'])} interviews scheduled"
    }
    state = safe_add_message(state, final_message)
    
    print(f"\n🎉 Response management completed successfully!")
    print(f"📞 {len(state['scheduled_interviews'])} interviews scheduled")
    print(f"📬 {len(state['follow_up_emails'])} follow-ups sent")
    print(f"⏭️ Ready for interview coordination stage")
    
    return state

# Helper functions

def simulate_candidate_responses(sent_emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simulate realistic candidate responses for demo purposes"""
    
    responses = []
    import random
    
    response_templates = {
        "interested": [
            "Hi, thank you for reaching out! I'm very interested in this opportunity. When can we schedule a call to discuss further?",
            "This sounds like a great opportunity. I'd love to learn more about the role and the team. Are you available for a call this week?",
            "Thank you for the email. I'm definitely interested in the position. Please let me know when would be a good time to talk."
        ],
        "questions": [
            "Hi, thanks for reaching out. I'm interested but have a few questions: What's the tech stack? Is remote work possible? What's the team size?",
            "This looks interesting. Can you tell me more about the company culture and growth opportunities? Also, what's the salary range?",
            "Thank you for contacting me. I'd like to know more about the day-to-day responsibilities and the team I'd be working with."
        ],
        "not_interested": [
            "Thank you for reaching out, but I'm not looking for new opportunities at this time.",
            "I appreciate the email, but I'm happy in my current role and not considering a change right now.",
            "Thanks for thinking of me, but this doesn't seem like the right fit for my career goals."
        ],
        "schedule_later": [
            "This sounds interesting, but I'm traveling for the next two weeks. Can we reconnect after that?",
            "I'm interested but currently wrapping up a major project. Could we schedule something for next month?",
            "Thanks for reaching out. I'm interested but my schedule is packed this week. How about next week?"
        ]
    }
    
    # Generate responses for 60% of sent emails
    num_responses = int(len(sent_emails) * 0.6)
    responding_emails = random.sample(sent_emails, num_responses)
    
    for email in responding_emails:
        # Determine response type
        response_type = random.choices(
            ["interested", "questions", "not_interested", "schedule_later"],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        # Generate response
        template = random.choice(response_templates[response_type])
        
        response = {
            "response_id": f"resp_{uuid.uuid4().hex[:8]}",
            "original_email_id": email.get("email_id", ""),
            "from_email": email.get("candidate_email", ""),
            "from_name": email.get("candidate_name", "Unknown"),
            "subject": f"Re: {email.get('subject', 'Job Opportunity')}",
            "content": template,
            "received_at": datetime.now().isoformat(),
            "message_type": "reply"
        }
        
        responses.append(response)
    
    return responses

def find_email_context(response: Dict[str, Any], sent_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the original email context for a response"""
    
    response_email = response.get("from_email", "").lower()
    
    for email in sent_emails:
        if email.get("candidate_email", "").lower() == response_email:
            return {
                "email_id": email.get("email_id", ""),
                "candidate_id": email.get("candidate_id", ""),
                "candidate_name": email.get("candidate_name", ""),
                "job_id": email.get("job_id", ""),
                "job_title": email.get("job_title", "")
            }
    
    # Return default context if not found
    return {
        "email_id": response.get("original_email_id", ""),
        "candidate_id": "unknown",
        "candidate_name": response.get("from_name", "Unknown"),
        "job_id": "unknown",
        "job_title": "Unknown Position"
    }

def generate_interview_slots() -> List[InterviewSlot]:
    """Generate available interview time slots"""
    
    slots = []
    now = datetime.now()
    
    # Generate slots for next 2 weeks, business hours only
    for day in range(1, 15):  # Next 14 days
        date = now + timedelta(days=day)
        
        # Skip weekends
        if date.weekday() >= 5:
            continue
        
        # Generate 3 slots per day
        for hour in [10, 14, 16]:  # 10 AM, 2 PM, 4 PM
            slot_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            slot = InterviewSlot(
                slot_id=f"slot_{uuid.uuid4().hex[:8]}",
                start_time=slot_time,
                end_time=slot_time + timedelta(hours=1),
                interviewer="Sarah Johnson",
                interview_type=InterviewType.VIDEO_INTERVIEW if hour != 10 else InterviewType.PHONE_SCREEN,
                timezone="America/New_York"
            )
            slots.append(slot)
    
    return slots

def find_suitable_interview_slot(available_slots: List[InterviewSlot], 
                                preferred_type: InterviewType,
                                availability: str = None) -> InterviewSlot:
    """Find a suitable interview slot based on preferences"""
    
    # Filter by interview type preference
    type_matched_slots = [slot for slot in available_slots if slot.interview_type == preferred_type]
    
    if type_matched_slots:
        return type_matched_slots[0]  # Return first available
    
    # Fall back to any available slot
    return available_slots[0] if available_slots else None

def check_response_processing_completion(state: ResponseManagementState) -> str:
    """Check if response processing is complete"""
    if state.get("processing_complete", False):
        return "response_complete"
    else:
        return "continue_processing"