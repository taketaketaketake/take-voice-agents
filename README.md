# Twilio + Livekit Voice Agent

AI Voice Agent that handles phone calls and SMS using Twilio and Livekit with minimal dependencies.

## Features

- ✅ **Minimal Dependencies**: Uses free OpenAI Whisper STT + OpenAI LLM/TTS
- ✅ **CLI-First Setup**: All configuration via Livekit CLI commands
- ✅ **Interruption Handling**: Natural conversation flow with built-in turn detection
- ✅ **Phone & SMS**: Handles both voice calls and text messages
- ✅ **Scalable**: Built on Livekit's robust infrastructure

## Architecture

```
Twilio Phone/SMS → SIP Trunk → Livekit Room → AI Voice Agent
```

## Quick Start

1. **Setup Environment**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure API Keys**
   Edit `.env` with your keys:
   - Livekit: URL, API Key, API Secret
   - OpenAI: API Key
   - Twilio: Account SID, Auth Token, Phone Number

3. **Configure SIP Integration**
   ```bash
   chmod +x configure_sip.sh
   ./configure_sip.sh
   ```

4. **Start Voice Agent**
   ```bash
   source venv/bin/activate
   python voice_agent.py
   ```

5. **Start SMS Handler** (separate terminal)
   ```bash
   source venv/bin/activate
   python sms_handler.py
   ```

## Twilio Configuration

### For Voice Calls
1. In Twilio Console, create a TwiML Bin
2. Use content from `twilio_config/twiml_bin.xml`
3. Replace placeholders with your actual values
4. Configure your phone number to use this TwiML Bin

### For SMS
1. Set your phone number's SMS webhook to: `https://your-domain.com/sms`
2. Deploy `sms_handler.py` to a public endpoint

## Cost Breakdown

- **STT**: Free (OpenAI Whisper)
- **LLM**: ~$0.15/1K tokens (GPT-4o-mini)
- **TTS**: ~$15/1M characters (OpenAI TTS)
- **Twilio**: Voice rates + SMS rates per your plan
- **Livekit**: Free tier available

## File Structure

```
├── voice_agent.py          # Main voice agent
├── sms_handler.py          # SMS to call bridge
├── requirements.txt        # Python dependencies
├── setup.sh               # Automated setup
├── configure_sip.sh       # SIP configuration
├── .env.example           # Environment template
├── sip_config/            # Livekit SIP configs
└── twilio_config/         # Twilio TwiML templates
```

## Development

- **Agent Name**: `telephony-voice-agent`
- **Room Prefix**: `call-` (calls create rooms like `call-abc123`)
- **Logging**: INFO level for debugging

## Troubleshooting

1. **Agent not connecting**: Check Livekit credentials and SIP trunk
2. **No audio**: Verify Twilio TwiML configuration
3. **SMS not working**: Ensure webhook URL is publicly accessible
4. **High latency**: Consider using Livekit's regional endpoints

  source venv/bin/activate
  python voice_agent.py dev
