#!/usr/bin/env python3

import secrets
import string

def generate_sip_credentials():
    """Generate secure SIP trunk credentials"""
    
    # Generate random username (alphanumeric, 8-12 chars)
    username_length = secrets.randbelow(5) + 8  # 8-12 characters
    username = ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                      for _ in range(username_length))
    
    # Generate secure password (alphanumeric + some symbols, 16-20 chars)
    password_length = secrets.randbelow(5) + 16  # 16-20 characters
    password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(password_chars) 
                      for _ in range(password_length))
    
    return username, password

if __name__ == "__main__":
    username, password = generate_sip_credentials()
    
    print("🔐 Generated SIP Trunk Credentials:")
    print(f"SIP_TRUNK_USERNAME={username}")
    print(f"SIP_TRUNK_PASSWORD={password}")
    print()
    print("📝 Add these to your .env file:")
    print(f"SIP_TRUNK_USERNAME={username}")
    print(f"SIP_TRUNK_PASSWORD={password}")
    print()
    print("⚠️  Use the SAME credentials in your Twilio TwiML bin!")