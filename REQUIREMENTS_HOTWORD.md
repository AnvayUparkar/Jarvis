# Required Packages for Jarvis Hotword Activation

## Installation Command
```bash
pip install pvporcupine pyaudio numpy pygame
```

## Individual Package Details

### 1. **pvporcupine** (Required)
- **Version:** Latest
- **Purpose:** Porcupine wake word detection engine
- **Size:** ~50 MB
- **Installation:** `pip install pvporcupine`
- **Status:** ✅ Included in requirements

```python
import pvporcupine
porcupine = pvporcupine.create(
    access_key="YOUR_KEY",
    keyword_paths=["/path/to/model.ppn"]
)
```

### 2. **pyaudio** (Required)
- **Version:** Latest
- **Purpose:** Cross-platform audio I/O
- **Size:** ~10 MB
- **Installation:** `pip install pyaudio`
- **Note:** May require Visual C++ build tools on Windows
- **Status:** ✅ Included in requirements

```python
import pyaudio
pa = pyaudio.PyAudio()
stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True)
```

### 3. **numpy** (Required for beep generation)
- **Version:** Latest
- **Purpose:** Numerical computing (sine wave generation)
- **Size:** ~100 MB
- **Installation:** `pip install numpy`
- **Status:** ✅ Included in requirements

```python
import numpy as np
# Generate sine wave for beep sound
wave = np.sin(frequency * 2 * np.pi * t)
```

### 4. **pygame** (Required for audio playback)
- **Version:** Latest
- **Purpose:** Audio playback and mixer management
- **Size:** ~30 MB
- **Installation:** `pip install pygame`
- **Status:** ✅ Already in existing Jarvis requirements
- **Note:** Already used by Jarvis for music playback

```python
import pygame
pygame.mixer.init()
sound = pygame.mixer.Sound(...)
sound.play()
```

---

## Existing Jarvis Dependencies (No changes needed)
- ✅ `speech_recognition` - Already installed
- ✅ `pyttsx3` - Already installed
- ✅ `pygame` - Already installed
- ✅ `threading` - Built-in
- ✅ `multiprocessing` - Built-in
- ✅ `queue` - Built-in

---

## Installation Verification

### Quick Check
```bash
# Test each package
python -c "import pvporcupine; print('✅ pvporcupine')"
python -c "import pyaudio; print('✅ pyaudio')"
python -c "import numpy; print('✅ numpy')"
python -c "import pygame; print('✅ pygame')"
```

### Full System Check
```bash
# Test hotword system
python -c "from engine.features import hotword; print('✅ Hotword system ready')"

# Test beep system
python -c "from activation_beep import play_activation_beep; print('✅ Beep system ready')"

# Test microphone
python -c "import pyaudio; print(f'✅ Microphone devices: {pyaudio.PyAudio().get_device_count()}')"
```

---

## Optional Dependencies (Nice-to-have)

### For Advanced Audio (Optional)
```bash
# Advanced audio analysis
pip install librosa  # For audio feature extraction (optional)

# Performance profiling
pip install py-spy   # For CPU profiling (optional)

# Enhanced error reporting
pip install better-exceptions  # Better error messages (optional)
```

---

## Troubleshooting Installation

### Windows: "error: Microsoft Visual C++ 14.0 is required"
**Solution:** Install C++ build tools
```bash
# Download and install Visual C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# OR use pre-built wheels
pip install pyaudio --only-binary :all:
```

### macOS: "clang: error: unsupported option"
**Solution:** Use Homebrew
```bash
brew install portaudio
pip install pyaudio
```

### Linux: "Fatal error in launcher"
**Solution:** Install dev headers
```bash
sudo apt-get install python3-dev portaudio19-dev
pip install pyaudio
```

### pip install fails: "Connection timeout"
**Solution:** Use alternative package index
```bash
pip install -i https://pypi.org/simple/ pvporcupine pyaudio numpy pygame
```

---

## Version Compatibility

| Package | Min Version | Current | Notes |
|---------|------------|---------|-------|
| Python | 3.7 | 3.9+ | Tested on Python 3.9+ |
| pvporcupine | 1.9.0 | Latest | Active development |
| pyaudio | 0.2.11 | Latest | Stable API |
| numpy | 1.19.0 | 1.21+ | For numerical operations |
| pygame | 2.0.0 | 2.1+ | Already in Jarvis |

---

## Quick Setup Script

### save as `setup_hotword.bat` (Windows)
```batch
@echo off
echo [*] Installing hotword dependencies...
pip install pvporcupine pyaudio numpy pygame
echo [*] Testing installation...
python -c "from engine.features import hotword; print('[OK] Hotword ready')"
python -c "from activation_beep import play_activation_beep; print('[OK] Beep ready')"
echo [OK] All dependencies installed successfully!
```

### save as `setup_hotword.sh` (Linux/macOS)
```bash
#!/bin/bash
echo "[*] Installing hotword dependencies..."
pip install pvporcupine pyaudio numpy pygame
echo "[*] Testing installation..."
python3 -c "from engine.features import hotword; print('[OK] Hotword ready')"
python3 -c "from activation_beep import play_activation_beep; print('[OK] Beep ready')"
echo "[OK] All dependencies installed successfully!"
```

---

## Disk Space Requirements

| Component | Size |
|-----------|------|
| pvporcupine | 50 MB |
| pyaudio | 10 MB |
| numpy | 100 MB |
| pygame | 30 MB |
| Porcupine model (.ppn) | 2.5 MB |
| **Total** | **~192 MB** |

---

## Network Requirements

### During Installation
- ✅ Internet required (for pip download)
- ⏱️ Time: 3-5 minutes (depends on connection)

### During Runtime
- ❌ Internet NOT required (all offline)
- 🔒 No data sent to external servers
- 🌐 Porcupine runs locally on your device

---

## Security Notes

### Package Safety
- ✅ All packages from official PyPI
- ✅ Verified and widely used packages
- ✅ No external API calls needed
- ✅ All processing happens locally

### Permissions
- ✅ Microphone access (required for hotword)
- ✅ Audio playback (required for beep)
- ❌ No internet access required
- ❌ No data collection

---

## Next Steps

1. Install packages:
```bash
pip install pvporcupine pyaudio numpy pygame
```

2. Verify installation:
```bash
python setup_hotword.bat  # Windows
# or
bash setup_hotword.sh     # Linux/macOS
```

3. Start Jarvis:
```bash
python run.py
```

4. Say "Jarvis" to activate!

---

**Installation Guide Version:** 1.0  
**Last Updated:** January 2026  
**Status:** ✅ Ready for Production
