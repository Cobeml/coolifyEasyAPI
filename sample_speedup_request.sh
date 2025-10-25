#!/bin/bash

# Sample curl request to speed up video using FFmpeg
# This will make the video play 2x faster

echo "🚀 Speeding up video gs://ultimateagentbucket/sample_0.mp4..."

curl -X POST "http://localhost:8000/process-video" \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
    "ffmpeg_command": "ffmpeg -i INPUT_FILE -filter:v \"setpts=0.5*PTS\" -filter:a \"atempo=2.0\" OUTPUT_FILE",
    "output_extension": "mp4",
    "return_raw_output": true
  }'

echo -e "\n\n✅ Speed up request completed!"
echo "📝 FFmpeg command explanation:"
echo "   - setpts=0.5*PTS: Makes video 2x faster (0.5 = half the presentation timestamps)"
echo "   - atempo=2.0: Speeds up audio to match (2.0 = double speed)"
