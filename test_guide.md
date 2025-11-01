# Testing Guide

## Local Testing Steps

### 1. Setup & Install
```bash
./setup.sh
source venv/bin/activate
```

### 2. Configure Environment
Edit `.env` with your actual values:
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
SIP_TRUNK_USERNAME=your_sip_user
SIP_TRUNK_PASSWORD=your_sip_pass
```

### 3. Test Voice Agent Locally
```bash
# Start agent
python voice_agent.py

# In another terminal, test with Livekit CLI
lk room create test-room
lk room join test-room
```

### 4. Configure SIP Integration
```bash
./configure_sip.sh
```

### 5. Deploy SMS Handler
```bash
# For local testing with ngrok
ngrok http 8000

# Start SMS handler
python sms_handler.py
```

### 6. Twilio Configuration

#### Phone Calls:
1. Twilio Console → Phone Numbers → Your Number
2. Voice Configuration → TwiML Bin → Create new bin
3. Use content from `twilio_config/twiml_bin.xml`
4. Replace placeholders with actual values

#### SMS:
1. Twilio Console → Phone Numbers → Your Number  
2. Messaging Configuration → Webhook URL: `https://your-ngrok-url.ngrok.io/sms`

### 7. End-to-End Test
1. Call your Twilio number
2. Should connect to voice agent
3. Test interruptions by speaking while agent talks
4. Send SMS to trigger callback

## Troubleshooting

### Agent Won't Start
- Check `.env` file values
- Verify Livekit credentials: `lk token create --room test --identity test`

### No Audio
- Check SIP trunk configuration
- Verify TwiML bin setup in Twilio

### SMS Not Working  
- Ensure webhook URL is public (use ngrok for testing)
- Check Twilio webhook logs

### High Latency
- Use regional Livekit endpoints
- Optimize OpenAI model selection