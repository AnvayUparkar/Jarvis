"""
Wav2Lip Integration Service for MIRAGE Virtual Assistant.

HIGH-PERFORMANCE VERSION with:
1. Persistent model loading (zero cold-start after boot)
2. GPU warm-up at startup
3. Pre-processed avatar face tensor
4. Audio silence trimming
5. Async rendering support
6. Smart caching

Author: MIRAGE Team - Performance Optimized
"""

import os
import platform
import subprocess
import hashlib
import shutil
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable

# === Path Configuration ===
PROJECT_ROOT = Path(__file__).parent.resolve()
WAV2LIP_DIR = PROJECT_ROOT / "Wav2Lip"
AVATAR_IMAGE = PROJECT_ROOT / "www" / "assets" / "img" / "avatar.jpg"
CHECKPOINT = WAV2LIP_DIR / "checkpoints" / "wav2lip.pth"  # Standard model for speed
CACHE_DIR = PROJECT_ROOT / "lipsync_cache"
OUTPUT_DIR = PROJECT_ROOT / "www" / "lipsync_output"
FFMPEG_PATH = PROJECT_ROOT / "ffmpeg.exe"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Pre-calculated face bounding box for 512x512 resized avatar
# [y1, y2, x1, x2] - calculated once, reused forever
FACE_BOX = [114, 351, 147, 358]

# === GLOBAL ENGINE (Singleton) ===
_engine = None
_engine_lock = threading.Lock()
_engine_ready = threading.Event()

# === ASYNC RENDERING ===
_render_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Wav2Lip-Render")


def _get_engine():
    """Get or initialize the persistent Wav2Lip engine."""
    global _engine
    
    if _engine is not None:
        return _engine
    
    with _engine_lock:
        if _engine is not None:
            return _engine
        
        # Lazy import to avoid loading torch at module import time
        import sys
        sys.path.insert(0, str(WAV2LIP_DIR))
        
        from wav2lip_engine import warmup_engine # type: ignore
        
        print("[WAV2LIP] 🚀 Initializing persistent inference engine...")
        _engine = warmup_engine(
            str(CHECKPOINT),
            str(AVATAR_IMAGE),
            FACE_BOX
        )
        _engine_ready.set()
        print("[WAV2LIP] ✅ Engine ready for real-time inference!")
        
        return _engine


def initialize_at_startup():
    """
    Call this during backend boot to pre-load the model.
    Eliminates cold-start latency for the first user request.
    """
    def _init_thread():
        try:
            _get_engine()
        except Exception as e:
            print(f"[WAV2LIP] ❌ Startup initialization failed: {e}")
    
    # Non-blocking initialization
    threading.Thread(target=_init_thread, daemon=True, name="Wav2Lip-Init").start()
    print("[WAV2LIP] 🔄 Background engine initialization started...")


def check_wav2lip_setup() -> bool:
    """Verify Wav2Lip is properly set up."""
    if not WAV2LIP_DIR.exists():
        print(f"[WAV2LIP] ❌ Wav2Lip directory not found at: {WAV2LIP_DIR}")
        return False
    
    if not CHECKPOINT.exists():
        print(f"[WAV2LIP] ❌ Checkpoint not found at: {CHECKPOINT}")
        return False
    
    if not AVATAR_IMAGE.exists():
        print(f"[WAV2LIP] ❌ Avatar image not found at: {AVATAR_IMAGE}")
        return False
    
    print("[WAV2LIP] ✅ Setup verified successfully")
    return True


def convert_mp3_to_wav(mp3_path: str, wav_path: str = None) -> Optional[str]:
    """Convert MP3 to WAV (mono, 16kHz) using FFmpeg."""
    if wav_path is None:
        wav_path = mp3_path.replace(".mp3", ".wav")
    
    try:
        ffmpeg_cmd = str(FFMPEG_PATH) if FFMPEG_PATH.exists() else "ffmpeg"
        
        # On Windows, if we are using the system ffmpeg, use shell=True for best compatibility
        use_shell = platform.system() == 'Windows' and ffmpeg_cmd == "ffmpeg"
        
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", mp3_path,
            "-ar", "16000",
            "-ac", "1",
            "-acodec", "pcm_s16le",
            wav_path
        ]
        
        if use_shell:
            result = subprocess.run(' '.join(cmd), capture_output=True, timeout=30, shell=True)
        else:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(wav_path):
            return wav_path
        return None
        
    except Exception as e:
        print(f"[WAV2LIP] ❌ Conversion error: {e}")
        return None


def get_cache_key(text: str) -> str:
    """Generate deterministic hash for caching."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_cached_video(text: str) -> Optional[str]:
    """Check for cached video. Returns web-accessible path if found."""
    cache_key = get_cache_key(text)
    cached_path = CACHE_DIR / f"{cache_key}.mp4"
    
    if cached_path.exists():
        print(f"[WAV2LIP] 📦 Cache hit: {cache_key[:8]}...")
        output_filename = f"lipsync_{cache_key[:8]}.mp4"
        output_path = OUTPUT_DIR / output_filename
        try:
            shutil.copy(cached_path, output_path)
            return f"lipsync_output/{output_filename}"
        except Exception as e:
            print(f"[WAV2LIP] ⚠️ Cache copy failed: {e}")
    return None


def cache_video(text: str, video_path: str) -> bool:
    """Cache generated video for future reuse."""
    try:
        cache_key = get_cache_key(text)
        cached_path = CACHE_DIR / f"{cache_key}.mp4"
        shutil.copy(video_path, cached_path)
        print(f"[WAV2LIP] 💾 Cached: {cache_key[:8]}...")
        return True
    except Exception as e:
        print(f"[WAV2LIP] ❌ Cache error: {e}")
        return False


def generate_lipsync_video(audio_path: str, text: str = None) -> Optional[str]:
    """
    Generate lip-synced video from audio.
    
    This is the main entry point - optimized for speed.
    
    Args:
        audio_path: Path to TTS audio file (MP3 or WAV)
        text: Optional text for caching
        
    Returns:
        Web-accessible path to video, or None on failure
    """
    start_time = time.time()
    cleanup_wav = False
    wav_path = None
    
    try:
        # === CACHE CHECK (Fast path) ===
        if text:
            cached = get_cached_video(text)
            if cached:
                return cached
        
        # === VALIDATE INPUT ===
        if not audio_path or not Path(audio_path).exists():
            print(f"[WAV2LIP] ❌ Audio not found: {audio_path}")
            return None
        
        # === GET ENGINE (Persistent, no cold-start) ===
        engine = _get_engine()
        
        # === GENERATE OUTPUT PATH ===
        cache_key = get_cache_key(text) if text else f"temp_{int(time.time())}"
        output_filename = f"lipsync_{cache_key[:8]}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # === RUN INFERENCE ===
        print(f"[WAV2LIP] 🎬 Generating video...")
        
        audio_path_abs = os.path.abspath(audio_path)
        output_path_abs = str(output_path)
        
        success = engine.infer(audio_path_abs, output_path_abs)
        
        if not success or not output_path.exists():
            print(f"[WAV2LIP] ❌ Inference failed")
            return None
        
        elapsed = time.time() - start_time
        print(f"[WAV2LIP] ✅ Video generated in {elapsed:.1f}s")
        
        # === CACHE RESULT ===
        if text:
            cache_video(text, output_path_abs)
        
        return f"lipsync_output/{output_filename}"
        
    except Exception as e:
        print(f"[WAV2LIP] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup temp WAV
        if cleanup_wav and wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass


def generate_lipsync_video_async(audio_path: str, text: str = None,
                                  callback: Callable[[Optional[str]], None] = None):
    """
    Async version - returns immediately, calls callback when done.
    
    Args:
        audio_path: Path to audio file
        text: Optional text for caching
        callback: Function to call with result path (or None on failure)
    """
    def _task():
        result = generate_lipsync_video(audio_path, text)
        if callback:
            callback(result)
        return result
    
    future = _render_executor.submit(_task)
    return future


def clear_cache() -> int:
    """Clear all cached videos. Returns count of deleted files."""
    count = 0
    for f in CACHE_DIR.glob("*.mp4"):
        try:
            f.unlink()
            count += 1
        except:
            pass
    print(f"[WAV2LIP] 🧹 Cleared {count} cached videos")
    return count


def get_engine_status() -> dict:
    """Get engine status for monitoring."""
    return {
        "initialized": _engine is not None,
        "ready": _engine_ready.is_set(),
        "device": _engine.device if _engine else None,
        "cache_size": len(list(CACHE_DIR.glob("*.mp4"))),
    }


# === AUTO-INITIALIZE ON IMPORT (Optional) ===
# Uncomment to auto-start engine when module is imported
# initialize_at_startup()


# === Quick Test ===
if __name__ == "__main__":
    print("=== Wav2Lip Performance Service Test ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Checkpoint: {CHECKPOINT}")
    print(f"Avatar: {AVATAR_IMAGE}")
    print()
    
    if check_wav2lip_setup():
        print("\n✅ Setup verified!")
        print("\nInitializing engine...")
        initialize_at_startup()
        
        # Wait for initialization
        _engine_ready.wait(timeout=60)
        
        print("\nEngine Status:", get_engine_status())
        print("\n🚀 Ready for real-time inference!")
    else:
        print("\n❌ Setup incomplete")
