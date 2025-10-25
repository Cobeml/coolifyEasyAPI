#!/usr/bin/env python3
"""
Test script for the add-captions endpoint
"""
import requests
import json

# Configuration
API_BASE_URL = "http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io"
BEARER_TOKEN = "12345"
TEST_VIDEO_URI = "gs://ultimateagentbucket/sample_0.mp4"

def test_add_captions():
    """Test the add-captions endpoint"""
    url = f"{API_BASE_URL}/add-captions"
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "video_uri": TEST_VIDEO_URI,
        "output_extension": "mp4"
    }
    
    print(f"Testing add-captions endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)  # 10 minute timeout
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if 'output_uri' in result:
                print(f"\n🎬 Captioned video available at: {result['output_uri']}")
        else:
            print("❌ Request failed!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (this is expected for speech-to-text processing)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_add_captions()
