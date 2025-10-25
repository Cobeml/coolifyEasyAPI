#!/usr/bin/env python3

"""
Quick script to generate a GCP access token and test the API
"""

import sys
import os
sys.path.append('.')

from gcp_auth import authenticate_gcp
import requests
import json

def get_token_and_test():
    """Get GCP token and make API request"""
    
    print("🔐 Getting GCP access token...")
    
    try:
        # Get the access token
        gcp_token = authenticate_gcp()
        print(f"✅ Got GCP token: {gcp_token[:20]}...")
        
        # Make the API request
        url = "http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io/process-video"
        
        headers = {
            "Authorization": "Bearer 12345",
            "Content-Type": "application/json"
        }
        
        payload = {
            "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
            "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy OUTPUT_FILE",
            "token": gcp_token,  # Use the real GCP token
            "output_extension": "mp4",
            "return_raw_output": True
        }
        
        print(f"🚀 Making request to: {url}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! Processed video: {result.get('output_uri')}")
        else:
            print(f"\n❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_token_and_test()
