import asyncio
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession, Agent
from livekit.agents.llm import ToolContext, function_tool, llm
from livekit.agents.llm.chat_context import ChatContext, ChatMessage
from livekit.agents.voice.background_audio import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip
from livekit.plugins import openai, silero
from elevenlabs_tts import ElevenLabsTTS
from collections.abc import AsyncIterable

import openai as openai_client
from supabase_service import (
    insert_appointment,
    insert_call,
    update_call,
    link_call_to_appointment,
    save_transcript,
    cleanup_stale_calls,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global background audio player for function tools
background_audio_player = None


# Global variables for pre-response functionality
fast_llm = None
session_instance = None

# Global variables for latency tracking
latency_metrics = {}

async def generate_pre_response(user_message: str) -> str:
    """Generate quick acknowledgment using fast LLM"""
    global fast_llm
    
    start_time = datetime.utcnow()
    
    if not fast_llm:
        fast_llm = openai.LLM(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=15
        )
    
    # Simple context for fast response
    fast_response_messages = [
        ChatMessage(
            role="system", 
            content="Generate a short professional response to acknowledge the customer's message with 5 to 10 words. You work for Fix My Furnace customer service. Examples: 'Let me help you with that', 'One moment while I check', 'I'll get that set up', 'That's a good question'."
        ),
        ChatMessage(role="user", content=user_message)
    ]
    
    # Create simple chat context
    fast_ctx = ChatContext(messages=fast_response_messages)
    
    # Generate quick response
    response = ""
    async for chunk in fast_llm.chat(chat_ctx=fast_ctx).to_str_iterable():
        response += chunk
    
    # Track pre-response latency
    end_time = datetime.utcnow()
    latency_ms = int((end_time - start_time).total_seconds() * 1000)
    logger.info(f"Pre-response latency: {latency_ms}ms")
    
    return response.strip()


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
        # Track function call latency
        function_start_time = datetime.utcnow()
        
        # Add typing sounds while processing appointment
        if background_audio_player:
            typing_handle = background_audio_player.play(
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.12)
            )
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
        }
        
        result = await insert_appointment(appointment_data)
        
        if call_id:
            await link_call_to_appointment(call_id, result["id"])
        
        # Track function completion time
        function_end_time = datetime.utcnow()
        function_latency_ms = int((function_end_time - function_start_time).total_seconds() * 1000)
        logger.info(f"save_appointment function latency: {function_latency_ms}ms")
        
        return {
            "status": "success",
            "message": "Appointment saved successfully. We'll call you back within 24 hours to schedule your service.",
            "appointment_data": appointment_data,
            "appointment_id": result["id"],
            "function_latency_ms": function_latency_ms
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

    # Clean up any stale in_progress calls from previous sessions
    await cleanup_stale_calls()

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

    # Initialize background audio for professional atmosphere
    global background_audio_player
    background_audio_player = BackgroundAudioPlayer(
        ambient_sound=AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=0.08),
        thinking_sound=AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.12)
    )

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
        # tts=ElevenLabsTTS(
        #     voice_id="pNInz6obpgDQGcFmaJgB",  # Adam - natural male voice
        #     model="eleven_turbo_v2_5",        # Fast, high-quality model
        #     stability=0.6,
        #     similarity_boost=0.8,
        #     style=0.2,
        # ),
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

    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        logger.info(f"Conversation: {event.item.role} - {event.item.text_content}")
        conversation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "speaker": "user" if event.item.role == "user" else "agent",
            "text": event.item.text_content
        })
        
        # Generate immediate acknowledgment for natural conversation flow
        async def send_pre_response():
            try:
                if event.item.role == "user":
                    pre_response = await generate_pre_response(event.item.text_content)
                    logger.info(f"Charlotte quick response: {pre_response}")
                    # Send quick acknowledgment without adding to chat context
                    await session.say(pre_response, allow_interruptions=True, add_to_chat_ctx=False)
            except Exception as e:
                logger.warning(f"Failed to generate pre-response: {e}")
        
        # Send pre-response asynchronously for user messages only
        if event.item.role == "user":
            asyncio.create_task(send_pre_response())


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
        
        # Cleanup background audio
        if background_audio_player:
            asyncio.create_task(background_audio_player.aclose())
        
        # Save final call transcript with summary
        if call_id:
            try:
                call_duration = int((datetime.utcnow() - call_start_time).total_seconds())
                
                logger.info(f"Saving transcript with {len(conversation_log)} messages")
                
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
                async def save_call_data():
                    try:
                        await save_transcript(call_id, transcript_data, summary, call_duration)
                    except Exception as e:
                        logger.error(f"Failed to save call data: {e}")
                
                # Run in background since we can't use async in sync callback
                asyncio.create_task(save_call_data())
                
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
        call_id = await insert_call(participant_phone)
        logger.info(f"Call tracking started with ID: {call_id}")
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
        4. Ask when their furnace was last serviced
        5. Ask about timing preferences (this week, ASAP, etc.)
        6. Use save_appointment function to store all information
        
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
        
        # Start background audio after session is started
        await background_audio_player.start(room=ctx.room, agent_session=session)
        logger.info("Background audio started")
        
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