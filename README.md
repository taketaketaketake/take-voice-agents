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

## 🛠️ Development & Deployment

### Core Services

**Voice Agent Server**
```bash
python voice_agent.py dev
```
Starts the LiveKit voice agent server for handling phone calls with AI responses.

**Call Monitor Dashboard**
```bash
python call_monitor.py
```
Launches Flask web interface at `http://localhost:5000` for viewing call data, transcripts, and appointments.

**SMS Handler Service**
```bash
python sms_handler.py
```
Starts FastAPI server at `http://localhost:8000` for intelligent SMS responses with OpenAI integration.

### Local Development Setup

**Expose Services with ngrok**
```bash
# For SMS webhooks (required for Twilio integration)
ngrok http 8000

# For voice webhooks (if needed)
ngrok http 5000
```

**Service Ports**
- Voice Agent: Connects to LiveKit cloud infrastructure
- Call Monitor: `http://localhost:5000`
- SMS Handler: `http://localhost:8000`
- ngrok tunnel: `https://random-id.ngrok-free.app`

### Environment Configuration

Required API keys in `.env`:
```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Twilio (for phone & SMS)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE=your-service-role-key
```

## 📱 SMS System Integration

### Intelligent SMS Responses
- **OpenAI-powered conversations** with contextual responses
- **Conversation memory** across multiple messages per phone number
- **Business context** as "Charlotte from Fix My Furnace"
- **Automatic handoff** to voice calls when requested

### Twilio SMS Configuration

1. **A2P 10DLC Registration** (Required for US business messaging)
   - Register your brand and campaign at console.twilio.com
   - Associate your phone number with approved campaign
   - Approval typically takes 2-7 business days

2. **Webhook Setup**
   ```
   Messaging Service → Integration → Incoming Messages
   Webhook URL: https://your-ngrok-url.ngrok-free.app/sms
   HTTP Method: POST
   ```

3. **Available SMS Endpoints**
   - `POST /sms` - Twilio webhook for incoming messages
   - `POST /send-sms` - Send individual outbound messages
   - `POST /broadcast` - Send bulk messages
   - `GET /conversations` - View all conversation history
   - `GET /conversations/{phone}` - View specific conversation

### SMS Features
- **Keyword intelligence** for scheduling, pricing, emergencies
- **Natural conversations** with GPT-3.5-turbo
- **Conversation threading** per phone number
- **Automatic fallbacks** if OpenAI fails

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

## 🚀 Production Deployment

### Prerequisites for Production

**Required Registrations:**
- **A2P 10DLC approval** (2-7 business days) for US SMS messaging
- **LiveKit account** with production plan for voice infrastructure
- **Supabase project** with database tables created
- **Domain name** for webhook endpoints (recommended over ngrok)

### Deployment Checklist

**Environment Setup:**
```bash
# Verify all API keys are configured
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ All keys loaded' if all([os.getenv('LIVEKIT_URL'), os.getenv('OPENAI_API_KEY'), os.getenv('TWILIO_ACCOUNT_SID')]) else '❌ Missing keys')"
```

**Database Setup:**
1. Create Supabase tables using provided SQL schema
2. Test connection: `python -c "from supabase_service import supabase; print(supabase.table('furnace_calls').select('*').limit(1).execute())"`

**Webhook Configuration:**
- SMS: `https://yourdomain.com/sms`
- Voice: Configure in LiveKit dashboard
- Health check: `https://yourdomain.com/health`

### Production Features

- **Retry logic** for database operations (3 attempts with backoff)
- **Async operations** to prevent blocking during DB writes
- **Complete error handling** with graceful fallbacks
- **Memory persistence** across calls for returning customers
- **Function calling** for structured data collection
- **Auto-summarization** of conversations using LLM
- **Real-time call monitoring** with web dashboard
- **SMS conversation threading** with OpenAI intelligence

### Hosting Platforms

**Recommended:**
- **Railway** - Automatic deployments from GitHub
- **Render** - Easy Python app hosting with health checks
- **DigitalOcean App Platform** - Managed container hosting
- **Docker** - Custom containerized deployment

### Railway Deployment (Recommended)

This project is pre-configured for Railway deployment with multi-service support:

**Quick Deploy:**
1. Connect your GitHub repo to Railway
2. Railway auto-detects the 3 services from `Procfile`:
   - `voice-agent`: Main voice processing service
   - `call-monitor`: Web dashboard (port 5000)
   - `sms-handler`: SMS API service (port 8000)
3. Set environment variables in Railway dashboard
4. Deploy and get webhook URLs for Twilio integration

**Railway Files:**
- `railway.json` - Platform configuration
- `Procfile` - Service definitions
- `.railwayignore` - Deployment exclusions

**Manual Setup Commands:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run production services
python voice_agent.py dev &
python call_monitor.py &
python sms_handler.py &
```

### Monitoring & Scaling

**Health Endpoints:**
- Voice Agent: Check LiveKit connection status
- Call Monitor: `GET /health` - Database connectivity
- SMS Handler: `GET /health` - Twilio & OpenAI status

**Performance:**
- SMS: Handles 1 msg/sec with A2P 10DLC approval
- Voice: Concurrent calls limited by LiveKit plan
- Database: Supabase handles 500+ requests/second

---

🚀 **Ready to deploy?** This agent works with Railway, Render, Docker, or any Python hosting platform.