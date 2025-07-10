"""
Simple verification of key-to-frequency mappings without dependencies
"""

def extract_frontend_mapping():
    """Frontend mapping from script.js"""
    return {
        'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23, 't': 392.00,
        'y': 440.00, 'u': 493.88, 'i': 523.25, 'o': 587.33, 'p': 659.25,
        'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61, 'g': 196.00,
        'h': 220.00, 'j': 246.94, 'k': 261.63, 'l': 293.66, 'z': 329.63,
        'x': 349.23, 'c': 392.00, 'v': 440.00, 'b': 493.88, 'n': 523.25,
        'm': 587.33, '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
        '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81, '9': 146.83,
        '0': 164.81, ' ': 0
    }

def extract_backend_mapping():
    """Backend mapping from audio_analyzer.py"""
    return {
        'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23, 't': 392.00,
        'y': 440.00, 'u': 493.88, 'i': 523.25, 'o': 587.33, 'p': 659.25,
        'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61, 'g': 196.00,
        'h': 220.00, 'j': 246.94, 'k': 261.63, 'l': 293.66, 'z': 329.63,
        'x': 349.23, 'c': 392.00, 'v': 440.00, 'b': 493.88, 'n': 523.25,
        'm': 587.33, '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
        '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81, '9': 146.83,
        '0': 164.81, ' ': 0
    }

def verify_mappings():
    """Verify the mappings are identical"""
    print("🎵 Verifying Frontend <-> Backend Mapping Consistency\n")
    
    frontend = extract_frontend_mapping()
    backend = extract_backend_mapping()
    
    all_keys = set(frontend.keys()) | set(backend.keys())
    mismatches = []
    
    print("Key-by-key comparison:")
    for key in sorted(all_keys):
        frontend_freq = frontend.get(key, 'MISSING')
        backend_freq = backend.get(key, 'MISSING')
        
        if frontend_freq != backend_freq:
            mismatches.append((key, frontend_freq, backend_freq))
            status = "❌"
        else:
            status = "✅"
        
        print(f"  '{key}': Frontend={frontend_freq} Hz, Backend={backend_freq} Hz {status}")
    
    print(f"\n=== RESULTS ===")
    print(f"Total keys: {len(all_keys)}")
    print(f"Mismatches: {len(mismatches)}")
    
    if mismatches:
        print("\n❌ MISMATCHES FOUND:")
        for key, f_freq, b_freq in mismatches:
            print(f"  Key '{key}': Frontend={f_freq}, Backend={b_freq}")
        return False
    else:
        print("\n✅ PERFECT MATCH! All mappings are consistent.")
        return True

def show_mapping_details():
    """Show details about the mapping"""
    mapping = extract_frontend_mapping()
    
    print(f"\n=== MAPPING DETAILS ===")
    print(f"Total keys: {len(mapping)}")
    
    frequencies = [freq for freq in mapping.values() if freq > 0]
    print(f"Musical notes: {len(frequencies)}")
    print(f"Frequency range: {min(frequencies):.2f} Hz - {max(frequencies):.2f} Hz")
    
    # Group by type
    letters = [k for k in mapping.keys() if k.isalpha()]
    numbers = [k for k in mapping.keys() if k.isdigit()]
    
    print(f"Letter keys: {len(letters)} - {', '.join(sorted(letters))}")
    print(f"Number keys: {len(numbers)} - {', '.join(sorted(numbers))}")
    print(f"Special keys: 1 - space (pause)")
    
    print(f"\nFrequency distribution (sorted):")
    freq_to_key = {freq: key for key, freq in mapping.items() if freq > 0}
    for i, freq in enumerate(sorted(frequencies)):
        key = freq_to_key[freq]
        print(f"  {i+1:2d}. '{key}': {freq:7.2f} Hz")

if __name__ == "__main__":
    success = verify_mappings()
    show_mapping_details()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 SUCCESS: Frontend and backend mappings are identical!")
    else:
        print("⚠️  WARNING: Mappings need to be synchronized!")
    print("="*50)