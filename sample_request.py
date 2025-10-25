import requests
import json

# Sample Python request to process video with FFmpeg
def make_sample_request():
    url = "http://localhost:8000/process-video"
    
    headers = {
        "Authorization": "Bearer YOUR_BEARER_TOKEN",  # Replace with your API bearer token
        "Content-Type": "application/json"
    }
    
    payload = {
        "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
        "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy OUTPUT_FILE",
        # Note: GCP token is now generated automatically by the API
        "output_extension": "mp4",
        "return_raw_output": True
    }
    
    try:
        print("📹 Making request to video processing API...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success! Processed video URI: {result.get('output_uri')}")
            
            if result.get('raw_output'):
                print(f"\n📋 FFmpeg Command: {result['raw_output']['command']}")
                print(f"📋 FFmpeg Stderr: {result['raw_output']['stderr']}")
        else:
            print(f"\n❌ Error: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    make_sample_request()
