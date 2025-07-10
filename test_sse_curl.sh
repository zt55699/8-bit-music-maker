#!/bin/bash

echo "Testing SSE progress tracking with curl..."

# Start analysis and get job_id
echo "Starting analysis..."
RESPONSE=$(curl -s -X POST \
  -F "file=@test_mario.wav" \
  -F "bpm_hint=120" \
  http://localhost:5000/analyze)

echo "Response: $RESPONSE"

# Extract job_id from response
JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

if [ -n "$JOB_ID" ]; then
    echo "Job ID: $JOB_ID"
    echo "Connecting to SSE for progress updates..."
    echo ""
    
    # Connect to SSE endpoint with timeout
    timeout 60 curl -s -N "http://localhost:5000/progress/$JOB_ID" | while read line; do
        if [[ $line == data:* ]]; then
            # Extract JSON from SSE data line
            JSON="${line#data: }"
            echo "Progress: $JSON"
            
            # Check if completed or failed
            if echo "$JSON" | grep -q '"status":"completed"' || echo "$JSON" | grep -q '"status":"failed"'; then
                echo "Analysis finished!"
                break
            fi
        fi
    done
    
    echo ""
    echo "Getting final result..."
    curl -s "http://localhost:5000/result/$JOB_ID" | python3 -m json.tool
    
else
    echo "Failed to get job_id"
    exit 1
fi