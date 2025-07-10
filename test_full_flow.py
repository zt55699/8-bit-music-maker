#!/usr/bin/env python3
import requests
import time
import json

def test_full_frontend_flow():
    """Test the complete frontend flow to see where it breaks"""
    print("🧪 Testing complete frontend flow...")
    
    # Step 1: Upload file and get job_id
    test_file = 'test_mario.wav'
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'audio/wav')}
            data = {'bpm_hint': '120'}
            
            print(f"📤 Step 1: Uploading {test_file}...")
            r = requests.post('http://localhost:5000/analyze', files=files, data=data)
            
            if r.status_code == 200:
                start_result = r.json()
                job_id = start_result.get('job_id')
                print(f"✅ Step 1: Got job_id: {job_id}")
                
                if job_id:
                    # Step 2: Wait for completion (simulate waitForResult)
                    print(f"🕐 Step 2: Waiting for completion...")
                    
                    for attempt in range(60):  # Wait up to 60 seconds
                        time.sleep(1)
                        result_r = requests.get(f'http://localhost:5000/result/{job_id}')
                        
                        if result_r.status_code == 200:
                            result = result_r.json()
                            print(f"✅ Step 2: Analysis complete!")
                            print(f"   Result keys: {list(result.keys())}")
                            print(f"   Sequence length: {len(result.get('sequence', []))}")
                            print(f"   Algorithm: {result.get('analysis_params', {}).get('algorithm', 'unknown')}")
                            
                            # Step 3: Simulate processAnalysisResult
                            print(f"🔄 Step 3: Processing result (simulating frontend)...")
                            
                            # Check if result has required fields
                            if 'sequence' in result and isinstance(result['sequence'], list):
                                print(f"✅ Result has valid sequence ({len(result['sequence'])} notes)")
                                
                                # Simulate deserializeMusicData
                                json_string = json.dumps(result)
                                print(f"📄 JSON string length: {len(json_string)} characters")
                                
                                # Check each note in sequence
                                for i, note in enumerate(result['sequence']):
                                    if 'key' in note and 'frequency' in note:
                                        print(f"   Note {i+1}: {note['key']} @ {note['frequency']}Hz (duration: {note.get('duration', 'missing')})")
                                    else:
                                        print(f"   ❌ Note {i+1}: Missing key or frequency: {note}")
                                
                                print(f"✅ Step 3: Frontend processing should work!")
                                return True
                            else:
                                print(f"❌ Step 3: Invalid result format - no sequence or not array")
                                print(f"   Result: {result}")
                                return False
                        elif result_r.status_code == 202:
                            print(f"   Still processing... (attempt {attempt + 1})")
                            continue
                        else:
                            print(f"❌ Step 2: Error getting result: {result_r.text}")
                            return False
                    else:
                        print("❌ Step 2: Timeout waiting for result")
                        return False
                else:
                    print(f"❌ Step 1: No job_id received: {start_result}")
                    return False
            else:
                print(f"❌ Step 1: Upload failed: {r.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_full_frontend_flow()
    print(f"\n{'🎉 OVERALL: SUCCESS' if success else '💥 OVERALL: FAILED'}")