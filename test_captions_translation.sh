#!/bin/bash

# Test script for the add-captions endpoint with translation using curl

API_BASE_URL="http://pg804o08c80ssg08484w4ksg.172.104.17.44.sslip.io"
BEARER_TOKEN="12345"
TEST_VIDEO_URI="gs://ultimateagentbucket/ffmpeg_processed/8c0ec954-3614-4a35-a96d-6a9077b7afdf.mp4"

echo "Testing add-captions endpoint with translation..."
echo "URL: ${API_BASE_URL}/add-captions"
echo "Video URI: ${TEST_VIDEO_URI}"
echo "---------------------------------------------------"

# Test 1: English captions (no translation)
echo "🇺🇸 Test 1: English captions (original)"
curl -X POST "${API_BASE_URL}/add-captions" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_uri\": \"${TEST_VIDEO_URI}\",
    \"output_extension\": \"mp4\"
  }" \
  --timeout 600 \
  -v

echo -e "\n\n---------------------------------------------------"

# Test 2: Spanish captions
echo "🇪🇸 Test 2: Spanish captions"
curl -X POST "${API_BASE_URL}/add-captions" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_uri\": \"${TEST_VIDEO_URI}\",
    \"output_extension\": \"mp4\",
    \"target_lang\": \"ES\"
  }" \
  --timeout 600 \
  -v

echo -e "\n\n---------------------------------------------------"

# Test 3: German captions
echo "🇩🇪 Test 3: German captions"
curl -X POST "${API_BASE_URL}/add-captions" \
  -H "Authorization: Bearer ${BEARER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_uri\": \"${TEST_VIDEO_URI}\",
    \"output_extension\": \"mp4\",
    \"target_lang\": \"DE\"
  }" \
  --timeout 600 \
  -v

echo -e "\n\n✅ All caption tests completed!"
