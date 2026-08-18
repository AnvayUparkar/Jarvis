"""
Far-Field Audio Engine for Jarvis
Handles robust, far-field speech recognition with automatic volume normalization,
dynamic threshold capping, and anti-infinite-loop safeguards.
"""

import speech_recognition as sr
import time
import math
import struct

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("[⚠️ AUDIO ENGINE] numpy not found. Using struct for normalization (slower).")

def get_tuned_recognizer():
    """Returns a highly tuned SpeechRecognition Recognizer object for far-field audio."""
    r = sr.Recognizer()
    
    # Enable dynamic adjustment to adapt to the room's noise floor.
    r.dynamic_energy_threshold = True
    
    # 1.2 ratio is sensitive enough for distant voices (20% over ambient)
    # but safe enough to prevent triggering on fan noise (which 1.1 might trigger).
    r.dynamic_energy_ratio = 1.2
    
    # Minimum audio energy to trigger recording
    r.energy_threshold = 300 
    
    # Pause threshold: How long of a pause (in seconds) signifies the end of a phrase.
    # 0.8 allows a natural breath in a long sentence.
    r.pause_threshold = 0.8
    
    # Phrase threshold: Minimum seconds of speech to be considered a phrase (ignores clicks).
    r.phrase_threshold = 0.3
    
    # Non-speaking duration: Padding kept before/after the phrase to help the ML model.
    r.non_speaking_duration = 0.4
    
    return r

def normalize_audio(audio_data, quiet=False):
    """
    Normalizes the volume of the audio data.
    If the user is far away, the microphone records very low amplitudes.
    This applies a digital gain to boost the volume before sending to Google,
    massively improving far-field recognition accuracy.
    """
    raw_data = audio_data.frame_data
    sample_width = audio_data.sample_width
    sample_rate = audio_data.sample_rate
    
    # Only support 16-bit audio (which is default for sr.Microphone)
    if sample_width != 2:
        return audio_data
        
    if not quiet: print(f"[🔊 AUDIO ENGINE] Normalizing audio ({len(raw_data)} bytes)...")
    
    if NUMPY_AVAILABLE:
        # Fast numpy normalization
        audio_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
        max_amp = np.max(np.abs(audio_array))
        
        if max_amp == 0:
            return audio_data
            
        # Target max amplitude (about 70% of max int16 to avoid clipping)
        target_amp = 20000.0
        
        if max_amp < target_amp:
            gain = target_amp / max_amp
            # Cap maximum gain so we don't blow up background noise
            gain = min(gain, 4.0) 
            
            print(f"[🔊 AUDIO ENGINE] Distant voice detected. Max amp: {max_amp:.0f}. Applying {gain:.2f}x gain.")
            audio_array = audio_array * gain
            
            # Clip and convert back
            audio_array = np.clip(audio_array, -32768, 32767).astype(np.int16)
            normalized_raw = audio_array.tobytes()
            
            return sr.AudioData(normalized_raw, sample_rate, sample_width)
        else:
            print(f"[🔊 AUDIO ENGINE] Voice is loud enough (Max amp: {max_amp:.0f}). No gain applied.")
            if max_amp > 32000:
                 print("[⚠️ AUDIO ENGINE] Warning: Audio is clipping. Please lower microphone volume.")
            return audio_data
    else:
        # Fallback using struct
        num_samples = len(raw_data) // 2
        samples = struct.unpack(f"<{num_samples}h", raw_data)
        max_amp = max(abs(s) for s in samples) if samples else 0
        
        if max_amp == 0:
            return audio_data
            
        target_amp = 20000.0
        if max_amp < target_amp:
            gain = min(target_amp / max_amp, 4.0)
            print(f"[🔊 AUDIO ENGINE] Distant voice. Max amp: {max_amp}. Applying {gain:.2f}x gain.")
            
            normalized_samples = [int(max(-32768, min(32767, s * gain))) for s in samples]
            normalized_raw = struct.pack(f"<{num_samples}h", *normalized_samples)
            return sr.AudioData(normalized_raw, sample_rate, sample_width)
            
    return audio_data

def smart_listen(recognizer, source, timeout=15, phrase_time_limit=15, calibrate=True, quiet=False):
    """
    Listens intelligently with ambient noise calibration, threshold capping,
    and strict limits to prevent infinite loops.
    """
    if calibrate:
        if not quiet: print("[🎙️ AUDIO ENGINE] Calibrating to room noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        # Cap the threshold so it doesn't get deafened by loud fans
        if recognizer.energy_threshold > 1500:
            if not quiet: print(f"[⚠️ AUDIO ENGINE] Room is very noisy! Capping threshold from {recognizer.energy_threshold:.0f} down to 1500.")
            recognizer.energy_threshold = 1500
        
        # Floor the threshold so it doesn't trigger on absolute silence
        elif recognizer.energy_threshold < 150:
            if not quiet: print(f"[⚠️ AUDIO ENGINE] Room is very quiet! Raising threshold from {recognizer.energy_threshold:.0f} up to 150.")
            recognizer.energy_threshold = 150
        else:
            if not quiet: print(f"[🎙️ AUDIO ENGINE] Dynamic threshold set to: {recognizer.energy_threshold:.0f}")

    if not quiet: print("[🎙️ AUDIO ENGINE] Listening...")
    
    # Record audio with strict limits
    # timeout: max time to wait for a phrase to START
    # phrase_time_limit: max time to let a phrase CONTINUE (prevents infinite loop if background noise is constant)
    audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    
    # Normalize volume before returning
    return normalize_audio(audio_data, quiet=quiet)
