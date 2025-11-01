from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twilio SMS to Voice Bridge")

# Initialize Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

@app.post("/sms")
async def handle_sms(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
):
    """Handle incoming SMS and initiate voice call"""
    logger.info(f"SMS received from {From}: {Body}")
    
    try:
        # Create TwiML response to acknowledge SMS
        response = VoiceResponse()
        
        # Initiate a call back to the sender
        call = twilio_client.calls.create(
            to=From,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url=f"{os.getenv('BASE_URL', 'https://your-domain.com')}/voice",
            method="POST"
        )
        
        logger.info(f"Initiated call {call.sid} to {From}")
        
        # Send confirmation SMS
        message = twilio_client.messages.create(
            body="Thanks for your message! I'm calling you now to discuss further.",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=From
        )
        
        return PlainTextResponse("SMS processed", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        raise HTTPException(status_code=500, detail="Error processing SMS")

@app.post("/voice")
async def handle_voice_call():
    """Handle voice calls - routes to Livekit via SIP"""
    response = VoiceResponse()
    
    # Use the same TwiML configuration as the TwiML bin
    dial = response.dial()
    dial.sip(
        f"sip:{os.getenv('TWILIO_PHONE_NUMBER')}@{os.getenv('LIVEKIT_SIP_ENDPOINT')}",
        username=os.getenv("SIP_TRUNK_USERNAME"),
        password=os.getenv("SIP_TRUNK_PASSWORD")
    )
    
    return PlainTextResponse(str(response), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)