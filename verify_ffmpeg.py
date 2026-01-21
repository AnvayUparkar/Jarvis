
import os
import sys
import platform
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Wav2Lip"))

def test_ffmpeg_fallback():
    print("=== Testing FFmpeg Fallback Logic ===")
    
    local_ffmpeg = PROJECT_ROOT / "ffmpeg.exe"
    print(f"Checking for local ffmpeg.exe at: {local_ffmpeg}")
    print(f"Exists: {local_ffmpeg.exists()}")
    
    # Test logic similar to wav2lip_engine.py
    if platform.system() == 'Windows':
        ffmpeg_path = str(local_ffmpeg) if local_ffmpeg.exists() else 'ffmpeg'
    else:
        ffmpeg_path = 'ffmpeg'
    
    print(f"Selected FFmpeg path: {ffmpeg_path}")
    
    try:
        # Try running the selected ffmpeg
        if platform.system() == 'Windows' and ffmpeg_path == 'ffmpeg':
            # Use shell=True for system ffmpeg on Windows
            result = subprocess.run('ffmpeg -version', capture_output=True, text=True, shell=True)
        else:
            result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True)
            
        if result.returncode == 0:
            print("✅ FFmpeg check successful!")
            print(f"Output snippet: {result.stdout[:50]}...")
        else:
            print(f"❌ FFmpeg check failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ FFmpeg check failed with exception: {e}")

if __name__ == "__main__":
    test_ffmpeg_fallback()
