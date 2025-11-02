# 🎤 Voice Agent

A production-ready voice agent that handles phone calls using LiveKit and OpenAI. Perfect for customer service, appointment scheduling, and business telephony applications.

## ✨ Features

- **Real-time voice conversations** with natural speech processing
- **OpenAI integration** for intelligent responses and function calling
- **Phone system compatibility** via SIP/telephony providers
- **Complete call tracking** with transcripts and AI-generated summaries
- **Appointment scheduling** with automatic data collection
- **Conversation memory** across multiple calls
- **Robust database integration** with retry logic
- **Easy deployment** to any cloud platform

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
- **OpenAI** - Speech processing, AI responses, and function calling
- **Phone provider** - Twilio, Telnyx, or similar SIP provider
- **Supabase** - Database for appointments, call logs, and conversation memory

## 📞 Use Cases

- **HVAC/Service businesses** - Schedule repair appointments automatically
- **Healthcare** - Appointment booking with patient information collection
- **Customer service** - Handle inquiries with full conversation tracking
- **Lead qualification** - Collect prospect information intelligently
- **Support hotlines** - Technical support with ticket creation
- **Any business** requiring appointment scheduling via phone

## 🧠 Memory & Persistence

The agent includes **Supabase memory** for conversation continuity:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE=your-service-role-key
```

**Features:**
- Remembers previous conversations with same caller
- Maintains context across multiple calls
- Stores conversation history in `voice_agent_memory` table
- Automatic caller identification via phone number

**Setup:**
1. Create Supabase project
2. Add URL and service role key to `.env`
3. Create required tables (see Database Schema below)
4. Agent handles all data operations automatically

## 🗄️ Database Schema

The agent uses three Supabase tables:

### `furnace_appointments` - Appointment Data
```sql
CREATE TABLE furnace_appointments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  customer_name TEXT NOT NULL,
  phone_number TEXT,
  address TEXT NOT NULL,
  city TEXT,
  state TEXT DEFAULT 'Michigan',
  home_size TEXT,
  last_service_date TEXT,
  issue_description TEXT,
  preferred_date TEXT,
  preferred_time TEXT,
  urgency TEXT DEFAULT 'routine',
  status TEXT DEFAULT 'new',
  appointment_datetime TIMESTAMP WITH TIME ZONE,
  call_duration INTEGER,
  notes TEXT,
  transcript JSONB,
  assigned_technician TEXT,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `furnace_calls` - Complete Call Tracking
```sql
CREATE TABLE furnace_calls (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  phone_number TEXT,
  call_status TEXT DEFAULT 'in_progress',
  transcript JSONB,
  summary TEXT,
  appointment_id UUID REFERENCES furnace_appointments(id),
  duration_seconds INTEGER,
  agent_name TEXT DEFAULT 'Charlotte'
);
```

### `voice_agent_memory` - Conversation Memory
*Auto-created by LiveKit AgentSession*

## 📊 Call Analytics

Every call generates:
- **Complete transcript** with timestamps
- **AI-generated summary** (e.g., "Customer reported no heat, 2000 sq ft home, booked Friday")
- **Call duration** and status tracking
- **Appointment linking** for booked calls

## 🛠️ Customization

Edit `voice_agent.py` to customize:
- Agent personality and instructions
- Voice model and speed
- Data collection fields
- Business logic and workflows
- Integration endpoints

## 📋 Requirements

- Python 3.8+
- LiveKit account (real-time voice infrastructure)
- OpenAI API key (GPT-4 for conversations, Whisper for STT, TTS for voice)
- Supabase project (database and memory storage)
- SIP/telephony provider (Twilio, Telnyx, etc.)

## 🚀 Production Features

- **Retry logic** for database operations (3 attempts with backoff)
- **Async operations** to prevent blocking during DB writes
- **Complete error handling** with graceful fallbacks
- **Memory persistence** across calls for returning customers
- **Function calling** for structured data collection
- **Auto-summarization** of conversations using LLM

---

Ready to deploy? This agent works with Railway, Render, Docker, or any Python hosting platform.