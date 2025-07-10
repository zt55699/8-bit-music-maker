"""
Audio file analyzer for 8-bit music maker
Converts audio files to JSON sequence format
"""

import librosa
import numpy as np
import json
from typing import List, Dict, Tuple, Optional
import os

class AudioAnalyzer:
    def __init__(self):
        # Frontend key-to-frequency mapping (from script.js)
        # This is the exact mapping from the frontend
        self.frontend_mapping = {
            'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23, 't': 392.00,
            'y': 440.00, 'u': 493.88, 'i': 523.25, 'o': 587.33, 'p': 659.25,
            'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61, 'g': 196.00,
            'h': 220.00, 'j': 246.94, 'k': 261.63, 'l': 293.66, 'z': 329.63,
            'x': 349.23, 'c': 392.00, 'v': 440.00, 'b': 493.88, 'n': 523.25,
            'm': 587.33, '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
            '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81, '9': 146.83,
            '0': 164.81, ' ': 0
        }
        
        # Create reverse mapping (frequency to key) for analysis
        self.frequency_to_key = {}
        for key, freq in self.frontend_mapping.items():
            if freq > 0:  # Skip the space/pause key
                self.frequency_to_key[freq] = key
        
        # Create sorted list of frequencies for quantization
        self.available_frequencies = sorted([freq for freq in self.frequency_to_key.keys() if freq > 0])
        
        # Create MIDI to frequency mapping for internal use
        self.midi_to_freq_map = {}
        for key, freq in self.frontend_mapping.items():
            if freq > 0:
                midi_note = self.frequency_to_midi(freq)
                self.midi_to_freq_map[midi_note] = freq
        
        # Default parameters for analysis
        self.hop_length = 512
        self.frame_size = 2048
        self.sample_rate = 22050
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, float]:
        """Load audio file and return audio data and sample rate"""
        try:
            # Load audio file, convert to mono, and resample
            y, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            return y, sr
        except Exception as e:
            raise Exception(f"Failed to load audio file: {str(e)}")
    
    def extract_pitch(self, y: np.ndarray, sr: float) -> Tuple[np.ndarray, np.ndarray]:
        """Extract pitch information from audio using librosa"""
        try:
            # Use librosa's pitch detection
            pitches, magnitudes = librosa.piptrack(
                y=y, 
                sr=sr, 
                hop_length=self.hop_length,
                fmin=80,   # Minimum frequency (around E2)
                fmax=2000  # Maximum frequency (around B6)
            )
            
            # Extract the most prominent pitch at each time frame
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                pitch_values.append(pitch)
            
            # Convert to numpy array and filter out zeros
            pitch_values = np.array(pitch_values)
            
            # Alternative: use pyin for better pitch detection
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, 
                fmin=librosa.note_to_hz('C2'), 
                fmax=librosa.note_to_hz('C7'),
                sr=sr,
                hop_length=self.hop_length
            )
            
            # Use pyin results if available
            if f0 is not None:
                pitch_values = f0
            
            return pitch_values, voiced_flag if f0 is not None else None
            
        except Exception as e:
            raise Exception(f"Failed to extract pitch: {str(e)}")
    
    def frequency_to_midi(self, frequency: float) -> int:
        """Convert frequency in Hz to MIDI note number"""
        if frequency <= 0:
            return 0
        
        # Formula: MIDI = 69 + 12 * log2(f/440)
        try:
            midi_note = 69 + 12 * np.log2(frequency / 440.0)
            return int(round(midi_note))
        except:
            return 0
    
    def quantize_to_frontend_frequencies(self, frequency: float) -> float:
        """Quantize frequency to nearest available frontend frequency"""
        if frequency <= 0:
            return 0.0
        
        # Find closest frequency in available frontend frequencies
        closest_freq = min(self.available_frequencies, key=lambda x: abs(x - frequency))
        return closest_freq
    
    def frequency_to_key(self, frequency: float) -> str:
        """Convert frequency to keyboard character using frontend mapping"""
        if frequency <= 0:
            return ' '  # Pause/silence
        
        # Quantize to available frequency first
        quantized_freq = self.quantize_to_frontend_frequencies(frequency)
        
        # Look up the key for this frequency
        return self.frequency_to_key.get(quantized_freq, 'a')  # Default to 'a' if not found
    
    def get_frequency_from_key(self, key: str) -> float:
        """Get frequency for a given key"""
        return self.frontend_mapping.get(key, 0.0)
    
    def segment_notes(self, pitch_values: np.ndarray, voiced_flag: Optional[np.ndarray] = None, 
                     time_per_frame: float = 0.023) -> List[Dict]:
        """Segment continuous pitch values into discrete notes"""
        if len(pitch_values) == 0:
            return []
        
        sequence = []
        current_frequency = None
        note_duration = 0
        min_note_duration = 0.1  # Minimum note duration in seconds
        
        for i, pitch in enumerate(pitch_values):
            # Check if this frame has a valid pitch
            is_voiced = voiced_flag[i] if voiced_flag is not None else pitch > 0
            
            if is_voiced and pitch > 0:
                # Quantize to frontend frequencies
                quantized_freq = self.quantize_to_frontend_frequencies(pitch)
                
                if current_frequency is None:
                    # Start new note
                    current_frequency = quantized_freq
                    note_duration = time_per_frame
                elif abs(current_frequency - quantized_freq) <= 5.0:  # Allow small frequency variations (5Hz tolerance)
                    # Continue current note
                    note_duration += time_per_frame
                else:
                    # Note changed, save previous note if long enough
                    if note_duration >= min_note_duration:
                        key = self.frequency_to_key(current_frequency)
                        sequence.append({
                            "key": key,
                            "frequency": round(current_frequency, 2)
                        })
                    
                    # Start new note
                    current_frequency = quantized_freq
                    note_duration = time_per_frame
            else:
                # Silence or unvoiced
                if current_frequency is not None:
                    # Save previous note if long enough
                    if note_duration >= min_note_duration:
                        key = self.frequency_to_key(current_frequency)
                        sequence.append({
                            "key": key,
                            "frequency": round(current_frequency, 2)
                        })
                    
                    # Add pause if silence is long enough
                    if note_duration >= min_note_duration:
                        sequence.append({
                            "key": " ",
                            "frequency": 0
                        })
                    
                    current_frequency = None
                    note_duration = 0
        
        # Save last note if exists
        if current_frequency is not None and note_duration >= min_note_duration:
            key = self.frequency_to_key(current_frequency)
            sequence.append({
                "key": key,
                "frequency": round(current_frequency, 2)
            })
        
        return sequence
    
    def analyze_audio_file(self, file_path: str) -> Dict:
        """Main method to analyze audio file and return JSON sequence"""
        try:
            # Load audio
            y, sr = self.load_audio(file_path)
            
            # Extract pitch
            pitch_values, voiced_flag = self.extract_pitch(y, sr)
            
            # Calculate time per frame
            time_per_frame = self.hop_length / sr
            
            # Segment into notes
            sequence = self.segment_notes(pitch_values, voiced_flag, time_per_frame)
            
            # Create output format
            result = {
                "version": "1.0",
                "sequence": sequence,
                "created": "2025-07-09T08:00:00.000Z",
                "source": "audio_analysis",
                "original_file": os.path.basename(file_path)
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

# Example usage and testing
if __name__ == "__main__":
    analyzer = AudioAnalyzer()
    
    # Test with a sample file (you would replace this with actual file path)
    try:
        # result = analyzer.analyze_audio_file("sample.wav")
        # print("Analysis complete!")
        # print(f"Found {len(result['sequence'])} notes")
        # 
        # # Save to file
        # analyzer.save_json(result, "analyzed_music.json")
        
        print("AudioAnalyzer initialized successfully!")
        print("Available note mappings:")
        for midi, key in sorted(analyzer.note_mapping.items()):
            freq = analyzer.midi_to_frequency(midi)
            print(f"  {key}: MIDI {midi} = {freq:.2f} Hz")
            
    except Exception as e:
        print(f"Error: {e}")