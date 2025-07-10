#!/usr/bin/env python3
import requests
import sys

# Test the API
def test_api():
    # First test health
    print("Testing health endpoint...")
    r = requests.get('http://localhost:5000/health')
    print(f"Health check: {r.status_code}")
    if r.status_code == 200:
        print(f"Response: {r.json()}")
    
    # Test analysis with a file
    print("\nTesting analysis endpoint...")
    test_file = 'test_mario.wav'
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'audio/wav')}
            data = {'bpm_hint': '120'}
            
            print(f"Uploading {test_file}...")
            r = requests.post('http://localhost:5000/analyze', files=files, data=data)
            
            print(f"Analysis response: {r.status_code}")
            if r.status_code == 200:
                start_result = r.json()
                job_id = start_result.get('job_id')
                
                if job_id:
                    print(f"Job started: {job_id}")
                    print("Waiting for analysis to complete...")
                    
                    # Poll for result
                    import time
                    for attempt in range(60):  # Wait up to 60 seconds
                        time.sleep(1)
                        result_r = requests.get(f'http://localhost:5000/result/{job_id}')
                        
                        if result_r.status_code == 200:
                            result = result_r.json()
                            print(f"Success! Found {len(result.get('sequence', []))} notes")
                            print(f"Algorithm: {result.get('analysis_params', {}).get('algorithm', 'unknown')}")
                            break
                        elif result_r.status_code == 202:
                            print(f"  Still processing... (attempt {attempt + 1})")
                            continue
                        else:
                            print(f"Error getting result: {result_r.text}")
                            break
                    else:
                        print("Timeout waiting for result")
                else:
                    print(f"No job_id received: {start_result}")
            else:
                print(f"Error: {r.text}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == '__main__':
    test_api()