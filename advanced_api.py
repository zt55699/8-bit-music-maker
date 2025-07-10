"""
Advanced Audio Analysis API for 8-bit Music Maker
Uses the advanced Demucs-based analyzer with progress tracking
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import tempfile
import threading
import time
import json
import uuid
import queue
import gc
from datetime import datetime
from advanced_audio_analyzer import AdvancedAudioAnalyzer

app = Flask(__name__)
CORS(app)

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac'}

# Initialize the advanced analyzer
try:
    analyzer = AdvancedAudioAnalyzer()
    print("✅ Advanced Audio Analyzer initialized successfully")
except Exception as e:
    print("❌ Advanced Audio Analyzer initialization failed!")
    print(f"   Error: {e}")
    raise RuntimeError("Advanced audio analysis libraries missing in runtime. "
                       "Install demucs, librosa, torch, and soundfile.") from e

# Global progress tracking
progress_store = {}
progress_lock = threading.Lock()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': '8-bit music analyzer (ADVANCED)',
        'analyzer_loaded': analyzer is not None,
        'demucs_model': str(analyzer.demucs_model.__class__.__name__),
        'timestamp': analyzer.__class__.__name__ if analyzer else 'N/A'
    })

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """
    Advanced audio analysis endpoint with Demucs source separation and real-time progress
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Unsupported file type',
                'allowed': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            return jsonify({
                'error': 'File too large',
                'max_size': f'{MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Get BPM hint
        bpm_hint = int(request.form.get('bpm_hint', 120))
        
        # Generate unique job ID for progress tracking
        job_id = str(uuid.uuid4())
        
        # Return job_id immediately so frontend can start SSE
        response_data = {
            'job_id': job_id,
            'message': 'Analysis starting...',
            'status': 'starting'
        }
        
        # Initialize progress
        with progress_lock:
            progress_store[job_id] = {
                'stage': 0,
                'message': '🔊 Starting analysis...',
                'progress': 0,
                'total_stages': 7,
                'status': 'running',
                'filename': file.filename
            }
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        # Start analysis in background thread
        import threading
        
        def run_analysis():
            try:
                # Force garbage collection before starting analysis
                import gc
                gc.collect()
                
                # Use the global analyzer but clear any state to avoid contamination
                print(f"🎵 Reusing analyzer instance for job: {job_id} (avoiding model reload)")
                # Clear any cached state in the analyzer
                if hasattr(analyzer, 'clear_cache'):
                    analyzer.clear_cache()
                
                # Perform ADVANCED audio analysis with progress tracking
                print(f"🎵 Starting advanced analysis for: {file.filename} (job: {job_id})")
                result = analyzer.analyze_audio_file_with_progress(temp_path, bpm_hint=bpm_hint, job_id=job_id, progress_store=progress_store, progress_lock=progress_lock)
                
                print(f"🔬 [DEBUG] Analysis completed, result type: {type(result)}")
                print(f"🔬 [DEBUG] Result keys: {list(result.keys()) if result else 'None'}")
                
                # Add metadata
                result['original_filename'] = file.filename
                result['file_size_bytes'] = size
                result['job_id'] = job_id
                
                print(f"🔬 [DEBUG] About to update job {job_id} status to completed")
                
                # Mark as completed and store result
                with progress_lock:
                    print(f"🔬 [DEBUG] Acquired lock, updating job {job_id} status")
                    progress_store[job_id]['status'] = 'completed'
                    progress_store[job_id]['message'] = '✅ Analysis complete!'
                    progress_store[job_id]['progress'] = 100
                    progress_store[job_id]['result'] = result
                    print(f"🔬 [DEBUG] Job {job_id} status set to: {progress_store[job_id]['status']}")
                
                print(f"✅ Advanced analysis complete: {len(result['sequence'])} notes detected")
                print(f"   Tempo: {result['detected_tempo']:.1f} BPM ({result['tempo_source']})")
                print(f"   Duration: {result['duration']:.1f}s")
                
                # Force garbage collection to clean up any temporary objects
                gc.collect()
                
            except Exception as e:
                print(f"Analysis error: {e}")
                import traceback
                traceback.print_exc()
                with progress_lock:
                    print(f"🔬 [DEBUG] Setting job {job_id} status to failed due to exception")
                    progress_store[job_id]['status'] = 'failed'
                    progress_store[job_id]['message'] = f'❌ Analysis failed: {str(e)}'
                    progress_store[job_id]['progress'] = 100
                
                # Force garbage collection on failure
                try:
                    gc.collect()
                except:
                    pass
            finally:
                # Ensure job status is always finalized
                with progress_lock:
                    if job_id in progress_store and progress_store[job_id]['status'] == 'running':
                        print(f"🔬 [DEBUG] Job {job_id} still running in finally block, marking as failed")
                        progress_store[job_id]['status'] = 'failed'
                        progress_store[job_id]['message'] = '❌ Analysis terminated unexpectedly'
                        progress_store[job_id]['progress'] = 100
                    
                    # Remove thread reference to allow garbage collection
                    if job_id in progress_store and 'thread' in progress_store[job_id]:
                        del progress_store[job_id]['thread']
                
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                # Final garbage collection
                import gc
                gc.collect()
                print(f"🔬 [DEBUG] Thread cleanup completed for job {job_id}")
        
        # Start analysis in background
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        # Store thread reference for potential cleanup
        with progress_lock:
            progress_store[job_id]['thread'] = thread
        
        # Return job_id immediately
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Advanced analysis failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Mark progress as failed if job_id exists
        if 'job_id' in locals():
            with progress_lock:
                if job_id in progress_store:
                    progress_store[job_id]['status'] = 'failed'
                    progress_store[job_id]['message'] = f'❌ Analysis failed: {str(e)}'
        
        return jsonify({
            'error': 'Advanced audio analysis failed',
            'details': str(e),
            'note': 'This is an advanced audio analyzer using Demucs source separation.',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about the advanced analysis service"""
    return jsonify({
        'service': '8-bit Music Analyzer (ADVANCED)',
        'version': '3.0-advanced',
        'status': 'advanced_analysis_with_demucs',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': f'{MAX_FILE_SIZE // (1024*1024)}MB',
        'features': [
            'Demucs v4 source separation (htdemucs_ft)',
            'Lead stem selection with spectral analysis',
            'High-resolution PYIN pitch detection (3ms frames)',
            'C major pentatonic quantization',
            'Beat-relative duration system',
            'Consecutive note merging and filtering',
            'No mock fallbacks - advanced analysis only'
        ],
        'analyzer_class': analyzer.__class__.__name__,
        'demucs_model': str(analyzer.demucs_model.__class__.__name__),
        'frequency_count': len(analyzer.available_frequencies),
        'pentatonic_frequencies': len(analyzer.pentatonic_freqs)
    })

@app.route('/progress/<job_id>', methods=['GET', 'OPTIONS'])
def get_progress_sse(job_id):
    """Server-Sent Events endpoint for real-time progress updates"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Cache-Control, Accept, Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    def generate_progress():
        while True:
            with progress_lock:
                if job_id not in progress_store:
                    yield f"data: {{\"error\": \"Job not found\", \"job_id\": \"{job_id}\"}}\n\n"
                    break
                
                # Clean up progress data for JSON serialization
                raw_data = progress_store[job_id]
                progress_data = {
                    'stage': raw_data.get('stage', 0),
                    'message': raw_data.get('message', ''),
                    'progress': raw_data.get('progress', 0),
                    'status': raw_data.get('status', 'unknown'),
                    'filename': raw_data.get('filename', ''),
                    'debug': raw_data.get('debug', ''),
                    'total_stages': raw_data.get('total_stages', 7)
                }
            
            # Send progress update
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            # Stop if completed or failed
            if progress_data['status'] in ['completed', 'failed']:
                yield f"data: {json.dumps(progress_data)}\n\n"  # Send final update
                break
                
            time.sleep(0.5)  # Update every 500ms
    
    response = Response(generate_progress(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Cache-Control, Accept, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Max-Age'] = '86400'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    # Remove credentials header when using wildcard origin for better browser compatibility
    return response

@app.route('/progress-json/<job_id>')
def get_progress_json(job_id):
    """JSON endpoint for progress polling (fallback when SSE fails)"""
    try:
        with progress_lock:
            if job_id not in progress_store:
                response = jsonify({'error': 'Job not found', 'job_id': job_id})
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response, 404
            
            # Clean up progress data for JSON serialization
            raw_data = progress_store[job_id]
            progress_data = {
                'stage': raw_data.get('stage', 0),
                'message': raw_data.get('message', ''),
                'progress': raw_data.get('progress', 0),
                'status': raw_data.get('status', 'unknown'),
                'filename': raw_data.get('filename', ''),
                'debug': raw_data.get('debug', ''),
                'total_stages': raw_data.get('total_stages', 7)
            }
            
            response = jsonify(progress_data)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
    except Exception as e:
        print(f"Error in progress-json endpoint: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({'error': 'Internal server error', 'details': str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/result/<job_id>')
def get_result(job_id):
    """Get analysis result for completed job"""
    with progress_lock:
        if job_id not in progress_store:
            print(f"🔬 [DEBUG] /result/{job_id}: Job not found in progress_store")
            return jsonify({'error': 'Job not found'}), 404
        
        job_data = progress_store[job_id]
        print(f"🔬 [DEBUG] /result/{job_id}: status={job_data['status']}, has_result={'result' in job_data}")
        
        if job_data['status'] == 'completed' and 'result' in job_data:
            print(f"🔬 [DEBUG] /result/{job_id}: Returning completed result with {len(job_data['result'].get('sequence', []))} notes")
            return jsonify(job_data['result'])
        elif job_data['status'] == 'failed':
            print(f"🔬 [DEBUG] /result/{job_id}: Returning failed status")
            return jsonify({'error': job_data['message']}), 500
        else:
            print(f"🔬 [DEBUG] /result/{job_id}: Returning 202, status={job_data['status']}")
            return jsonify({'error': 'Analysis not complete', 'status': job_data['status']}), 202

@app.route('/debug/jobs', methods=['GET'])
def debug_jobs():
    """Debug endpoint to monitor all job statuses"""
    with progress_lock:
        jobs_info = {}
        for job_id, job_data in progress_store.items():
            # Clean up job data for JSON serialization
            clean_job_data = {
                'stage': job_data.get('stage', 0),
                'message': job_data.get('message', ''),
                'progress': job_data.get('progress', 0),
                'status': job_data.get('status', 'unknown'),
                'filename': job_data.get('filename', ''),
                'has_result': 'result' in job_data,
                'has_thread': 'thread' in job_data,
                'thread_alive': job_data.get('thread', {}).is_alive() if 'thread' in job_data else False
            }
            jobs_info[job_id] = clean_job_data
    
    return jsonify({
        'active_jobs': len(progress_store),
        'jobs': jobs_info,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/debug/cleanup', methods=['POST'])
def debug_cleanup():
    """Debug endpoint to manually cleanup completed/failed jobs"""
    cleaned_count = 0
    with progress_lock:
        # Find jobs to clean up (completed/failed and older than 5 minutes)
        import time
        current_time = time.time()
        jobs_to_remove = []
        
        for job_id, job_data in progress_store.items():
            if job_data.get('status') in ['completed', 'failed']:
                # Check if thread exists and is dead
                thread = job_data.get('thread')
                if thread and not thread.is_alive():
                    jobs_to_remove.append(job_id)
                elif not thread:  # No thread reference, safe to clean
                    jobs_to_remove.append(job_id)
        
        # Remove old jobs
        for job_id in jobs_to_remove:
            del progress_store[job_id]
            cleaned_count += 1
    
    # Force garbage collection after cleanup
    gc.collect()
    
    return jsonify({
        'cleaned_jobs': cleaned_count,
        'remaining_jobs': len(progress_store)
    })

@app.route('/progress', methods=['GET'])
def get_progress_info():
    """Get information about progress tracking"""
    return jsonify({
        'message': 'Real-time progress tracking available via SSE',
        'stages': [
            '🔊 Loading audio file',
            '🎛️ Separating audio stems',
            '🎯 Selecting lead stem',
            '🎼 Detecting pitch and notes',
            '🥁 Tracking rhythm and tempo',
            '🎹 Extracting and quantizing notes',
            '🔧 Post-processing and cleanup'
        ],
        'sse_endpoint': '/progress/<job_id>',
        'debug_endpoints': ['/debug/jobs', '/debug/cleanup'],
        'note': 'Use Server-Sent Events for real-time updates'
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'max_size': f'{MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    return jsonify({
        'error': 'Advanced audio analysis failed',
        'details': 'Check server logs for details',
        'note': 'This service provides advanced audio analysis with Demucs'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting ADVANCED 8-bit Music Analyzer API...")
    print("🎛️ Features: Demucs source separation + lead stem selection")
    print(f"   Advanced analyzer loaded: {analyzer.__class__.__name__}")
    print(f"   Demucs model: {analyzer.demucs_model.__class__.__name__}")
    print(f"   Supported frequencies: {len(analyzer.available_frequencies)}")
    print(f"   Pentatonic frequencies: {len(analyzer.pentatonic_freqs)}")
    print(f"   Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"   Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("")
    print("Available endpoints:")
    print("  POST /analyze - Advanced audio analysis with Demucs")
    print("  GET /info - Service information")
    print("  GET /progress - Progress tracking info")
    print("  GET /health - Health check")
    print("")
    print("Starting server on http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)