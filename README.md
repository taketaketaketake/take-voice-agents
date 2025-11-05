# 🎤 Voice Agent

**Production-ready AI voice agent** that handles phone calls and SMS using LiveKit, OpenAI, and Railway deployment. Built for businesses requiring intelligent customer service, appointment scheduling, and automated telephony solutions.

🌟 **[Live Demo](https://call-monitor-production.up.railway.app)** - View real call logs and dashboard

📞 **Ready to deploy in minutes** - Pre-configured for Railway with multi-service architecture

## ✨ Features

### 🎙️ Voice Intelligence
- **Real-time voice conversations** with natural speech processing
- **OpenAI GPT-4 integration** for intelligent responses and function calling
- **Conversation memory** across multiple calls with Supabase persistence
- **Auto-generated call summaries** and complete transcription logs

### 📱 Multi-Channel Communication  
- **Phone system compatibility** via LiveKit SIP integration
- **Intelligent SMS responses** with OpenAI-powered conversations
- **Unified dashboard** for managing both voice calls and SMS threads

### 🚀 Production Ready
- **Railway deployment** with 3-service architecture (voice, dashboard, SMS)
- **Complete call tracking** with real-time monitoring dashboard
- **Appointment scheduling** with automatic data collection and Supabase storage
- **Robust retry logic** and error handling for enterprise reliability

## 🚀 One-Click Railway Deployment

**Deploy to production in 3 minutes** with pre-configured Railway setup:

### Option A: Railway Deploy (Recommended)
1. **Fork this repository** to your GitHub account
2. **Connect to Railway** at [railway.app](https://railway.app)
3. **Import your forked repo** - Railway auto-detects all 3 services:
   - `voice-agent` - Handles phone calls via LiveKit
   - `call-monitor` - Web dashboard for call management  
   - `sms-handler` - Intelligent SMS responses
4. **Set environment variables** (see configuration below)
5. **Deploy** - Your voice agent is live in minutes!

### Option B: Local Development
```bash
git clone https://github.com/taketaketaketake/take-voice-agents.git
cd take-voice-agents
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure environment (see Environment Setup below)
cp .env.example .env && nano .env

# Run services locally
python voice_agent.py dev      # Terminal 1: Voice agent
python call_monitor.py         # Terminal 2: Dashboard (localhost:5000)  
python sms_handler.py          # Terminal 3: SMS API (localhost:8000)
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

## 📞 Use Cases & Success Stories

### 🔧 Service Businesses
- **HVAC/Repair companies** - Automated appointment scheduling with address collection
- **Plumbing services** - Emergency call handling with urgency assessment
- **Home maintenance** - Customer information gathering and service scheduling

### 🏥 Healthcare & Professional Services  
- **Medical practices** - Patient appointment booking with insurance verification
- **Dental offices** - Appointment reminders and rescheduling via phone/SMS
- **Legal consultations** - Initial client intake and case information collection

### 🏢 Enterprise Applications
- **Customer service** - 24/7 inquiry handling with intelligent escalation
- **Lead qualification** - Automated prospect scoring and information capture
- **Support hotlines** - Technical support with automatic ticket creation
- **Sales teams** - Appointment setting with CRM integration

**Real Example:** *Fix My Furnace Detroit* uses this system to handle 100+ service calls per week, automatically collecting customer information and scheduling technician visits.

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

### 🌐 Production Architecture

**Multi-Service Railway Deployment:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Agent   │    │  Call Monitor   │    │   SMS Handler   │
│                 │    │                 │    │                 │
│ ├ LiveKit ←→ AI │    │ ├ Flask Dashboard│    │ ├ FastAPI Server│
│ ├ Phone Calls   │    │ ├ Call Logs     │    │ ├ Twilio Webhook│
│ ├ Transcription │    │ ├ Appointments  │    │ ├ AI Responses  │
│ └ No Public URL │    │ └ Public Domain │    │ └ Public Domain │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Supabase DB   │
                    │                 │
                    │ ├ Call Records  │
                    │ ├ Appointments  │
                    │ ├ Transcripts   │
                    │ └ SMS Threads   │
                    └─────────────────┘
```

**Key Files:**
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

## 🎯 Getting Started

### Quick Deploy to Railway
1. **[Fork this repo](https://github.com/taketaketaketake/take-voice-agents/fork)**
2. **[Connect to Railway](https://railway.app)** 
3. **Deploy all 3 services** with one click
4. **Configure API keys** in Railway dashboard
5. **Start receiving calls!**

### Need Help?
- 📋 **[View Live Demo](https://call-monitor-production.up.railway.app)** - See the dashboard in action
- 📖 **Read the deployment guide** above for step-by-step instructions  
- 🐛 **[Report issues](https://github.com/taketaketaketake/take-voice-agents/issues)** - We respond quickly

### Enterprise Support
Looking for custom integrations, white-label solutions, or enterprise deployment? 
**[Contact us](mailto:your-email@domain.com)** for dedicated support and custom development.

---

⭐ **Star this repo** if it helps your business automate customer communications!