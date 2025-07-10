"""
Simple Flask API for 8-bit music maker without audio analysis dependencies
Provides basic endpoints and test functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_mock_sequence(filename, complexity='medium'):
    """Generate a mock music sequence based on filename"""
    
    # Frontend frequency mapping
    freqs = {
        'simple': [130.81, 146.83, 164.81, 196.00, 220.00, 261.63, 293.66],
        'medium': [98.00, 110.00, 123.47, 130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63, 293.66, 329.63, 392.00, 440.00],
        'complex': [65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 123.47, 130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25]
    }
    
    freq_to_key = {
        65.41: '1', 73.42: '2', 82.41: '3', 87.31: '4', 98.00: '5',
        110.00: '6', 123.47: '7', 130.81: 'a', 146.83: 's', 164.81: 'd',
        174.61: 'f', 196.00: 'g', 220.00: 'h', 246.94: 'j', 261.63: 'k',
        293.66: 'l', 329.63: 'z', 349.23: 'x', 392.00: 'c', 440.00: 'v',
        493.88: 'b', 523.25: 'n', 587.33: 'm', 659.25: 'p'
    }
    
    # Determine complexity from filename
    if any(word in filename.lower() for word in ['simple', 'easy', 'basic']):
        complexity = 'simple'
    elif any(word in filename.lower() for word in ['complex', 'hard', 'advanced']):
        complexity = 'complex'
    
    available_freqs = freqs[complexity]
    
    # Generate sequence based on filename hash for consistency
    random.seed(hash(filename) % (2**32))
    
    # Generate 8-20 notes
    length = random.randint(8, 20)
    sequence = []
    
    for i in range(length):
        if random.random() < 0.15:  # 15% chance of pause
            sequence.append({"key": " ", "frequency": 0})
        else:
            freq = random.choice(available_freqs)
            key = freq_to_key[freq]
            sequence.append({"key": key, "frequency": freq})
    
    return sequence

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': '8-bit music analyzer (simple)',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """
    Mock audio analysis endpoint (no real analysis, returns intelligent mock)
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
        
        # Get file size
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
        
        # Generate intelligent mock sequence
        sequence = generate_mock_sequence(file.filename)
        
        result = {
            "version": "1.0",
            "sequence": sequence,
            "created": datetime.now().isoformat(),
            "source": "mock_server_analysis",
            "original_filename": file.filename,
            "bpm_hint": bpm_hint,
            "note": "This is a mock analysis from the simplified API server. For real audio analysis, install librosa and use the full API."
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e)
        }), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about the service"""
    return jsonify({
        'service': '8-bit Music Analyzer (Simple)',
        'version': '1.0-simple',
        'status': 'mock_analysis_only',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': f'{MAX_FILE_SIZE // (1024*1024)}MB',
        'features': [
            'Mock audio analysis (no real pitch detection)',
            'File validation and handling',
            'Multiple complexity levels',
            'Consistent mock results based on filename'
        ],
        'note': 'This is a simplified API without audio analysis dependencies. Install librosa for real analysis.'
    })

@app.route('/test-sample', methods=['POST'])
def test_with_sample():
    """Test endpoint with sample data"""
    try:
        sample_sequence = [
            {"key": "c", "frequency": 392.00},
            {"key": "d", "frequency": 164.81},
            {"key": "e", "frequency": 329.63},
            {"key": "f", "frequency": 174.61},
            {"key": "g", "frequency": 196.00},
            {"key": " ", "frequency": 0},
            {"key": "a", "frequency": 130.81},
            {"key": "b", "frequency": 493.88},
            {"key": "c", "frequency": 392.00}
        ]
        
        result = {
            "version": "1.0",
            "sequence": sample_sequence,
            "created": datetime.now().isoformat(),
            "source": "test_sample",
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
    print("Starting Simple 8-bit Music Analyzer API...")
    print("⚠️  Note: This is a simplified API without real audio analysis")
    print("   For real audio analysis, install librosa and run the full API")
    print("")
    print(f"Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("Available endpoints:")
    print("  POST /analyze - Mock audio analysis")
    print("  GET /info - Service information")
    print("  POST /test-sample - Test with sample data")
    print("  GET /health - Health check")
    print("")
    print("Starting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)