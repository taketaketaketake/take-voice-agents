import asyncio
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession, Agent
from livekit.agents.llm import ToolContext, function_tool
from livekit.plugins import openai, silero

import openai as openai_client  # Moved to top

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client for appointments
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_ROLE")
)

@function_tool
async def save_appointment(
    customer_name: str,
    phone_number: str,
    address: str,
    home_size: str = "",
    last_service_date: str = "",
    issue_description: str = "",
    preferred_date: str = "",
    preferred_time: str = "",
    urgency: str = "routine",
    call_id: str = None
):
    """Save customer appointment information to the database"""
    try:
        # Extract city from address if possible
        city = ""
        state = "Michigan"
        if "," in address:
            parts = address.split(",")
            if len(parts) >= 2:
                city = parts[1].strip()
        
        appointment_data = {
            "customer_name": customer_name,
            "phone_number": phone_number,
            "address": address,
            "city": city,
            "state": state,
            "home_size": home_size,
            "last_service_date": last_service_date,
            "issue_description": issue_description,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "urgency": urgency,
            "status": "new",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Retry logic for database writes
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(
                    lambda: supabase.table("furnace_appointments").insert(appointment_data).execute()
                )
                break
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise e
                await asyncio.sleep(1)
        logger.info(f"Appointment saved successfully: {result.data}")
        
        # Update call record to link with appointment
        if call_id:
            try:
                for attempt in range(3):
                    try:
                        await asyncio.to_thread(
                            lambda: supabase.table("furnace_calls")
                            .update({
                                "call_status": "booked",
                                "appointment_id": result.data[0]["id"]
                            })
                            .eq("id", call_id)
                            .execute()
                        )
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        await asyncio.sleep(1)
                logger.info(f"Call {call_id} linked to appointment {result.data[0]['id']}")
            except Exception as e:
                logger.error(f"Failed to link call to appointment: {e}")
        
        return {
            "status": "success",
            "message": "Appointment saved successfully. We'll call you back within 24 hours to schedule your service.",
            "appointment_data": appointment_data,
            "appointment_id": result.data[0]["id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to save appointment: {e}")
        return {
            "status": "error",
            "message": "I apologize, there was an issue saving your information. Let me transfer you to someone who can help you directly.",
            "error": str(e)
        }

async def entrypoint(ctx: JobContext):
    logger.info(f"Agent starting in room: {ctx.room.name}")

    # Initialize call tracking variables
    call_id = None
    conversation_log = []
    call_start_time = datetime.utcnow()

    # Test OpenAI connection
    try:
        client = openai_client.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        await asyncio.to_thread(client.models.list)  # offload sync call
        logger.info("OpenAI API connection successful")
    except Exception as e:
        logger.error(f"OpenAI API test failed: {e}")

    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    # Wait for first participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Load VAD properly
    try:
        vad = silero.VAD.load()
    except Exception as e:
        logger.error(f"Failed to load VAD: {e}")
        return

    session = AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=0.7
        ),
        tts=openai.TTS(
            model="tts-1",
            voice="alloy",
            speed=1.0
        ),
        vad=vad,
    )

    # Try registering function directly on session
    try:
        session.register_function_tool(save_appointment)
        logger.info("Function tool registered successfully")
    except Exception as e:
        logger.warning(f"Could not register function tool: {e} - continuing without function calling")

    # Note: Memory persistence disabled for this LiveKit version
    # Can be re-enabled when SupabaseMemory is available

    @session.on("user_speech_committed")
    def on_user_speech(ev):
        logger.info(f"User said: {ev.user_transcript}")
        conversation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "speaker": "user",
            "text": ev.user_transcript
        })

    @session.on("agent_speech_committed")
    def on_agent_speech(ev):
        logger.info(f"Agent said: {ev.agent_transcript}")
        conversation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "speaker": "agent",
            "text": ev.agent_transcript
        })

    @session.on("function_calls_finished")
    def on_function_calls_finished(ev):
        logger.info("Function calls finished")
    
    @session.on("user_interrupt")
    def on_user_interrupt(ev):
        logger.info("User interrupted the agent.")
    
    # Store conversation transcript on disconnect
    @ctx.room.on("participant_disconnected")
    def on_disconnect(p):
        logger.info(f"User disconnected: {p.identity}")
        
        # Save final call transcript with summary
        if call_id:
            try:
                call_duration = int((datetime.utcnow() - call_start_time).total_seconds())
                
                transcript_data = {
                    "ended_at": datetime.utcnow().isoformat(),
                    "conversation": conversation_log,
                    "total_messages": len(conversation_log)
                }
                
                # Generate summary if conversation happened
                summary = ""
                if conversation_log:
                    try:
                        # Create a compact conversation for summarization
                        conversation_text = "\n".join([
                            f"{msg['speaker']}: {msg['text']}" for msg in conversation_log
                        ])
                        
                        # Use basic summary since we can't await in sync callback
                        summary = f"Call lasted {call_duration}s with {len(conversation_log)} messages"
                        
                    except Exception as e:
                        logger.error(f"Failed to create summary task: {e}")
                        summary = f"Call lasted {call_duration}s with {len(conversation_log)} messages"
                
                # Update call record with transcript, summary, and duration
                def save_call_data_sync():
                    try:
                        supabase.table("furnace_calls").update({
                            "call_status": "completed" if conversation_log else "disconnected",
                            "transcript": transcript_data,
                            "summary": summary,
                            "duration_seconds": call_duration
                        }).eq("id", call_id).execute()
                    except Exception as e:
                        logger.error(f"Failed to save call data: {e}")
                
                # Run in background thread since we can't use async in sync callback
                asyncio.create_task(asyncio.to_thread(save_call_data_sync))
                
                logger.info(f"Call transcript and summary saved for {participant_phone} (duration: {call_duration}s)")
                
            except Exception as e:
                logger.error(f"Failed to save call transcript: {e}")

    # Get phone number from participant identity with fallback
    participant_phone = getattr(participant, "identity", "unknown")
    if participant_phone.startswith("sip:"):
        participant_phone = participant_phone.split(":")[1]
    elif "sip_" in participant_phone:
        participant_phone = participant_phone.replace("sip_", "").replace("_", "")
    
    logger.info(f"Caller phone number: {participant_phone}")
    
    # Create call record on start
    try:
        call_record = {
            "phone_number": participant_phone,
            "call_status": "in_progress",
            "agent_name": "Charlotte"
        }
        
        for attempt in range(3):
            try:
                call_result = await asyncio.to_thread(
                    lambda: supabase.table("furnace_calls").insert(call_record).execute()
                )
                call_id = call_result.data[0]["id"]
                logger.info(f"Call tracking started with ID: {call_id}")
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Failed to create call record: {e}")
    
    agent = Agent(
        instructions=f"""
        You are Charlotte, a friendly customer service representative for Fix My Furnace in Michigan.
        
        Your job is to help customers schedule furnace service appointments. Be warm, professional, and helpful.
        
        CONVERSATION FLOW:
        1. Greet warmly and ask what's going on with their furnace
        2. Get their name
        3. Confirm their address (for service location)
        4. Ask about their home size (square footage or bedrooms)
        5. Ask when their furnace was last serviced
        6. Ask about timing preferences (this week, ASAP, etc.)
        7. Use save_appointment function to store all information
        
        You can call save_appointment() when you have all the necessary details.
        Always confirm the customer's name, address, and issue before booking.
        When calling save_appointment, use call_id: {call_id}
        
        IMPORTANT GUIDELINES:
        - Keep responses brief (1-2 sentences)
        - Ask ONE question at a time
        - Sound natural, not robotic
        - Use contractions (I'll, we'll, can't)
        - If they seem urgent, ask about that
        - The caller's phone number is: {participant_phone}
        
        EXAMPLE CONVERSATION:
        "Hi, this is Charlotte with Fix My Furnace! What's going on with your heating system today?"
        
        Don't mention you're an AI. Act like a real person working from the office.
        """
    )

    try:
        await session.start(room=ctx.room, agent=agent)
        logger.info("Voice agent ready and active")
        
        # Send initial greeting
        await session.say("Hi, this is Charlotte with Fix My Furnace! What's going on with your heating system today?", allow_interruptions=True)
        
    except Exception as e:
        logger.error(f"Agent session failed: {e}")

def main():
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "OPENAI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"Missing env vars: {missing}")
        return

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="telephony-voice-agent",
        )
    )

if __name__ == "__main__":
    main()