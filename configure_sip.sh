#!/bin/bash

# SIP Configuration Script for Livekit + Twilio Integration

source .env

echo "🔧 Configuring Livekit SIP integration..."

# Check if environment variables are set
if [[ -z "$LIVEKIT_URL" || -z "$LIVEKIT_API_KEY" || -z "$LIVEKIT_API_SECRET" ]]; then
    echo "❌ Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in .env"
    exit 1
fi

# Replace placeholders in SIP config files
echo "📝 Preparing SIP configuration..."

# Create temporary files with actual values
sed "s/{{SIP_TRUNK_USERNAME}}/$SIP_TRUNK_USERNAME/g; s/{{SIP_TRUNK_PASSWORD}}/$SIP_TRUNK_PASSWORD/g" \
    sip_config/inbound_trunk.json > /tmp/inbound_trunk.json

# Create SIP inbound trunk
echo "📞 Creating SIP inbound trunk..."
lk sip inbound create /tmp/inbound_trunk.json

# Create dispatch rule
echo "🎯 Creating dispatch rule..."
lk sip dispatch create sip_config/dispatch_rule.json

# Clean up
rm /tmp/inbound_trunk.json

echo "✅ SIP configuration complete!"
echo ""
echo "Next steps for Twilio:"
echo "1. Create TwiML bin in Twilio Console with content from twilio_config/twiml_bin.xml"
echo "2. Replace placeholders in TwiML with your actual values"
echo "3. Configure your Twilio phone number to use the TwiML bin"
echo "4. For SMS: Set webhook URL to https://your-domain.com/sms"