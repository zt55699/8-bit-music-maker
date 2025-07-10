# Quick Start Guide for Audio Analysis API

## Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **If you don't have pip or Python:**
   - Install Python 3.8+ from https://python.org
   - Install pip: `python -m ensurepip --upgrade`

## Start the API Server

1. **Navigate to the project directory:**
   ```bash
   cd /home/tong/apps/8_bit_music
   ```

2. **Start the Flask API:**
   ```bash
   python app.py
   ```
   
   OR if python3 is required:
   ```bash
   python3 app.py
   ```

3. **You should see output like:**
   ```
   Starting 8-bit Music Analyzer API...
   Supported formats: wav, mp3, flac, ogg, m4a, aac
   Max file size: 16MB
   Available endpoints:
     POST /analyze - Analyze audio file
     GET /download/<id> - Download analysis result
     GET /info - Service information
     POST /test-sample - Test with sample data
     GET /health - Health check
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:5000
   * Running on http://[::1]:5000
   ```

4. **The API is now running on port 5000**

## Test the API

1. **Visit the web app:** http://localhost:8080
2. **Upload an audio file** and click "🎵 Analyze Audio"
3. **The app will now use real audio analysis** instead of mock melodies

## Troubleshooting

### Common Issues:

1. **"ModuleNotFoundError: No module named 'librosa'"**
   ```bash
   pip install librosa
   ```

2. **"Port 5000 already in use"**
   - Change the port in app.py: `app.run(debug=True, host='0.0.0.0', port=5001)`
   - Update frontend script.js to use the new port

3. **"Permission denied" or "command not found"**
   - Try with python3: `python3 app.py`
   - Check if Python is in PATH: `which python` or `which python3`

4. **CORS errors in browser**
   - Make sure Flask-CORS is installed: `pip install flask-cors`

### Dependencies Installation:

If you encounter issues with librosa installation:

```bash
# For Ubuntu/Debian
sudo apt-get install libsndfile1

# For macOS
brew install libsndfile

# For Windows
# Usually works with just pip install
```

## API Endpoints

Once running, you can test these endpoints:

- **Health check:** http://localhost:5000/health
- **Service info:** http://localhost:5000/info
- **Test sample:** http://localhost:5000/test-sample (POST)

## Stop the API

Press `Ctrl+C` in the terminal where the API is running.

## Production Notes

For production deployment:
- Use a proper WSGI server (gunicorn, uWSGI)
- Set up proper logging
- Configure environment variables
- Add rate limiting and authentication if needed