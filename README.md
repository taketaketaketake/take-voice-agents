# 🎤 Voice Agent

A production-ready voice agent that handles phone calls using LiveKit and OpenAI. Perfect for customer service, support lines, or any telephony application.

## ✨ Features

- **Real-time voice conversations** with natural speech processing
- **OpenAI integration** for intelligent responses
- **Phone system compatibility** via SIP/telephony providers
- **Easy deployment** to any cloud platform
- **Customizable personality** and conversation flow

## 🚀 Quick Start

1. **Clone and setup**
   ```bash
   git clone https://github.com/taketaketaketake/take-voice-agents.git
   cd take-voice-agents
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the agent**
   ```bash
   python voice_agent.py dev
   ```

## 🔑 Required APIs

- **LiveKit** - Real-time voice infrastructure
- **OpenAI** - Speech processing and AI responses
- **Phone provider** - Twilio, Telnyx, or similar
- **Supabase** (optional) - Conversation memory and persistence

## 📞 Use Cases

- Customer service automation
- Appointment scheduling
- Lead qualification
- Support hotlines
- Interactive voice responses

## 🧠 Memory & Persistence

The agent includes **Supabase memory** for conversation continuity:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

**Features:**
- Remembers previous conversations with same caller
- Maintains context across multiple calls
- Stores conversation history in `voice_agent_memory` table
- Automatic caller identification via phone number

**Setup:**
1. Create Supabase project
2. Add URL and anon key to `.env`
3. Agent automatically creates memory table on first run

## 🛠️ Customization

Edit `voice_agent.py` to customize:
- Agent personality and instructions
- Voice model and speed
- Response behavior
- Integration workflows
- Memory behavior and retention

## 📋 Requirements

- Python 3.8+
- LiveKit account
- OpenAI API key
- SIP/telephony provider

---

Ready to deploy? This agent works with Railway, Render, Docker, or any Python hosting platform.