"""
Real Audio Analysis API for 8-bit Music Maker
NO MOCK FALLBACKS - Forces proper audio analysis
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from real_audio_analyzer import RealAudioAnalyzer

app = Flask(__name__)
CORS(app)

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac'}

# Initialize the real analyzer (will fail if dependencies missing)
try:
    analyzer = RealAudioAnalyzer()
    print("✅ Real Audio Analyzer initialized successfully")
except ImportError as e:
    print("❌ Audio analysis dependencies missing!")
    print("   Install with: pip install librosa soundfile")
    raise RuntimeError("Audio analysis libraries missing in runtime. "
                       "Install librosa and soundfile.") from e

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': '8-bit music analyzer (REAL)',
        'analyzer_loaded': analyzer is not None,
        'timestamp': analyzer.__class__.__name__ if analyzer else 'N/A'
    })

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """
    Real audio analysis endpoint - NO MOCK FALLBACKS
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
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Perform REAL audio analysis
            print(f"Analyzing uploaded file: {file.filename} (BPM hint: {bpm_hint})")
            result = analyzer.analyze_audio_file(temp_path, bpm_hint=bpm_hint)
            
            # Add metadata
            result['original_filename'] = file.filename
            result['file_size_bytes'] = size
            
            print(f"✅ Real analysis complete: {len(result['sequence'])} notes detected")
            return jsonify(result)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ Real analysis failed: {e}")
        return jsonify({
            'error': 'Real audio analysis failed',
            'details': str(e),
            'note': 'This is a real audio analyzer. No mock fallbacks available.'
        }), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about the real analysis service"""
    return jsonify({
        'service': '8-bit Music Analyzer (REAL)',
        'version': '2.0-real',
        'status': 'real_analysis_only',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': f'{MAX_FILE_SIZE // (1024*1024)}MB',
        'features': [
            'Real audio analysis using librosa.pyin',
            'Musical quantization with MIDI distances',
            'Dynamic note duration based on BPM',
            'Median filtering for noise reduction',
            'No mock fallbacks - real analysis only'
        ],
        'analyzer_class': analyzer.__class__.__name__,
        'frequency_count': len(analyzer.available_frequencies)
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
        'error': 'Real audio analysis failed',
        'details': 'Check server logs for details',
        'note': 'This service only provides real audio analysis'
    }), 500

if __name__ == '__main__':
    print("🎵 Starting REAL 8-bit Music Analyzer API...")
    print("⚠️  This API provides REAL audio analysis only - no mock fallbacks")
    print(f"   Real analyzer loaded: {analyzer.__class__.__name__}")
    print(f"   Supported frequencies: {len(analyzer.available_frequencies)}")
    print(f"   Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"   Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("")
    print("Available endpoints:")
    print("  POST /analyze - Real audio analysis (NO MOCKS)")
    print("  GET /info - Service information")
    print("  GET /health - Health check")
    print("")
    print("Starting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)