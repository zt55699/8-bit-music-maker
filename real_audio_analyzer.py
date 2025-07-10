"""
Real Audio Analyzer for 8-bit Music Maker
Uses librosa for actual audio analysis - no mock fallbacks
"""

import librosa
import numpy as np
import soundfile as sf
import os
import uuid
from datetime import datetime
from scipy.signal import medfilt


class RealAudioAnalyzer:
    def __init__(self):
        """Initialize the real audio analyzer with proper frequency mapping"""
        
        # Complete frequency to key mapping (exact match with frontend)
        self.freq_to_key_map = {
            65.41: '1', 73.42: '2', 82.41: '3', 87.31: '4', 98.00: '5',
            110.00: '6', 123.47: '7', 130.81: 'a', 146.83: 's', 164.81: 'd',
            174.61: 'f', 196.00: 'g', 220.00: 'h', 246.94: 'j', 261.63: 'k',
            293.66: 'l', 329.63: 'z', 349.23: 'x', 392.00: 'c', 440.00: 'v',
            493.88: 'b', 523.25: 'n', 587.33: 'm', 659.25: 'p'
        }
        
        # Reverse mapping for quantization
        self.key_to_freq_map = {v: k for k, v in self.freq_to_key_map.items()}
        
        # Available frequencies for quantization
        self.available_frequencies = sorted(self.freq_to_key_map.keys())
        
        print(f"Real Audio Analyzer initialized with {len(self.available_frequencies)} frequencies")

    def frequency_to_key(self, frequency):
        """Convert frequency to the closest available key"""
        if frequency == 0 or frequency is None:
            return ' '
        
        # Find closest frequency using musical (MIDI) distance
        closest_freq = min(self.available_frequencies, 
                          key=lambda x: abs(librosa.hz_to_midi(x) - librosa.hz_to_midi(frequency)))
        
        return self.freq_to_key_map[closest_freq]

    def quantize_frequency(self, frequency):
        """Quantize frequency to nearest available frequency"""
        if frequency == 0 or frequency is None:
            return 0
        
        # Use MIDI-based distance for musical accuracy
        closest_freq = min(self.available_frequencies,
                          key=lambda x: abs(librosa.hz_to_midi(x) - librosa.hz_to_midi(frequency)))
        
        return closest_freq

    def analyze_audio_file(self, file_path, bpm_hint=120):
        """
        Analyze audio file and extract note sequence with timing
        
        Args:
            file_path: Path to audio file
            bpm_hint: BPM hint for dynamic timing thresholds
            
        Returns:
            dict: Analysis result with sequence, timing info
        """
        print(f"Starting real audio analysis of: {file_path}")
        print(f"BPM hint: {bpm_hint}")
        
        try:
            # Load audio at native sample rate for best quality
            y, sr = librosa.load(file_path, sr=None, mono=True)
            print(f"Loaded audio: {len(y)} samples at {sr} Hz ({len(y)/sr:.2f} seconds)")
            
            # Use improved parameters for better time resolution
            hop_length = 256  # ~5.8ms at 44.1kHz (vs 11.6ms with 512)
            
            # Extract fundamental frequency using PYIN (better than piptrack)
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, 
                fmin=65,        # C2 (lowest note we support)
                fmax=700,       # Slightly above our highest note
                sr=sr,
                hop_length=hop_length,
                fill_na=0
            )
            
            print(f"Extracted {len(f0)} fundamental frequency frames")
            
            # Apply median filtering to reduce noise
            f0_smoothed = medfilt(f0, kernel_size=3)
            
            # Convert to time stamps
            times = librosa.times_like(f0_smoothed, sr=sr, hop_length=hop_length)
            
            # Dynamic minimum note duration based on BPM
            min_note_duration = 60.0 / bpm_hint / 4  # Sixteenth note duration
            min_frames = int(min_note_duration * sr / hop_length)
            
            print(f"Minimum note duration: {min_note_duration:.3f}s ({min_frames} frames)")
            
            sequence = []
            current_freq = None
            current_start_time = None
            current_frame_count = 0
            
            for i, (time, freq) in enumerate(zip(times, f0_smoothed)):
                if freq > 0:  # Voiced frame
                    quantized_freq = self.quantize_frequency(freq)
                    
                    # Check if this is the same note (within semitone tolerance)
                    if current_freq is not None:
                        midi_diff = abs(librosa.hz_to_midi(quantized_freq) - librosa.hz_to_midi(current_freq))
                        is_same_note = midi_diff < 0.5
                    else:
                        is_same_note = False
                    
                    if is_same_note:
                        # Continue current note
                        current_frame_count += 1
                    else:
                        # End previous note if it was long enough
                        if current_freq is not None and current_frame_count >= min_frames:
                            duration = current_frame_count * hop_length / sr
                            key = self.frequency_to_key(current_freq)
                            
                            sequence.append({
                                'key': key,
                                'frequency': current_freq,
                                'duration': duration,
                                'start_time': current_start_time
                            })
                        
                        # Start new note
                        current_freq = quantized_freq
                        current_start_time = time
                        current_frame_count = 1
                        
                else:  # Unvoiced frame (potential pause)
                    # End current note if it exists and is long enough
                    if current_freq is not None and current_frame_count >= min_frames:
                        duration = current_frame_count * hop_length / sr
                        key = self.frequency_to_key(current_freq)
                        
                        sequence.append({
                            'key': key,
                            'frequency': current_freq,
                            'duration': duration,
                            'start_time': current_start_time
                        })
                        
                        # Add pause if gap is significant
                        if len(sequence) > 0:
                            gap_duration = time - (current_start_time + duration)
                            if gap_duration > min_note_duration:
                                sequence.append({
                                    'key': ' ',
                                    'frequency': 0,
                                    'duration': gap_duration,
                                    'start_time': current_start_time + duration
                                })
                    
                    current_freq = None
                    current_frame_count = 0
            
            # Handle final note
            if current_freq is not None and current_frame_count >= min_frames:
                duration = current_frame_count * hop_length / sr
                key = self.frequency_to_key(current_freq)
                sequence.append({
                    'key': key,
                    'frequency': current_freq,
                    'duration': duration,
                    'start_time': current_start_time
                })
            
            print(f"Extracted {len(sequence)} notes from audio")
            
            # Create result
            result = {
                "version": "1.0",
                "sequence": sequence,
                "created": datetime.now().isoformat(),
                "source": "real_audio_analysis",
                "analysis_id": str(uuid.uuid4()),
                "original_filename": os.path.basename(file_path),
                "bpm_hint": bpm_hint,
                "sample_rate": int(sr),
                "duration": float(len(y) / sr),
                "note_count": len(sequence),
                "analysis_params": {
                    "hop_length": hop_length,
                    "min_note_duration": min_note_duration,
                    "frequency_range": [65, 700],
                    "algorithm": "librosa.pyin"
                }
            }
            
            return result
            
        except Exception as e:
            print(f"Real audio analysis failed: {e}")
            raise RuntimeError(f"Audio analysis failed: {str(e)}") from e


def test_analyzer():
    """Test the real analyzer with a simple tone"""
    print("Testing Real Audio Analyzer...")
    
    # Generate a test tone (C major scale)
    sr = 44100
    duration = 0.5
    freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C major scale
    
    # Create test audio
    test_audio = []
    for freq in freqs:
        t = np.linspace(0, duration, int(sr * duration))
        tone = 0.3 * np.sin(2 * np.pi * freq * t)
        test_audio.extend(tone)
    
    test_audio = np.array(test_audio)
    
    # Save test file
    test_file = "/tmp/test_scale.wav"
    sf.write(test_file, test_audio, sr)
    
    # Analyze
    analyzer = RealAudioAnalyzer()
    result = analyzer.analyze_audio_file(test_file, bpm_hint=120)
    
    print(f"Test result: {len(result['sequence'])} notes detected")
    for note in result['sequence'][:5]:  # Show first 5 notes
        print(f"  {note['key']}: {note['frequency']:.2f}Hz, {note['duration']:.3f}s")
    
    return result


if __name__ == "__main__":
    test_analyzer()