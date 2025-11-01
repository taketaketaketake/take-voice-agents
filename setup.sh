#!/bin/bash

# Twilio + Livekit Voice Agent Setup Script

echo "🎙️ Setting up Twilio + Livekit Voice Agent..."

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "📋 Checking dependencies..."
check_tool "python3"
check_tool "pip"

# Install Livekit CLI if not present
if ! command -v lk &> /dev/null; then
    echo "📦 Installing Livekit CLI..."
    curl -sSL https://get.livekit.io | bash
fi

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📄 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before proceeding!"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Set up Livekit SIP trunk: ./configure_sip.sh"
echo "3. Run the voice agent: python voice_agent.py"
echo "4. Run SMS handler: python sms_handler.py"