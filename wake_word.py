import os
import struct
import sys
import time
from datetime import datetime

# Dependencies
import speech_recognition as sr
import pvporcupine
import pyaudio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WakeWordDetector:
    def __init__(self):
        self.porcupine_key = os.getenv("PORCUPINE_ACCESS_KEY")
        # Determine the path to the .ppn file
        # Priority: Hello Mirage -> Hey Mirage -> Fallback internal default
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.keyword_paths = []
        
        # Look for the specific file mentioned in requirements
        potential_files = [
            "Hello-Mirage_en_windows_v4_0_0.ppn",
            "Hey-MIRAGE_en_windows_v4_0_0.ppn",
            "Jarvis_en_windows_v3_0_0.ppn"
        ]
        
        for p_file in potential_files:
            full_path = os.path.join(current_dir, p_file)
            if os.path.exists(full_path):
                self.keyword_paths.append(full_path)
                print(f"[WAKE WORD SETUP] Found primary model: {p_file}")
                break # Just use the first valid one found based on priority
        
        self.porcupine = None
        self.pa = None
        self.audio_stream = None

    def _initialize_porcupine(self):
        """Attempts to initialize Porcupine. Returns True if successful."""
        if not self.porcupine_key:
            print("[WAKE WORD] No PORCUPINE_ACCESS_KEY found in .env")
            return False
            
        if not self.keyword_paths:
            print("[WAKE WORD] No .ppn files found.")
            return False

        try:
            self.porcupine = pvporcupine.create(
                access_key=self.porcupine_key,
                keyword_paths=self.keyword_paths
            )
            
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print(f"[WAKE WORD] Porcupine initialized using {self.keyword_paths[0]}")
            return True
            
        except Exception as e:
            print(f"[WAKE WORD] Porcupine initialization failed: {e}")
            self._cleanup_porcupine()
            return False

    def _cleanup_porcupine(self):
        """Safely cleans up Porcupine resources."""
        if self.audio_stream is not None:
            self.audio_stream.close()
            self.audio_stream = None
        if self.pa is not None:
            self.pa.terminate()
            self.pa = None
        if self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None

    def _listen_primary(self):
        """
        Listens using Porcupine. 
        Returns True if wake word detected. 
        Raises Exception if stream fails, triggering fallback.
        """
        if not self.porcupine or not self.audio_stream:
            raise RuntimeError("Porcupine not initialized")

        print("[WAKE WORD] Using Porcupine... Listening for 'Hello Mirage'")
        
        # We listen in a loop here, but we also need to allow checking for exceptions
        while True:
            try:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("[WAKE WORD] MIRAGE Activated (Primary)")
                    return True
            except OSError as e:
                # Audio device error possibly
                 raise e
            except Exception as e:
                 raise e

    def _listen_fallback(self):
        """
        Listens using SpeechRecognition (Google/Offline).
        Returns True if wake word detected.
        """
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 400  # Initial guess, dynamic will adjust
        
        # Keywords to trigger
        triggers = ["hello mirage", "hey mirage", "hi mirage", "mirage"]
        
        print("[WAKE WORD] Porcupine failed — switching to fallback")
        print("[WAKE WORD] Using Speech fallback... Listening...")

        mic = sr.Microphone()
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
        while True:
            try:
                with mic as source:
                    # Short timeout to keep loop responsive, phrase_time_limit to avoid long creates
                    audio = recognizer.listen(source, timeout=1.0, phrase_time_limit=3.0)
                
                # Recognize
                try:
                    # Using google for better accuracy in hackathon setting
                    # For offline, one would use sphinx, but it's less accurate for specific phrases without tuning
                    text = recognizer.recognize_google(audio).lower()
                    # print(f"[DEBUG] Heard: {text}") # Optional debug
                    
                    if any(trigger in text for trigger in triggers):
                        print(f"[WAKE WORD] MIRAGE Activated (Fallback: '{text}')")
                        return True
                        
                except sr.UnknownValueError:
                    pass # Heard nothing intelligible
                except sr.RequestError:
                    print("[WAKE WORD] Network error in fallback. Retrying...")
                    time.sleep(1)
                    
            except sr.WaitTimeoutError:
                continue # Just loop back
            except KeyboardInterrupt:
                return False
            except Exception as e:
                print(f"[WAKE WORD] Fallback error: {e}")
                time.sleep(1)

    def listen(self):
        """
        Main entry point. 
        Tries Primary -> Falls back -> Returns True when detected.
        """
        # 1. Try Initialize Primary
        use_primary = self._initialize_porcupine()
        
        detected = False
        
        try:
            if use_primary:
                try:
                    detected = self._listen_primary()
                except Exception as e:
                    print(f"[WAKE WORD] Primary crashed: {e}")
                    self._cleanup_porcupine()
                    use_primary = False 
            
            # 2. If Primary failed or wasn't used, run Fallback
            if not use_primary and not detected:
                 detected = self._listen_fallback()
                 
        except KeyboardInterrupt:
            print("\n[WAKE WORD] Stopped by user.")
            return False
        finally:
            self._cleanup_porcupine()
            
        return detected

# Standalone execution for testing
if __name__ == "__main__":
    detector = WakeWordDetector()
    while True:
        if detector.listen():
            # In a real app, you would break or trigger the main bot here
            # For this test script, we just loop to show it can detect again
            print("--> Handing off to main logic... (Simulation)")
            print("--> Main logic finished. Waiting for wake word again...\n")
            time.sleep(1)
