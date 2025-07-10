"""
Verify that frontend and backend key-to-frequency mappings are identical
"""

from audio_analyzer import AudioAnalyzer
import json

def extract_frontend_mapping():
    """Extract the frontend mapping from script.js"""
    # This is the mapping from script.js (lines 24-32)
    frontend_mapping = {
        'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23, 't': 392.00,
        'y': 440.00, 'u': 493.88, 'i': 523.25, 'o': 587.33, 'p': 659.25,
        'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61, 'g': 196.00,
        'h': 220.00, 'j': 246.94, 'k': 261.63, 'l': 293.66, 'z': 329.63,
        'x': 349.23, 'c': 392.00, 'v': 440.00, 'b': 493.88, 'n': 523.25,
        'm': 587.33, '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
        '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81, '9': 146.83,
        '0': 164.81, ' ': 0
    }
    return frontend_mapping

def verify_mappings():
    """Verify that frontend and backend mappings are identical"""
    print("=== Mapping Verification ===\n")
    
    # Get mappings
    frontend_map = extract_frontend_mapping()
    analyzer = AudioAnalyzer()
    backend_map = analyzer.frontend_mapping
    
    # Compare mappings
    print("Comparing frontend (script.js) with backend (audio_analyzer.py):")
    
    all_keys = set(frontend_map.keys()) | set(backend_map.keys())
    mismatches = []
    
    for key in sorted(all_keys):
        frontend_freq = frontend_map.get(key, 'MISSING')
        backend_freq = backend_map.get(key, 'MISSING')
        
        if frontend_freq != backend_freq:
            mismatches.append((key, frontend_freq, backend_freq))
            status = "❌ MISMATCH"
        else:
            status = "✅ MATCH"
        
        print(f"  Key '{key}': Frontend={frontend_freq} Hz, Backend={backend_freq} Hz - {status}")
    
    print(f"\n=== Summary ===")
    print(f"Total keys checked: {len(all_keys)}")
    print(f"Mismatches found: {len(mismatches)}")
    
    if mismatches:
        print("\n❌ MISMATCHES DETECTED:")
        for key, frontend, backend in mismatches:
            print(f"  Key '{key}': Frontend={frontend}, Backend={backend}")
        return False
    else:
        print("\n✅ ALL MAPPINGS MATCH!")
        return True

def test_round_trip():
    """Test round-trip conversion: frequency -> key -> frequency"""
    print("\n=== Round-trip Test ===\n")
    
    analyzer = AudioAnalyzer()
    
    # Test frequencies from the frontend mapping
    test_frequencies = [65.41, 98.00, 130.81, 174.61, 220.00, 261.63, 329.63, 440.00, 523.25, 659.25]
    
    print("Testing frequency -> key -> frequency conversion:")
    
    errors = []
    for original_freq in test_frequencies:
        # Convert frequency to key
        key = analyzer.frequency_to_key(original_freq)
        
        # Convert key back to frequency
        recovered_freq = analyzer.get_frequency_from_key(key)
        
        # Check if they match
        if abs(original_freq - recovered_freq) < 0.01:  # Allow small floating point errors
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            errors.append((original_freq, key, recovered_freq))
        
        print(f"  {original_freq} Hz -> '{key}' -> {recovered_freq} Hz - {status}")
    
    print(f"\n=== Round-trip Summary ===")
    print(f"Tests run: {len(test_frequencies)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\n❌ ROUND-TRIP ERRORS:")
        for orig, key, recovered in errors:
            print(f"  {orig} Hz -> '{key}' -> {recovered} Hz")
        return False
    else:
        print("\n✅ ALL ROUND-TRIP TESTS PASSED!")
        return True

def show_mapping_stats():
    """Show statistics about the mapping"""
    print("\n=== Mapping Statistics ===\n")
    
    analyzer = AudioAnalyzer()
    
    frequencies = [freq for freq in analyzer.available_frequencies if freq > 0]
    
    print(f"Total mapped keys: {len(analyzer.frontend_mapping)}")
    print(f"Musical notes (non-space): {len(frequencies)}")
    print(f"Frequency range: {min(frequencies):.2f} Hz - {max(frequencies):.2f} Hz")
    
    # Count keys by type
    letters = sum(1 for k in analyzer.frontend_mapping.keys() if k.isalpha())
    numbers = sum(1 for k in analyzer.frontend_mapping.keys() if k.isdigit())
    spaces = sum(1 for k in analyzer.frontend_mapping.keys() if k == ' ')
    
    print(f"Letter keys: {letters}")
    print(f"Number keys: {numbers}")
    print(f"Space keys: {spaces}")
    
    # Show frequency distribution
    print(f"\nFrequency distribution:")
    sorted_freqs = sorted(frequencies)
    for i, freq in enumerate(sorted_freqs):
        key = analyzer.frequency_to_key(freq)
        print(f"  {i+1:2d}. {key}: {freq:7.2f} Hz")

if __name__ == "__main__":
    print("🎵 8-Bit Music Maker - Mapping Verification Tool\n")
    
    # Run verification tests
    mapping_ok = verify_mappings()
    roundtrip_ok = test_round_trip()
    
    # Show statistics
    show_mapping_stats()
    
    # Final result
    print("\n" + "="*60)
    if mapping_ok and roundtrip_ok:
        print("🎉 ALL TESTS PASSED - Mappings are consistent!")
    else:
        print("⚠️  TESTS FAILED - Mappings need to be fixed!")
    print("="*60)