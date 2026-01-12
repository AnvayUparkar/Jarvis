"""
Activation Beep Module for Jarvis
==================================
Plays a short, pleasant beep sound when the "Jarvis" wake word is detected.
Uses pygame for cross-platform audio support.
"""

import pygame
import os
import numpy as np
from typing import Optional

# Configuration
BEEP_FREQUENCY = 880  # Hz (A5 note - pleasant, attention-grabbing)
BEEP_DURATION = 0.15  # seconds
BEEP_SAMPLE_RATE = 44100  # Hz


def generate_beep_sound(frequency: int = BEEP_FREQUENCY, 
                       duration: float = BEEP_DURATION,
                       sample_rate: int = BEEP_SAMPLE_RATE) -> pygame.mixer.Sound:
    """
    Generates a simple sine wave beep sound programmatically.
    
    Args:
        frequency: Frequency in Hz (default: 880 Hz - A5 note)
        duration: Duration in seconds (default: 0.15s)
        sample_rate: Sample rate in Hz (default: 44100 Hz)
        
    Returns:
        pygame.mixer.Sound object ready to play
    """
    try:
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Calculate number of samples
        num_samples = int(duration * sample_rate)
        
        # Generate time array
        t = np.linspace(0, duration, num_samples, False)
        
        # Generate sine wave
        wave = np.sin(frequency * 2 * np.pi * t)
        
        # Apply simple fade-in and fade-out (to avoid clicks)
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # Convert to 16-bit PCM
        wave_int16 = np.int16(wave * 32767)
        
        # Create stereo sound (duplicate for both channels)
        stereo_wave = np.zeros((num_samples, 2), dtype=np.int16)
        stereo_wave[:, 0] = wave_int16
        stereo_wave[:, 1] = wave_int16
        
        # Create pygame Sound object
        sound = pygame.sndarray.make_sound(stereo_wave.T)
        return sound
        
    except Exception as e:
        print(f"[⚠️ BEEP] Error generating beep sound: {e}")
        return None


def play_activation_beep() -> bool:
    """
    Plays the activation beep sound to confirm wake word detection.
    
    Returns:
        True if beep was played successfully, False otherwise
    """
    try:
        # Initialize pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        print(f"[🔊 BEEP] Playing activation beep...")
        
        # Generate the beep sound
        beep_sound = generate_beep_sound()
        
        if beep_sound is None:
            print(f"[⚠️ BEEP] Failed to generate beep sound")
            return False
        
        # Play the sound
        beep_sound.play()
        
        # Wait for sound to finish
        import time
        time.sleep(BEEP_DURATION + 0.1)  # Add small buffer
        
        print(f"[✅ BEEP] Activation beep played successfully")
        return True
        
    except Exception as e:
        print(f"[❌ BEEP] Error playing activation beep: {e}")
        return False


def play_completion_beep() -> bool:
    """
    Plays a completion/notification beep (different from activation beep).
    Uses a slightly higher pitch for distinction.
    
    Returns:
        True if beep was played successfully, False otherwise
    """
    try:
        # Initialize pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        print(f"[🔊 BEEP] Playing completion beep...")
        
        # Generate a higher-pitched completion beep
        beep_sound = generate_beep_sound(frequency=1100, duration=0.1)
        
        if beep_sound is None:
            print(f"[⚠️ BEEP] Failed to generate completion beep sound")
            return False
        
        # Play the sound twice for distinctiveness
        beep_sound.play()
        import time
        time.sleep(0.15)
        beep_sound.play()
        time.sleep(0.15)
        
        print(f"[✅ BEEP] Completion beep played successfully")
        return True
        
    except Exception as e:
        print(f"[❌ BEEP] Error playing completion beep: {e}")
        return False


if __name__ == "__main__":
    # Test beep sounds
    print("[🧪 BEEP] Testing activation beep...")
    play_activation_beep()
    
    print("\n[🧪 BEEP] Testing completion beep...")
    play_completion_beep()
    
    print("\n[✅ BEEP] Beep tests completed")
