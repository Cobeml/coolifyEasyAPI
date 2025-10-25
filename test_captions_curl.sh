#!/bin/bash

# Test script for the add-captions endpoint using curl

API_BASE_URL="http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io"
BEARER_TOKEN="12345"
TEST_VIDEO_URI="gs://ultimateagentbucket/sample_0.mp4"

echo "Testing add-captions endpoint..."
echo "URL: ${API_BASE_URL}/add-captions"
echo "Video URI: ${TEST_VIDEO_URI}"
echo "---------------------------------------------------"

curl -X POST "${API_BASE_URL}/add-captions" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_uri\": \"${TEST_VIDEO_URI}\",
    \"output_extension\": \"mp4\"
  }" \
  --timeout 600 \
  -v

echo -e "\n\n✅ Caption test completed!"
