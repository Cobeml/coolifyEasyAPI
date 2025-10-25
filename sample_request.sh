#!/bin/bash

# Sample API request to process video with FFmpeg
# Replace YOUR_BEARER_TOKEN with your actual bearer token
# Replace YOUR_GCS_JWT_TOKEN with your actual GCS JWT token

echo "Making sample request to process video..."

curl -X POST "http://localhost:8000/process-video" \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
    "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy OUTPUT_FILE",
    "bucket_name": "ultimateagentbucket",
    "token": "YOUR_GCS_JWT_TOKEN",
    "output_extension": "mp4",
    "return_raw_output": true
  }'

echo -e "\n\nRequest completed!"
