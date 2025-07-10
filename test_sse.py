#!/usr/bin/env python3
import requests
import sseclient  # pip install sseclient-py
import threading
import time

def test_sse_progress():
    print("Testing SSE progress tracking...")
    
    # First start an analysis
    test_file = 'test_mario.wav'
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'audio/wav')}
            data = {'bpm_hint': '120'}
            
            print(f"Starting analysis for {test_file}...")
            r = requests.post('http://localhost:5000/analyze', files=files, data=data)
            
            if r.status_code == 200:
                start_result = r.json()
                job_id = start_result.get('job_id')
                
                if job_id:
                    print(f"Job started: {job_id}")
                    print("Connecting to SSE for progress updates...\n")
                    
                    # Connect to SSE endpoint
                    response = requests.get(f'http://localhost:5000/progress/{job_id}', stream=True)
                    client = sseclient.SSEClient(response)
                    
                    for event in client.events():
                        if event.data:
                            import json
                            try:
                                progress_data = json.loads(event.data)
                                
                                # Print progress update
                                stage = progress_data.get('stage', 0)
                                message = progress_data.get('message', '')
                                progress = progress_data.get('progress', 0)
                                debug = progress_data.get('debug', '')
                                status = progress_data.get('status', 'running')
                                
                                print(f"[Stage {stage}] {message} ({progress}%)")
                                if debug:
                                    print(f"  Debug: {debug}")
                                
                                # Stop when completed or failed
                                if status in ['completed', 'failed']:
                                    print(f"\nFinal status: {status}")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")
                                print(f"Raw data: {event.data}")
                    
                    # Get final result
                    print(f"\nGetting final result...")
                    result_r = requests.get(f'http://localhost:5000/result/{job_id}')
                    
                    if result_r.status_code == 200:
                        result = result_r.json()
                        print(f"✅ Analysis complete! Found {len(result.get('sequence', []))} notes")
                        print(f"   Algorithm: {result.get('analysis_params', {}).get('algorithm', 'unknown')}")
                        print(f"   Tempo: {result.get('detected_tempo', 0):.1f} BPM")
                    else:
                        print(f"❌ Error getting result: {result_r.text}")
                        
                else:
                    print(f"No job_id received: {start_result}")
            else:
                print(f"Error starting analysis: {r.text}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == '__main__':
    test_sse_progress()