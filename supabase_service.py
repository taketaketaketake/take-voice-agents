import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize once at import
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)


# -------------------------------
# Retry helper
# -------------------------------
async def _with_retries(coro_fn, max_attempts=3, delay=1):
    """Execute a coroutine function with retry logic."""
    for attempt in range(max_attempts):
        try:
            return await asyncio.to_thread(coro_fn)
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"Final attempt failed: {e}")
                raise
            logger.warning(f"Retrying after error ({attempt + 1}/{max_attempts}): {e}")
            await asyncio.sleep(delay)


# -------------------------------
# Appointment I/O
# -------------------------------
async def insert_appointment(data: dict) -> dict:
    """Insert a new appointment record."""
    data["created_at"] = datetime.utcnow().isoformat()

    result = await _with_retries(
        lambda: supabase.table("furnace_appointments").insert(data).execute()
    )
    logger.info(f"Inserted appointment: {result.data}")
    return result.data[0]


# -------------------------------
# Call Tracking I/O
# -------------------------------
async def insert_call(phone_number: str, agent_name="Charlotte") -> str:
    """Create a new call record and return its ID."""
    call_record = {
        "phone_number": phone_number,
        "call_status": "in_progress",
        "agent_name": agent_name,
        "created_at": datetime.utcnow().isoformat(),
    }

    result = await _with_retries(
        lambda: supabase.table("furnace_calls").insert(call_record).execute()
    )
    call_id = result.data[0]["id"]
    logger.info(f"Created call record: {call_id}")
    return call_id


async def update_call(call_id: str, updates: dict):
    """Update a call record by ID."""
    await _with_retries(
        lambda: supabase.table("furnace_calls").update(updates).eq("id", call_id).execute()
    )
    logger.info(f"Updated call {call_id} with {updates}")


# -------------------------------
# Linking
# -------------------------------
async def link_call_to_appointment(call_id: str, appointment_id: str):
    """Link an existing call record to an appointment."""
    await update_call(call_id, {"appointment_id": appointment_id, "call_status": "booked"})


# -------------------------------
# Transcript persistence
# -------------------------------
async def save_transcript(call_id: str, transcript: dict, summary: str, duration_seconds: int):
    """Save transcript and summary after a call ends."""
    status = "completed" if transcript.get("conversation") else "disconnected"
    updates = {
        "call_status": status,
        "transcript": transcript,
        "summary": summary,
        "duration_seconds": duration_seconds,
    }
    await update_call(call_id, updates)