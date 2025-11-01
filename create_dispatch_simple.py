#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv
from livekit import api
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_dispatch_rule():
    """Create dispatch rule using simple approach"""
    
    # Get credentials
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY") 
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([url, api_key, api_secret]):
        logger.error("Missing Livekit credentials in .env file")
        return False
    
    try:
        # Create API client
        logger.info("Connecting to Livekit...")
        lk_api = api.LiveKitAPI(url, api_key, api_secret)
        
        # Create dispatch rule with minimal configuration
        logger.info("Creating dispatch rule...")
        dispatch_request = api.CreateSIPDispatchRuleRequest(
            rule=api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                    room_prefix="call-"
                )
            )
        )
        
        dispatch_response = await lk_api.sip.create_sip_dispatch_rule(dispatch_request)
        logger.info(f"✅ Created dispatch rule: {dispatch_response.dispatch_rule.dispatch_rule_id}")
        
        logger.info("🎉 Dispatch rule created successfully!")
        logger.info("📞 Calls will now route to rooms with 'call-' prefix")
        logger.info("🤖 Make sure your voice agent is running to join these rooms!")
        return True
        
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            logger.info("✅ Dispatch rule already exists - that's good!")
            return True
        logger.error(f"❌ Failed to create dispatch rule: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔧 Creating dispatch rule for SIP calls...")
    success = await create_dispatch_rule()
    
    if success:
        logger.info("✅ Ready to test! Call your Twilio number now.")
        logger.info("🎯 Make sure your voice agent is running with: python voice_agent.py dev")
    else:
        logger.error("❌ Dispatch rule creation failed.")

if __name__ == "__main__":
    asyncio.run(main())