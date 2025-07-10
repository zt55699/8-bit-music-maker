"""
Advanced Audio Analyzer for 8-bit Music Maker
Implements Demucs → Lead Selection → Improved Pitch Detection pipeline
"""

import librosa
import numpy as np
import soundfile as sf
import os
import uuid
import tempfile
import psutil
import gc
from datetime import datetime
from scipy.signal import medfilt
from demucs.pretrained import get_model
from demucs.apply import apply_model
import torch
from tqdm import tqdm


class AdvancedAudioAnalyzer:
    def __init__(self):
        """Initialize the advanced audio analyzer with Demucs and improved pipeline"""
        
        # Complete frequency to key mapping (exact match with frontend)
        self.freq_to_key_map = {
            65.41: '1', 73.42: '2', 82.41: '3', 87.31: '4', 98.00: '5',
            110.00: '6', 123.47: '7', 130.81: 'a', 146.83: 's', 164.81: 'd',
            174.61: 'f', 196.00: 'g', 220.00: 'h', 246.94: 'j', 261.63: 'k',
            293.66: 'l', 329.63: 'z', 349.23: 'x', 392.00: 'c', 440.00: 'v',
            493.88: 'b', 523.25: 'n', 587.33: 'm', 659.25: 'p'
        }
        
        # C major pentatonic frequencies for quantization (as per your suggestion)
        self.pentatonic_freqs = [
            130.81, 146.83, 164.81, 196.00, 220.00,  # C D E G A (octave 3)
            261.63, 293.66, 329.63, 392.00, 440.00,  # C D E G A (octave 4)
            523.25, 587.33, 659.25                   # C D E (octave 5)
        ]
        
        # Available frequencies for final quantization
        self.available_frequencies = sorted(self.freq_to_key_map.keys())
        
        # Load Demucs model
        print("Loading Demucs model for source separation...")
        self.demucs_model = get_model('htdemucs_ft')
        print(f"Advanced Audio Analyzer initialized with Demucs {self.demucs_model}")

    def clear_cache(self):
        """Clear any cached state to ensure clean analysis"""
        # Force garbage collection to free up memory
        gc.collect()
        # Clear any torch cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("🧹 Analyzer cache cleared")

    def choose_lead_stem(self, stems, sr):
        """
        Choose the lead stem using spectral centroid and energy heuristics
        Based on your suggestion for 8-bit game audio analysis
        """
        print("Analyzing stems to find lead track...")
        
        best_stem = None
        best_score = -1
        stem_scores = {}
        
        for name, y in stems.items():
            if len(y.shape) > 1:
                y = y.mean(axis=0)  # Convert to mono if stereo
            
            # Skip if stem is too quiet
            if np.max(np.abs(y)) < 0.001:
                stem_scores[name] = 0
                continue
            
            # Compute STFT for frequency analysis
            S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
            
            # Find 2-5 kHz band (where NES pulse leads sit)
            band_start = np.argmax(freqs >= 2000)
            band_end = np.argmax(freqs >= 5000)
            if band_end == 0:
                band_end = len(freqs)
            
            band_energy = S[band_start:band_end].mean(axis=0)
            
            # Compute spectral centroid variance
            spec_cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
            sc_var = spec_cent.var()
            
            # Combined score: energy in pulse band * spectral centroid variance
            score = band_energy.max() * sc_var
            stem_scores[name] = score
            
            print(f"  {name}: band_energy={band_energy.max():.6f}, sc_var={sc_var:.2f}, score={score:.6f}")
            
            if score > best_score:
                best_score = score
                best_stem = y
        
        print(f"Selected stem with highest score: {best_score:.6f}")
        print(f"Stem scores: {stem_scores}")
        
        return best_stem

    def snap_to_pentatonic(self, frequency):
        """Snap frequency to C major pentatonic first, then to keyboard table"""
        if frequency <= 0 or not np.isfinite(frequency):
            return 0
        
        # Clamp frequency to reasonable range to avoid librosa.hz_to_midi() issues
        frequency = max(20, min(frequency, 8000))  # 20Hz to 8kHz
        
        try:
            # First snap to pentatonic
            pentatonic_freq = min(self.pentatonic_freqs,
                                 key=lambda x: abs(librosa.hz_to_midi(x) - librosa.hz_to_midi(frequency)))
            
            # Then snap to available keyboard frequencies
            final_freq = min(self.available_frequencies,
                            key=lambda x: abs(librosa.hz_to_midi(x) - librosa.hz_to_midi(pentatonic_freq)))
            
            return final_freq
        except Exception as e:
            print(f"Warning: snap_to_pentatonic failed for freq {frequency}: {e}")
            # Fallback to closest available frequency
            return min(self.available_frequencies, key=lambda x: abs(x - frequency))

    def frequency_to_key(self, frequency):
        """Convert frequency to the closest available key"""
        if frequency == 0 or frequency is None:
            return ' '
        
        return self.freq_to_key_map.get(frequency, ' ')

    def merge_consecutive_notes(self, sequence, threshold_frames=1):
        """Merge consecutive identical notes separated by ≤ threshold frames"""
        if not sequence:
            return sequence
        
        merged = []
        current_note = sequence[0].copy()
        
        for next_note in sequence[1:]:
            # Check if notes are identical and close in time
            time_gap = next_note['start_time'] - (current_note['start_time'] + current_note['duration'])
            
            if (current_note['key'] == next_note['key'] and 
                current_note['frequency'] == next_note['frequency'] and
                time_gap <= threshold_frames * 0.008):  # 8ms threshold
                
                # Merge notes by extending duration
                current_note['duration'] += next_note['duration'] + time_gap
            else:
                # Different note, save current and start new
                merged.append(current_note)
                current_note = next_note.copy()
        
        # Add final note
        merged.append(current_note)
        
        return merged

    def update_progress(self, job_id, progress_store, progress_lock, stage, message, progress=None, debug_info=None):
        """Update progress for SSE tracking with detailed debug info"""
        if job_id and progress_store is not None and progress_lock is not None:
            with progress_lock:
                if job_id in progress_store:
                    progress_store[job_id]['stage'] = stage
                    progress_store[job_id]['message'] = message
                    if progress is not None:
                        progress_store[job_id]['progress'] = progress
                    if debug_info is not None:
                        progress_store[job_id]['debug'] = debug_info
        
        # Always print to console for debugging
        debug_str = f" | {debug_info}" if debug_info else ""
        print(f"[PROGRESS] Stage {stage}: {message}{debug_str}")

    def analyze_audio_file_with_progress(self, file_path, bpm_hint=120, job_id=None, progress_store=None, progress_lock=None):
        """
        Advanced audio analysis with SSE progress tracking
        """
        return self.analyze_audio_file(file_path, bpm_hint, True, job_id, progress_store, progress_lock)

    def analyze_audio_file(self, file_path, bpm_hint=120, show_progress=True, job_id=None, progress_store=None, progress_lock=None):
        """
        Advanced audio analysis using Demucs → Lead Selection → Improved Pitch Detection
        
        Args:
            file_path: Path to audio file
            bpm_hint: BPM hint for dynamic timing thresholds
            show_progress: Whether to show progress bars
            
        Returns:
            dict: Analysis result with sequence, timing info
        """
        print(f"🎵 Starting advanced audio analysis of: {file_path}")
        print(f"🎼 BPM hint: {bpm_hint}")
        print()
        
        # Create overall progress bar
        if show_progress:
            overall_pbar = tqdm(total=7, desc="Overall Progress", unit="stage", 
                              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        
        try:
            # Stage 1: Load audio
            self.update_progress(job_id, progress_store, progress_lock, 1, "🔊 Loading audio file", 10, f"File: {file_path}")
            if show_progress:
                overall_pbar.set_description("🔊 Loading audio file")
            
            y, sr = librosa.load(file_path, sr=44100, mono=False)  # Keep stereo for Demucs
            if len(y.shape) == 1:
                # Convert mono to stereo for Demucs
                y = np.stack([y, y])  # Duplicate mono to both channels
            
            audio_duration = y.shape[-1] / sr
            self.update_progress(job_id, progress_store, progress_lock, 1, "✅ Audio loaded", 20, 
                               f"Shape: {y.shape}, SR: {sr}Hz, Duration: {audio_duration:.2f}s")
            if show_progress:
                overall_pbar.update(1)
                print(f"✅ Loaded audio: {y.shape} at {sr} Hz ({y.shape[-1]/sr:.2f} seconds)")
            
            # Stage 2: Source separation with Demucs
            self.update_progress(job_id, progress_store, progress_lock, 2, "🎛️ Separating audio stems", 25, "Initializing Demucs...")
            if show_progress:
                overall_pbar.set_description("🎛️ Separating audio stems")
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(y).float()
            self.update_progress(job_id, progress_store, progress_lock, 2, "🎛️ Running Demucs separation", 30, 
                               f"Processing {audio_duration:.1f}s of audio...")
            
            # Apply Demucs model with progress
            with torch.no_grad():
                separated = apply_model(self.demucs_model, audio_tensor[None], device='cpu')[0]
            
            # Extract stems
            stems = {
                'drums': separated[0].numpy(),
                'bass': separated[1].numpy(), 
                'other': separated[2].numpy(),
                'vocals': separated[3].numpy()
            }
            
            # Analyze stem energy levels
            stem_energies = {name: np.max(np.abs(stem)) for name, stem in stems.items()}
            self.update_progress(job_id, progress_store, progress_lock, 2, "✅ Stems separated", 40, 
                               f"Energy levels: {stem_energies}")
            if show_progress:
                overall_pbar.update(1)
                print(f"✅ Separated into {len(stems)} stems")
            
            # Stage 3: Choose lead stem
            self.update_progress(job_id, progress_store, progress_lock, 3, "🎯 Selecting lead stem", 45, "Analyzing stem characteristics...")
            if show_progress:
                overall_pbar.set_description("🎯 Selecting lead stem")
            
            lead_audio = self.choose_lead_stem(stems, sr)
            
            if lead_audio is None:
                raise ValueError("Could not identify lead stem")
            
            lead_energy = np.max(np.abs(lead_audio))
            self.update_progress(job_id, progress_store, progress_lock, 3, "✅ Lead stem selected", 50, 
                               f"Lead stem energy: {lead_energy:.6f}")
            if show_progress:
                overall_pbar.update(1)
                print(f"✅ Lead stem selected")
            
            # Stage 4: Improved pitch detection on lead stem
            self.update_progress(job_id, progress_store, progress_lock, 4, "🎼 Detecting pitch and notes", 55, "Running PYIN analysis...")
            if show_progress:
                overall_pbar.set_description("🎼 Detecting pitch and notes")
            
            # Use higher resolution for game music
            hop_length = 128  # ~3ms at 44.1kHz (vs 5.8ms with 256)
            
            # Extract fundamental frequency using PYIN
            f0, voiced_flag, voiced_probs = librosa.pyin(
                lead_audio,
                fmin=65,        # C2 (lowest note we support)
                fmax=700,       # Slightly above our highest note
                sr=sr,
                hop_length=hop_length,
                fill_na=0
            )
            
            # Apply median filtering to reduce noise
            f0_smoothed = medfilt(f0, kernel_size=3)
            
            # Convert to time stamps
            times = librosa.times_like(f0_smoothed, sr=sr, hop_length=hop_length)
            
            # Count detection stats
            total_frames = len(f0_smoothed)
            freq_detected = np.sum(f0_smoothed > 0)
            high_confidence = np.sum(voiced_probs > 0.01)
            
            self.update_progress(job_id, progress_store, progress_lock, 4, "✅ Pitch detection complete", 65, 
                               f"Frames: {total_frames}, Freq>0: {freq_detected}, Confident: {high_confidence}")
            if show_progress:
                overall_pbar.update(1)
                print(f"✅ Extracted {len(f0)} fundamental frequency frames")
            
            # Stage 5: Beat-relative duration system
            self.update_progress(job_id, progress_store, progress_lock, 5, "🥁 Tracking rhythm and tempo", 70, "Analyzing beats...")
            if show_progress:
                overall_pbar.set_description("🥁 Tracking rhythm and tempo")
            
            try:
                tempo, beats = librosa.beat.beat_track(y=lead_audio, sr=sr, hop_length=hop_length)
                
                # Use detected tempo, fall back to hint if detection fails
                if tempo < 60 or tempo > 200:
                    tempo = bpm_hint
                    tempo_source = "BPM hint"
                else:
                    tempo_source = "detected"
            except Exception as e:
                tempo = bpm_hint
                tempo_source = f"BPM hint (beat tracking failed: {str(e)})"
            
            # Dynamic minimum note duration (much shorter for game music)
            min_note_duration_beats = 0.125  # Thirty-second note in beats
            min_note_duration_sec = 60.0 / float(tempo) * min_note_duration_beats
            min_frames = max(1, int(min_note_duration_sec * sr / hop_length))  # At least 1 frame
            
            self.update_progress(job_id, progress_store, progress_lock, 5, f"✅ Tempo: {float(tempo):.1f} BPM", 75, 
                               f"Source: {tempo_source}, Min frames: {min_frames}")
            if show_progress:
                overall_pbar.update(1)
                print(f"✅ Tempo: {float(tempo):.1f} BPM ({tempo_source})")
                print(f"   Min note duration: {min_note_duration_sec:.3f}s ({min_frames} frames)")
            
            # Stage 6: Note extraction with pentatonic quantization
            self.update_progress(job_id, progress_store, progress_lock, 6, "🎹 Extracting and quantizing notes", 80, 
                               f"Processing {len(f0_smoothed)} frames...")
            if show_progress:
                overall_pbar.set_description("🎹 Extracting and quantizing notes")
            
            sequence = []
            current_freq = None
            current_start_time = None
            current_frame_count = 0
            
            # Process frames with progress bar and timeout handling
            frame_pbar = tqdm(enumerate(zip(times, f0_smoothed)), total=len(times), 
                            desc="Processing frames", unit="frame", leave=False,
                            disable=not show_progress)
            
            voiced_frame_count = 0
            detected_freq_count = 0
            frame_errors = 0
            
            import time as time_module
            start_time = time_module.time()
            timeout_seconds = 120  # 2 minute timeout for frame processing
            last_progress_time = start_time
            
            for i, (time, freq) in frame_pbar:
                # Aggressive timeout check every 500 frames or if no progress for 30 seconds
                current_time = time_module.time()
                if i % 500 == 0 or (current_time - last_progress_time) > 30:
                    elapsed = current_time - start_time
                    if elapsed > timeout_seconds:
                        print(f"⚠️ Frame processing timeout after {elapsed:.1f}s at frame {i}/{len(times)}")
                        print(f"   Processed: {voiced_frame_count} voiced frames, {detected_freq_count} with frequency")
                        # Update progress to indicate timeout
                        self.update_progress(job_id, progress_store, progress_lock, 6, 
                                           f"⚠️ Processing timeout at frame {i}/{len(times)}", 
                                           80 + (i / len(times)) * 15, f"Timeout after {elapsed:.1f}s")
                        break
                    last_progress_time = current_time
                
                # Progress update every 2000 frames to reduce overhead
                if i % 2000 == 0 and i > 0:
                    progress = 80 + (i / len(times)) * 15  # 80-95% for frame processing
                    self.update_progress(job_id, progress_store, progress_lock, 6, 
                                       f"🎹 Processing frames ({i}/{len(times)})", 
                                       progress, f"Voiced: {voiced_frame_count}, Errors: {frame_errors}")
                
                try:
                    if freq > 0:
                        detected_freq_count += 1
                        
                    if freq > 0 and voiced_probs[i] > 0.01:  # Very low confidence threshold for complex music
                        voiced_frame_count += 1
                        
                        # Pentatonic then keyboard quantization with error handling
                        quantized_freq = self.snap_to_pentatonic(freq)
                        
                        # Check if this is the same note (within semitone tolerance)
                        if current_freq is not None and quantized_freq > 0:
                            try:
                                midi_diff = abs(librosa.hz_to_midi(quantized_freq) - librosa.hz_to_midi(current_freq))
                                is_same_note = midi_diff < 0.5
                            except Exception as e:
                                # If midi conversion fails, fall back to frequency comparison
                                freq_ratio = max(quantized_freq, current_freq) / min(quantized_freq, current_freq)
                                is_same_note = freq_ratio < 1.06  # ~1 semitone
                        else:
                            is_same_note = False
                    
                        if is_same_note:
                            # Continue current note
                            current_frame_count += 1
                        else:
                            # End previous note if it was long enough
                            if current_freq is not None and current_frame_count >= min_frames:
                                duration_sec = current_frame_count * hop_length / sr
                                duration_beats = duration_sec * float(tempo) / 60
                                duration_beats = round(float(duration_beats) * 4) / 4  # Quantize to 16th notes
                                
                                key = self.frequency_to_key(current_freq)
                                
                                sequence.append({
                                    'key': key,
                                    'frequency': current_freq,
                                    'duration': duration_beats,
                                    'start_time': current_start_time
                                })
                            
                            # Start new note
                            current_freq = quantized_freq
                            current_start_time = time
                            current_frame_count = 1
                        
                    else:  # Unvoiced frame or low confidence
                        # End current note if it exists and is long enough
                        if current_freq is not None and current_frame_count >= min_frames:
                            duration_sec = current_frame_count * hop_length / sr
                            duration_beats = duration_sec * float(tempo) / 60
                            duration_beats = round(float(duration_beats) * 4) / 4  # Quantize to 16th notes
                            
                            key = self.frequency_to_key(current_freq)
                            
                            sequence.append({
                                'key': key,
                                'frequency': current_freq,
                                'duration': duration_beats,
                                'start_time': current_start_time
                            })
                            
                            # Add pause if gap is significant
                            if len(sequence) > 0:
                                gap_duration_sec = time - (current_start_time + duration_sec)
                                if gap_duration_sec > min_note_duration_sec:
                                    gap_duration_beats = gap_duration_sec * float(tempo) / 60
                                    gap_duration_beats = round(float(gap_duration_beats) * 4) / 4
                                    
                                    if gap_duration_beats >= 0.25:  # Only add significant pauses
                                        sequence.append({
                                            'key': ' ',
                                            'frequency': 0,
                                            'duration': gap_duration_beats,
                                            'start_time': current_start_time + duration_sec
                                        })
                        
                        current_freq = None
                        current_frame_count = 0
                
                except Exception as e:
                    frame_errors += 1
                    if frame_errors <= 10:  # Only log first 10 errors to avoid spam
                        print(f"Warning: Frame {i} processing error: {e}")
                    continue
            
            # Handle final note
            if current_freq is not None and current_frame_count >= min_frames:
                duration_sec = current_frame_count * hop_length / sr
                duration_beats = duration_sec * float(tempo) / 60
                duration_beats = round(float(duration_beats) * 4) / 4
                
                key = self.frequency_to_key(current_freq)
                sequence.append({
                    'key': key,
                    'frequency': current_freq,
                    'duration': duration_beats,
                    'start_time': current_start_time
                })
            
            # Memory cleanup
            gc.collect()
            
            # Final frame processing stats
            extraction_stats = f"Raw: {len(sequence)}, Freq>0: {detected_freq_count}, Voiced: {voiced_frame_count}, Errors: {frame_errors}"
            memory_info = psutil.Process().memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            self.update_progress(job_id, progress_store, progress_lock, 6, f"✅ Extracted {len(sequence)} notes", 90, 
                               f"{extraction_stats}, Memory: {memory_mb:.1f}MB")
            if show_progress:
                frame_pbar.close()
                overall_pbar.update(1)
                print(f"✅ Extracted {len(sequence)} raw notes")
                print(f"   Debug: {detected_freq_count} frames with frequency > 0")
                print(f"   Debug: {voiced_frame_count} frames above confidence threshold")
                print(f"   Debug: min_frames = {min_frames}, min_duration = {min_note_duration_sec:.3f}s")
            
            # Stage 7: Post-processing
            initial_count = len(sequence)
            self.update_progress(job_id, progress_store, progress_lock, 7, "🔧 Post-processing and cleanup", 95, 
                               f"Starting with {initial_count} notes...")
            if show_progress:
                overall_pbar.set_description("🔧 Post-processing and cleanup")
            
            # Merge consecutive identical notes
            sequence = self.merge_consecutive_notes(sequence)
            after_merge = len(sequence)
            
            # Filter out very short notes (less than thirty-second note)
            sequence = [note for note in sequence if note['duration'] >= 0.125]
            final_count = len(sequence)
            
            processing_info = f"Initial: {initial_count} → Merged: {after_merge} → Final: {final_count}"
            # Don't send "Analysis complete!" yet - wait until result is fully created
            self.update_progress(job_id, progress_store, progress_lock, 6, f"🔧 Finalizing results", 95, processing_info)
            if show_progress:
                overall_pbar.update(1)
                overall_pbar.set_description("🔧 Finalizing results...")
                print(f"✅ Final sequence: {len(sequence)} notes after post-processing")
            
            # Create result
            result = {
                "version": "1.0",
                "sequence": sequence,
                "created": datetime.now().isoformat(),
                "source": "advanced_audio_analysis",
                "analysis_id": str(uuid.uuid4()),
                "original_filename": os.path.basename(file_path),
                "bpm_hint": bpm_hint,
                "detected_tempo": float(tempo),
                "tempo_source": tempo_source,
                "sample_rate": int(sr),
                "duration": float(y.shape[-1] / sr),
                "note_count": len(sequence),
                "analysis_params": {
                    "hop_length": hop_length,
                    "min_note_duration_beats": min_note_duration_beats,
                    "frequency_range": [65, 700],
                    "algorithm": "demucs+pyin+pentatonic",
                    "demucs_model": str(self.demucs_model),
                    "confidence_threshold": 0.01
                }
            }
            
            # NOW send the final completion message
            self.update_progress(job_id, progress_store, progress_lock, 7, f"✅ Analysis complete! {final_count} notes", 100, processing_info)
            if show_progress:
                overall_pbar.set_description("✅ Analysis complete!")
                overall_pbar.close()
                print()
            
            return result
            
        except Exception as e:
            print(f"Advanced audio analysis failed: {e}")
            raise RuntimeError(f"Advanced audio analysis failed: {str(e)}") from e


def test_advanced_analyzer():
    """Test the advanced analyzer"""
    print("Testing Advanced Audio Analyzer...")
    
    try:
        analyzer = AdvancedAudioAnalyzer()
        
        # Test with our simple test file
        test_file = "test_mario_stereo.wav"
        if os.path.exists(test_file):
            result = analyzer.analyze_audio_file(test_file, bpm_hint=120)
            
            print(f"Advanced analysis result: {len(result['sequence'])} notes detected")
            print(f"Detected tempo: {result['detected_tempo']:.1f} BPM")
            
            for i, note in enumerate(result['sequence'][:10]):  # Show first 10 notes
                print(f"  {i+1}: {note['key']} ({note['frequency']:.1f}Hz) - {note['duration']:.2f} beats")
            
            return result
        else:
            print("No test file found")
            return None
    
    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    test_advanced_analyzer()