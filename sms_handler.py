from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import openai
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twilio SMS Handler")

class SMSRequest(BaseModel):
    to: str
    message: str

class BroadcastRequest(BaseModel):
    numbers: list[str]
    message: str

# Initialize Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Initialize OpenAI client
openai_client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Store conversation contexts (in production, use a database)
conversation_contexts = {}

@app.post("/sms")
async def handle_sms(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
):
    """Handle incoming SMS messages with intelligent responses"""
    logger.info(f"SMS received from {From}: {Body}")
    
    try:
        # Process the incoming message and generate a response
        response_text = process_sms_message(Body, From)
        
        # Send SMS response
        message = twilio_client.messages.create(
            body=response_text,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=From
        )
        
        logger.info(f"Sent SMS response to {From}: {response_text}")
        
        return PlainTextResponse("SMS processed", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        raise HTTPException(status_code=500, detail="Error processing SMS")

def process_sms_message(message_body: str, sender: str) -> str:
    """Process incoming SMS and generate intelligent response using OpenAI"""
    try:
        # Get or create conversation context for this sender
        if sender not in conversation_contexts:
            conversation_contexts[sender] = {
                "messages": [],
                "created_at": datetime.now()
            }
        
        # Add user message to context
        conversation_contexts[sender]["messages"].append({
            "role": "user",
            "content": message_body,
            "timestamp": datetime.now()
        })
        
        # Build messages for OpenAI (keep last 10 messages for context)
        messages = [
            {
                "role": "system",
                "content": """You are Charlotte, a helpful customer service representative for Fix My Furnace, a furnace repair and maintenance company. 

Key information:
- Company: Fix My Furnace
- Services: Furnace repair, maintenance, installation, emergency service
- Hours: Monday-Saturday 7AM-7PM, emergency service available 24/7
- Basic maintenance: starts at $99
- Repairs: typically $150-400 depending on parts needed
- Free estimates available

Guidelines:
- Be friendly, professional, and helpful
- Keep responses concise (under 160 characters when possible for SMS)
- Help with scheduling, pricing questions, and service information
- For emergencies, direct customers to call immediately
- Offer to schedule appointments via text or phone
- If customers want to switch to a phone call, offer to call them back

Respond naturally and conversationally, not with rigid keyword responses."""
            }
        ]
        
        # Add recent conversation history (last 10 messages)
        recent_messages = conversation_contexts[sender]["messages"][-10:]
        for msg in recent_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Generate response using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to context
        conversation_contexts[sender]["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now()
        })
        
        logger.info(f"OpenAI response for {sender}: {ai_response}")
        return ai_response
        
    except Exception as e:
        logger.error(f"Error generating OpenAI response: {e}")
        # Fallback to basic response
        return "Thanks for reaching out! I'm Charlotte from Fix My Furnace. I can help with scheduling service, pricing questions, or information about our services. What can I help you with today?"

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

@app.post("/send-sms")
async def send_sms(request: SMSRequest):
    """Send outbound SMS message"""
    try:
        message = twilio_client.messages.create(
            body=request.message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=request.to
        )
        
        logger.info(f"Sent SMS to {request.to}: {request.message}")
        
        return {
            "status": "sent",
            "message_sid": message.sid,
            "to": request.to,
            "message": request.message
        }
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending SMS: {str(e)}")

@app.post("/broadcast")
async def broadcast_sms(request: BroadcastRequest):
    """Send SMS to multiple recipients"""
    results = []
    
    for number in request.numbers:
        try:
            message = twilio_client.messages.create(
                body=request.message,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=number
            )
            
            results.append({
                "to": number,
                "status": "sent",
                "message_sid": message.sid
            })
            
            logger.info(f"Broadcast SMS sent to {number}")
            
        except Exception as e:
            results.append({
                "to": number,
                "status": "failed",
                "error": str(e)
            })
            
            logger.error(f"Failed to send broadcast SMS to {number}: {e}")
    
    return {
        "message": request.message,
        "total_recipients": len(request.numbers),
        "results": results
    }

@app.get("/conversations")
async def get_conversations():
    """Get all conversation contexts"""
    return {
        "total_conversations": len(conversation_contexts),
        "conversations": {
            phone: {
                "message_count": len(context["messages"]),
                "created_at": context["created_at"].isoformat(),
                "last_message": context["messages"][-1]["timestamp"].isoformat() if context["messages"] else None
            }
            for phone, context in conversation_contexts.items()
        }
    }

@app.get("/conversations/{phone_number}")
async def get_conversation(phone_number: str):
    """Get conversation history for specific phone number"""
    if phone_number not in conversation_contexts:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "phone_number": phone_number,
        "conversation": conversation_contexts[phone_number]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)