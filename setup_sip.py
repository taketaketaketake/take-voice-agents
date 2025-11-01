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

async def setup_sip_configuration():
    """Set up SIP trunk and dispatch rules using Python API"""
    
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
        
        # Create SIP inbound trunk
        logger.info("Creating SIP inbound trunk...")
        trunk_request = api.CreateSIPInboundTrunkRequest(
            trunk=api.SIPInboundTrunkInfo(
                name="Twilio Inbound Trunk",
                auth_username="xdh1fvzi1n1", 
                auth_password="UepCW3@rTm3hOziA"
            )
        )
        
        trunk_response = await lk_api.sip.create_sip_inbound_trunk(trunk_request)
        logger.info(f"✅ Created SIP trunk: {trunk_response.trunk.sip_trunk_id}")
        
        # Create dispatch rule
        logger.info("Creating dispatch rule...")
        dispatch_request = api.CreateSIPDispatchRuleRequest(
            rule=api.SIPDispatchRuleIndividual(
                room_prefix="call-"
            ),
            room_config=api.CreateRoomRequest(
                agents=[api.RoomAgentDispatch(
                    agent_name="telephony-voice-agent"
                )]
            )
        )
        
        dispatch_response = await lk_api.sip.create_sip_dispatch_rule(dispatch_request)
        logger.info(f"✅ Created dispatch rule: {dispatch_response.dispatch_rule.dispatch_rule_id}")
        
        logger.info("🎉 SIP configuration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to set up SIP configuration: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🔧 Setting up SIP configuration with Python API...")
    success = await setup_sip_configuration()
    
    if success:
        logger.info("✅ SIP setup complete! You can now test calling your Twilio number.")
    else:
        logger.error("❌ SIP setup failed. Please check your credentials and try again.")

if __name__ == "__main__":
    asyncio.run(main())