import asyncio
import logging
import os
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession, Agent
from livekit.plugins import openai, silero

import openai as openai_client  # Moved to top

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    logger.info(f"Agent starting in room: {ctx.room.name}")

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

    @session.on("user_speech_committed")
    def on_user_speech(ev):
        logger.info(f"User said: {ev.user_transcript}")

    @session.on("agent_speech_committed")
    def on_agent_speech(ev):
        logger.info(f"Agent said: {ev.agent_transcript}")

    @session.on("function_calls_finished")
    def on_function_calls_finished(ev):
        logger.info("Function calls finished")

    agent = Agent(
        instructions="""
        You are Charlotte, a friendly customer service representative for Fix My Furnace.
        Keep responses brief (1-2 sentences maximum).
        Speak naturally and conversationally.
        Ask one question at a time.
        """
    )

    try:
        await session.start(room=ctx.room, agent=agent)
        logger.info("Voice agent ready and active")
        
        # Send initial greeting
        await session.say("This is Charlotte with Fix My Furnace. What can I do for you today?", allow_interruptions=True)
        
    except Exception as e:
        logger.error(f"Agent session failed: {e}")

    # Optional: Handle disconnect
    @ctx.room.on("participant_disconnected")
    def on_disconnect(p):
        logger.info(f"User disconnected: {p.identity}")
        # Could add: await session.shutdown() if desired

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