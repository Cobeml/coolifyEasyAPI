#!/bin/bash

# Updated curl request for deployed API - NO GCP token needed!
echo "🎬 Testing deployed API with internal GCP authentication..."

curl -X POST "http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io/process-video" \
  -H "Authorization: Bearer 12345" \
  -H "Content-Type: application/json" \
  -d '{
    "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
    "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy -y OUTPUT_FILE",
    "output_extension": "mp4",
    "return_raw_output": true
  }'

echo -e "\n\n✅ Request sent! The API will now:"
echo "   1. Generate GCP access token automatically"
echo "   2. Download video from GCS"
echo "   3. Process with FFmpeg"
echo "   4. Upload result back to GCS"
