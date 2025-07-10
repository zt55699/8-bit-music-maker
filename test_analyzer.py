"""
Test script for audio analyzer
Creates a synthetic test audio file and analyzes it
"""

import numpy as np
import scipy.io.wavfile as wavfile
import json
from audio_analyzer import AudioAnalyzer
import os

def create_test_audio():
    """Create a simple test audio file with known frequencies"""
    sample_rate = 22050
    duration = 5.0  # 5 seconds
    
    # Create a simple melody: C-D-E-F-G-F-E-D-C
    notes = [
        (261.63, 0.5),  # C4
        (293.66, 0.5),  # D4
        (329.63, 0.5),  # E4
        (349.23, 0.5),  # F4
        (392.00, 0.5),  # G4
        (0, 0.2),       # Pause
        (349.23, 0.5),  # F4
        (329.63, 0.5),  # E4
        (293.66, 0.5),  # D4
        (261.63, 0.5),  # C4
    ]
    
    # Generate audio
    audio = []
    for freq, note_duration in notes:
        samples = int(sample_rate * note_duration)
        if freq > 0:
            # Generate sine wave
            t = np.linspace(0, note_duration, samples)
            note_audio = 0.5 * np.sin(2 * np.pi * freq * t)
            
            # Add some envelope to make it more realistic
            envelope = np.exp(-t * 2)  # Exponential decay
            note_audio *= envelope
        else:
            # Silence
            note_audio = np.zeros(samples)
        
        audio.extend(note_audio)
    
    # Convert to numpy array and normalize
    audio = np.array(audio)
    audio = audio / np.max(np.abs(audio))
    
    # Convert to 16-bit integers
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Save as WAV file
    wavfile.write('test_melody.wav', sample_rate, audio_int16)
    print("Created test_melody.wav")
    
    return 'test_melody.wav'

def test_analyzer():
    """Test the audio analyzer with the synthetic audio"""
    print("Testing Audio Analyzer...")
    
    # Create test audio file
    test_file = create_test_audio()
    
    try:
        # Initialize analyzer
        analyzer = AudioAnalyzer()
        
        # Analyze the test file
        print("Analyzing test file...")
        result = analyzer.analyze_audio_file(test_file)
        
        # Print results
        print(f"\nAnalysis complete!")
        print(f"Found {len(result['sequence'])} notes/pauses")
        print("\nSequence:")
        for i, note in enumerate(result['sequence']):
            key = note['key']
            freq = note['frequency']
            if key == ' ':
                print(f"  {i+1}: PAUSE")
            else:
                print(f"  {i+1}: {key} ({freq} Hz)")
        
        # Save result
        with open('test_analysis.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nSaved analysis to test_analysis.json")
        
        # Clean up
        os.remove(test_file)
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_note_mapping():
    """Test the note mapping system"""
    print("Testing note mapping...")
    
    analyzer = AudioAnalyzer()
    
    # Test frequency quantization
    test_frequencies = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]
    
    print("\nFrequency quantization and mapping:")
    for freq in test_frequencies:
        quantized = analyzer.quantize_to_frontend_frequencies(freq)
        key = analyzer.frequency_to_key(quantized)
        back_to_freq = analyzer.get_frequency_from_key(key)
        print(f"  {freq} Hz -> quantized {quantized} Hz -> key '{key}' -> {back_to_freq:.2f} Hz")
    
    print("\nFrontend mapping table:")
    for key, freq in sorted(analyzer.frontend_mapping.items()):
        if freq > 0:
            print(f"  Key '{key}': {freq:.2f} Hz")
    
    print(f"\nTotal available frequencies: {len(analyzer.available_frequencies)}")
    print(f"Frequency range: {min(analyzer.available_frequencies):.2f} Hz - {max(analyzer.available_frequencies):.2f} Hz")

if __name__ == "__main__":
    print("=== 8-Bit Music Analyzer Test ===\n")
    
    # Test note mapping
    test_note_mapping()
    
    print("\n" + "="*50 + "\n")
    
    # Test analyzer with synthetic audio
    success = test_analyzer()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")