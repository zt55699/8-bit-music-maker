"""
Improved Audio-to-8bit JSON converter (fixes critical bugs)
Based on the analysis provided in the user feedback
"""

import librosa
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
from scipy.signal import medfilt
from datetime import datetime

class AudioAnalyzer:
    """Improved audio analyzer with proper frequency mapping and bug fixes"""
    
    def __init__(self):
        # Static frequency mapping from frontend (fixed naming collision)
        self.KEY_FREQ = {
            # QWERTY top row
            'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23,
            't': 392.00, 'y': 440.00, 'u': 493.88, 'i': 523.25,
            'o': 587.33, 'p': 659.25,
            # ASDF home row
            'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61,
            'g': 196.00, 'h': 220.00, 'j': 246.94, 'k': 261.63,
            'l': 293.66,
            # ZXCV bottom row
            'z': 329.63, 'x': 349.23, 'c': 392.00, 'v': 440.00,
            'b': 493.88, 'n': 523.25, 'm': 587.33,
            # Number row
            '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
            '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81,
            '9': 146.83, '0': 164.81,
            # Silence
            ' ': 0.00
        }
        
        # Build reverse lookup (fixed: separate dict name from method)
        self.freq_to_key_map = {v: k for k, v in self.KEY_FREQ.items()}
        self.available_freqs = sorted([f for f in self.freq_to_key_map.keys() if f > 0])
        
        # Audio processing parameters (improved as per feedback)
        self.hop_length = 256  # Smaller hop for better time resolution
        self.frame_size = 1024
        self.sample_rate = None  # Use native sample rate instead of forcing 22050
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, float]:
        """Load audio file at native sample rate"""
        try:
            # Load at native sample rate for better quality
            y, sr = librosa.load(file_path, sr=None, mono=True)
            self.sample_rate = sr
            return y, sr
        except Exception as e:
            raise Exception(f"Failed to load audio file: {str(e)}")
    
    def extract_pitch_improved(self, y: np.ndarray, sr: float) -> Tuple[np.ndarray, np.ndarray]:
        """Improved pitch extraction with better parameters"""
        try:
            # Use pyin with improved parameters
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, 
                fmin=librosa.note_to_hz('C2'),  # Lower bound
                fmax=librosa.note_to_hz('C7'),  # Upper bound
                sr=sr,
                hop_length=self.hop_length,  # Smaller hop length
                frame_length=self.frame_size,
                fill_na=0.0,
                center=True
            )
            
            # Apply median filter to smooth pitch track (fixes micro-pitch issues)
            if len(f0) > 0:
                # Use median filter with small window to smooth pitch contours
                f0_smoothed = medfilt(f0, kernel_size=3)
                return f0_smoothed, voiced_flag
            else:
                return f0, voiced_flag
                
        except Exception as e:
            raise Exception(f"Failed to extract pitch: {str(e)}")
    
    def nearest_frontend_freq(self, frequency: float) -> float:
        """Find nearest frequency from frontend mapping"""
        if frequency <= 0:
            return 0.0
        return min(self.available_freqs, key=lambda f: abs(f - frequency))
    
    def frequency_to_key(self, frequency: float) -> str:
        """Convert frequency to key using proper mapping (fixed method name)"""
        if frequency <= 0:
            return ' '
        
        # Find nearest frequency in our mapping
        nearest_freq = self.nearest_frontend_freq(frequency)
        return self.freq_to_key_map.get(nearest_freq, 'a')
    
    def midi_to_frontend_freq(self, midi_note: float) -> float:
        """Convert MIDI note to nearest frontend frequency"""
        if midi_note <= 0:
            return 0.0
        
        # Convert MIDI to Hz
        freq_hz = librosa.midi_to_hz(midi_note)
        
        # Find nearest frontend frequency
        return self.nearest_frontend_freq(freq_hz)
    
    def is_same_note(self, freq1: float, freq2: float) -> bool:
        """Check if two frequencies represent the same note (semitone tolerance)"""
        if freq1 <= 0 or freq2 <= 0:
            return freq1 == freq2
        
        # Use MIDI semitone tolerance instead of Hz tolerance
        midi1 = librosa.hz_to_midi(freq1)
        midi2 = librosa.hz_to_midi(freq2)
        
        return abs(midi1 - midi2) < 0.5  # Less than half semitone
    
    def segment_notes_improved(self, pitch_values: np.ndarray, voiced_flag: np.ndarray, 
                              time_per_frame: float, bpm_hint: int = 120) -> List[Dict]:
        """Improved note segmentation with dynamic minimum duration"""
        if len(pitch_values) == 0:
            return []
        
        # Dynamic minimum note duration based on BPM (instead of hard-coded 0.1s)
        min_note_duration = 60 / bpm_hint / 2  # Eighth note duration
        
        sequence = []
        current_freq = None
        note_duration = 0
        consecutive_frames = 0
        required_frames = max(2, int(0.05 / time_per_frame))  # Minimum 2-3 frames for stability
        
        for i, pitch in enumerate(pitch_values):
            is_voiced = voiced_flag[i] if voiced_flag is not None else pitch > 0
            
            if is_voiced and pitch > 0:
                # Quantize to nearest frontend frequency
                quantized_freq = self.nearest_frontend_freq(pitch)
                
                if current_freq is None:
                    # Start tracking new note
                    current_freq = quantized_freq
                    note_duration = time_per_frame
                    consecutive_frames = 1
                elif self.is_same_note(current_freq, quantized_freq):
                    # Continue current note
                    note_duration += time_per_frame
                    consecutive_frames += 1
                else:
                    # Note changed - save previous if stable and long enough
                    if consecutive_frames >= required_frames and note_duration >= min_note_duration:
                        key = self.frequency_to_key(current_freq)
                        sequence.append({
                            "key": key,
                            "frequency": round(current_freq, 2)
                        })
                    
                    # Start new note
                    current_freq = quantized_freq
                    note_duration = time_per_frame
                    consecutive_frames = 1
            else:
                # Silence detected
                if current_freq is not None:
                    # Save previous note if stable and long enough
                    if consecutive_frames >= required_frames and note_duration >= min_note_duration:
                        key = self.frequency_to_key(current_freq)
                        sequence.append({
                            "key": key,
                            "frequency": round(current_freq, 2)
                        })
                    
                    # Add pause if silence is long enough
                    if note_duration >= min_note_duration:
                        sequence.append({
                            "key": " ",
                            "frequency": 0
                        })
                    
                    current_freq = None
                    note_duration = 0
                    consecutive_frames = 0
        
        # Save final note if exists
        if current_freq is not None and consecutive_frames >= required_frames and note_duration >= min_note_duration:
            key = self.frequency_to_key(current_freq)
            sequence.append({
                "key": key,
                "frequency": round(current_freq, 2)
            })
        
        return sequence
    
    def analyze_audio_file(self, file_path: str, bpm_hint: int = 120) -> Dict:
        """Main analysis method with improved processing"""
        try:
            # Load audio at native sample rate
            y, sr = self.load_audio(file_path)
            
            # Extract pitch with improved parameters
            pitch_values, voiced_flag = self.extract_pitch_improved(y, sr)
            
            # Calculate time per frame
            time_per_frame = self.hop_length / sr
            
            # Segment into notes with dynamic minimum duration
            sequence = self.segment_notes_improved(pitch_values, voiced_flag, time_per_frame, bpm_hint)
            
            # Limit sequence length for UI performance
            max_notes = 100
            if len(sequence) > max_notes:
                sequence = sequence[:max_notes]
            
            # Create output format
            result = {
                "version": "1.1",
                "sequence": sequence,
                "created": datetime.now().isoformat(),
                "source": "improved_analysis",
                "original_file": os.path.basename(file_path),
                "sample_rate": sr,
                "bpm_hint": bpm_hint,
                "analysis_params": {
                    "hop_length": self.hop_length,
                    "frame_size": self.frame_size,
                    "min_note_duration": 60 / bpm_hint / 2
                }
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def save_json(self, data: Dict, output_path: str) -> None:
        """Save analysis result to JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save JSON: {str(e)}")

# Test the improved analyzer
if __name__ == "__main__":
    import sys
    
    analyzer = AudioAnalyzer()
    
    if len(sys.argv) > 1:
        try:
            result = analyzer.analyze_audio_file(sys.argv[1])
            print(f"Analysis complete! Found {len(result['sequence'])} notes")
            
            # Save result
            output_file = "analyzed_music_improved.json"
            analyzer.save_json(result, output_file)
            print(f"Saved to {output_file}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python audio_analyzer_improved.py <audio_file>")
        print("Example: python audio_analyzer_improved.py song.wav")
        
        # Show improvements
        print("\nKey improvements:")
        print("✓ Fixed naming collision bug")
        print("✓ Native sample rate (not forced 22050)")
        print("✓ Smaller hop length for better time resolution")
        print("✓ Median filtering for pitch smoothing")
        print("✓ Semitone tolerance for note matching")
        print("✓ Dynamic minimum note duration based on BPM")
        print("✓ Requires note stability across multiple frames")