# 8-bit Music Maker - Music Extraction Feature

## Overview

This branch contains the music extraction functionality for the 8-bit Music Maker application. This feature uses advanced audio analysis with Demucs v4 source separation to extract melodies from audio files and convert them into 8-bit style sequences.

**Note**: This feature is being deprecated in future versions due to unsatisfactory extraction results. This branch serves as a reference implementation.

## Architecture

### Backend Components

1. **advanced_api.py** (Port 5001)
   - Flask API server with real-time progress tracking
   - Server-Sent Events (SSE) for live progress updates
   - JSON polling fallback endpoint
   - Memory management with garbage collection
   - CORS support for cross-origin requests

2. **advanced_audio_analyzer.py**
   - Demucs v4 (htdemucs_ft model) for source separation
   - Lead stem selection using spectral analysis
   - PYIN pitch detection with 3ms resolution
   - C major pentatonic quantization
   - Beat-relative duration system
   - Consecutive note merging and filtering

### Frontend Components

1. **index.html** & **script.js**
   - File upload interface
   - Real-time progress visualization
   - SSE connection for live updates
   - Fallback to JSON polling if SSE fails
   - Virtual 8-bit keyboard playback

## Key Features

- **Source Separation**: Uses Demucs to separate audio into drums, bass, other, and vocals
- **Lead Detection**: Automatically selects the lead melody stem using spectral centroid analysis
- **Pitch Detection**: High-resolution PYIN algorithm for accurate pitch tracking
- **Quantization**: Maps detected pitches to C major pentatonic scale, then to available keyboard keys
- **Progress Tracking**: Real-time progress updates during analysis
- **Memory Management**: Reuses analyzer instance to avoid loading Demucs model multiple times

## Technical Details

### Audio Analysis Pipeline

1. Load audio file (supports WAV, MP3, FLAC, OGG, M4A, AAC)
2. Separate into stems using Demucs v4
3. Select lead stem based on 2-5kHz energy and spectral variance
4. Extract pitch using PYIN (fmin=65Hz, fmax=700Hz)
5. Quantize to C major pentatonic frequencies
6. Map to virtual keyboard keys
7. Merge consecutive identical notes
8. Filter out notes shorter than 1/32 beat

### API Endpoints

- `POST /analyze` - Submit audio file for analysis
- `GET /progress/<job_id>` - SSE endpoint for real-time progress
- `GET /progress-json/<job_id>` - JSON polling fallback
- `GET /result/<job_id>` - Retrieve analysis results
- `GET /info` - Service information
- `GET /health` - Health check
- `GET /debug/jobs` - Monitor all active jobs
- `POST /debug/cleanup` - Manual cleanup of completed jobs

### Progress Stages

1. 🔊 Loading audio file (10-20%)
2. 🎛️ Separating audio stems (25-40%)
3. 🎯 Selecting lead stem (45-50%)
4. 🎼 Detecting pitch and notes (55-65%)
5. 🥁 Tracking rhythm and tempo (70-75%)
6. 🎹 Extracting and quantizing notes (80-95%)
7. 🔧 Post-processing and cleanup (95-100%)

## Known Issues

1. **Extraction Quality**: The extracted melodies often don't match the original music well
2. **Performance**: Demucs processing can take significant time for longer audio files
3. **Memory Usage**: Demucs model requires substantial memory (~2GB)
4. **Complex Music**: Struggles with polyphonic or harmonically complex music

## Running the Application

### Backend Setup

```bash
# Install dependencies
pip install flask flask-cors demucs librosa soundfile numpy scipy torch torchaudio psutil

# Start the advanced API server
python advanced_api.py
```

### Frontend Setup

```bash
# Start the frontend server
python -m http.server 8080
```

Access the application at http://localhost:8080

## Configuration

- Maximum file size: 16MB
- Supported formats: WAV, MP3, FLAC, OGG, M4A, AAC
- Default BPM: 120 (used as hint for tempo detection)
- Minimum note duration: 1/32 beat
- Confidence threshold: 0.01 for pitch detection

## Future Considerations

This music extraction approach is being deprecated due to:
- Inconsistent extraction quality across different music styles
- High computational requirements
- Better alternatives available (MIDI files, manual transcription)

The codebase will be refactored to focus on direct MIDI import and manual note entry in future versions.