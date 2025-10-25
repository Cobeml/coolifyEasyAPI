#!/usr/bin/env python3

"""
Simple script to get a GCP access token
"""

import sys
import os
sys.path.append('.')

def get_gcp_token():
    """Get GCP access token and print it"""
    
    try:
        from gcp_auth import authenticate_gcp
        
        print("🔐 Authenticating with GCP...")
        token = authenticate_gcp()
        
        print(f"\n✅ SUCCESS! Your GCP access token:")
        print(f"{token}")
        
        print(f"\n📋 Copy this token and use it in your curl command:")
        print(f'curl -X POST "http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io/process-video" \\')
        print(f'  -H "Authorization: Bearer 12345" \\')
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{{")
        print(f'    "video_uri": "gs://ultimateagentbucket/sample_0.mp4",')
        print(f'    "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy OUTPUT_FILE",')
        print(f'    "token": "{token}",')
        print(f'    "output_extension": "mp4",')
        print(f'    "return_raw_output": true')
        print(f"  }}\'")
        
        return token
        
    except Exception as e:
        print(f"❌ Error getting GCP token: {e}")
        print("\n🔧 Make sure you have set these environment variables:")
        print("   - GCP_PRIVATE_KEY")
        print("   - GCP_KEY_ID")
        print("   - GCP_CLIENT_EMAIL")
        print("   - GCP_PROJECT_ID")
        return None

if __name__ == "__main__":
    get_gcp_token()
