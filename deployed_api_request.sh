#!/bin/bash

# Curl request to deployed API for video processing
echo "🎬 Processing video on deployed API..."

curl -X POST "http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io/process-video" \
  -H "Authorization: Bearer 12345" \
  -H "Content-Type: application/json" \
  -d '{
    "video_uri": "gs://ultimateagentbucket/sample_0.mp4",
    "ffmpeg_command": "ffmpeg -i INPUT_FILE -vf scale=720:480 -c:a copy -y OUTPUT_FILE",
    "output_extension": "mp4",
    "return_raw_output": true
  }'

echo -e "\n\n✅ Request sent to deployed API!"
echo "📝 Command: Scale video to 720x480 resolution, keep original audio"
