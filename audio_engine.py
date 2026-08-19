"""
Far-Field Audio Engine for Jarvis
Handles robust, far-field speech recognition with automatic volume normalization,
dynamic threshold capping, and anti-infinite-loop safeguards.
"""

import speech_recognition as sr
import pyaudio
import threading
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


class AudioManager:
    def __init__(self):
        self.pa = None
        self.stream = None
        self.lock = threading.Lock()
        self.energy_threshold = 300
        self.calibrated = False
        
        # Centralized configurations
        self.MIC_CALIBRATION_DURATION = 1.0
        self.MIC_ENERGY_THRESHOLD_DEFAULT = 300
        self.MIC_DYNAMIC_ENERGY = True
        self.MIC_TIMEOUT = 5
        self.MIC_PHRASE_TIME_LIMIT = 15

    def initialize_mic(self):
        """Initializes PyAudio interface once."""
        with self.lock:
            if not self.pa:
                print("[AUDIO] Initializing microphone")
                self.pa = pyaudio.PyAudio()
                print("[AUDIO] Microphone initialized")

    def start_stream(self):
        """Opens and starts PyAudio input stream."""
        self.initialize_mic()
        with self.lock:
            if not self.stream:
                print("[AUDIO] Opening microphone stream...")
                self.stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024
                )
                print("[AUDIO] Microphone stream opened successfully.")

    def stop_stream(self):
        """Stops and closes PyAudio input stream cleanly."""
        with self.lock:
            if self.stream:
                print("[AUDIO] Releasing microphone stream...")
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    print(f"[AUDIO] Error stopping stream: {e}")
                self.stream = None
                print("[AUDIO] Microphone stream released.")

    def clear_buffer(self):
        """Discards any stale frames in the stream buffer."""
        with self.lock:
            if self.stream:
                try:
                    available = self.stream.get_read_available()
                    if available > 0:
                        self.stream.read(available, exception_on_overflow=False)
                except Exception as e:
                    print(f"[AUDIO] Error clearing stream buffer: {e}")

    def calibrate_ambient_noise(self, duration=1.0):
        """Calibrates baseline energy threshold once based on ambient room noise."""
        self.start_stream()
        print(f"[AUDIO] Starting ambient noise calibration for {duration}s...")
        
        # Read frames for duration and find average energy
        num_frames = int(16000 / 1024 * duration)
        energies = []
        
        for _ in range(num_frames):
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                if len(samples) > 0:
                    energy = np.sqrt(np.mean(samples**2))
                    energies.append(energy)
            except Exception as e:
                pass
            time.sleep(0.01)
            
        if energies:
            avg_energy = sum(energies) / len(energies)
            # Energy trigger is typically 1.5 - 2.0x average ambient noise
            self.energy_threshold = max(avg_energy * 1.8, 150.0)
            self.energy_threshold = min(self.energy_threshold, 1500.0)  # cap at 1500
            self.calibrated = True
            print(f"[AUDIO] Ambient noise calibration complete. Threshold set to: {self.energy_threshold:.2f}")
        else:
            self.energy_threshold = self.MIC_ENERGY_THRESHOLD_DEFAULT
            print(f"[AUDIO] Calibration failed. Using default energy threshold: {self.energy_threshold}")

    def read_chunk(self):
        """Reads a chunk of raw audio frames."""
        if not self.stream:
            self.start_stream()
        return self.stream.read(1024, exception_on_overflow=False)

    def close(self):
        """Releases all PyAudio resources completely."""
        self.stop_stream()
        with self.lock:
            if self.pa:
                print("[AUDIO] Closing PyAudio interface...")
                self.pa.terminate()
                self.pa = None
                print("[AUDIO] PyAudio interface closed.")

