"""
Flask API for audio file analysis
Converts uploaded audio files to 8-bit music maker JSON format
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import uuid
from datetime import datetime
try:
    from audio_analyzer_improved import AudioAnalyzer
    print("Using improved audio analyzer")
except ImportError:
    from audio_analyzer import AudioAnalyzer
    print("Using basic audio analyzer")
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Initialize analyzer
analyzer = AudioAnalyzer()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': '8-bit music analyzer',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """
    Analyze uploaded audio file and return JSON sequence
    
    Returns:
        JSON with sequence array compatible with 8-bit music maker
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
        if get_file_size(file) > MAX_FILE_SIZE:
            return jsonify({
                'error': 'File too large',
                'max_size': f'{MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save uploaded file
        file.save(upload_path)
        
        try:
            # Get BPM hint from request if provided
            bpm_hint = int(request.form.get('bpm_hint', 120))
            
            # Analyze audio file with improved method
            result = analyzer.analyze_audio_file(upload_path, bpm_hint)
            
            # Add analysis metadata
            result['analysis_id'] = file_id
            result['original_filename'] = file.filename
            if 'created' not in result:
                result['created'] = datetime.now().isoformat()
            
            # Save result to file
            result_filename = f"{file_id}_analysis.json"
            result_path = os.path.join(RESULTS_FOLDER, result_filename)
            
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Clean up uploaded file
            os.remove(upload_path)
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up uploaded file on error
            if os.path.exists(upload_path):
                os.remove(upload_path)
            
            return jsonify({
                'error': 'Analysis failed',
                'details': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Upload failed',
            'details': str(e)
        }), 500

@app.route('/download/<analysis_id>', methods=['GET'])
def download_analysis(analysis_id):
    """
    Download analysis result as JSON file
    
    Args:
        analysis_id: UUID of the analysis
    """
    try:
        result_filename = f"{analysis_id}_analysis.json"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        if not os.path.exists(result_path):
            return jsonify({'error': 'Analysis not found'}), 404
        
        return send_file(
            result_path,
            as_attachment=True,
            download_name=f"music_analysis_{analysis_id}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Download failed',
            'details': str(e)
        }), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about the service and supported formats"""
    return jsonify({
        'service': '8-bit Music Analyzer',
        'version': '1.0',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': f'{MAX_FILE_SIZE // (1024*1024)}MB',
        'key_frequency_mapping': analyzer.frontend_mapping,
        'available_frequencies': analyzer.available_frequencies,
        'features': [
            'Pitch detection using librosa',
            'Frequency quantization to frontend mapping',
            'Monophonic melody extraction',
            'JSON output compatible with 8-bit music maker'
        ]
    })

@app.route('/test-sample', methods=['POST'])
def test_with_sample():
    """
    Test endpoint that creates a sample analysis result
    Useful for testing frontend integration without audio files
    """
    try:
        # Create a sample sequence similar to the demo song
        sample_sequence = [
            {"key": "a", "frequency": 130.81},
            {"key": "s", "frequency": 146.83},
            {"key": "d", "frequency": 164.81},
            {"key": "f", "frequency": 174.61},
            {"key": "g", "frequency": 196.0},
            {"key": " ", "frequency": 0},
            {"key": "g", "frequency": 196.0},
            {"key": "f", "frequency": 174.61},
            {"key": "d", "frequency": 164.81},
            {"key": "s", "frequency": 146.83},
            {"key": "a", "frequency": 130.81},
            {"key": " ", "frequency": 0}
        ]
        
        result = {
            "version": "1.0",
            "sequence": sample_sequence,
            "created": datetime.now().isoformat(),
            "source": "test_sample",
            "analysis_id": "test_sample",
            "original_filename": "test_sample.wav"
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Test failed',
            'details': str(e)
        }), 500

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
        'error': 'Internal server error',
        'details': 'Please try again later'
    }), 500

if __name__ == '__main__':
    print("Starting 8-bit Music Analyzer API...")
    print(f"Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("Available endpoints:")
    print("  POST /analyze - Analyze audio file")
    print("  GET /download/<id> - Download analysis result")
    print("  GET /info - Service information")
    print("  POST /test-sample - Test with sample data")
    print("  GET /health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)