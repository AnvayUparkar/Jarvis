# 📋 Hotword Implementation - Pre-Launch Checklist

## ✅ Pre-Launch Setup Checklist

### Installation Phase
- [ ] Downloaded/Updated repository
- [ ] Navigated to Jarvis directory
- [ ] Python 3.7+ installed (`python --version`)
- [ ] pip installed (`pip --version`)

### Package Installation
- [ ] Installed pvporcupine: `pip install pvporcupine`
- [ ] Installed pyaudio: `pip install pyaudio`
- [ ] Installed numpy: `pip install numpy`
- [ ] Installed pygame: `pip install pygame`

### File Verification
- [ ] File exists: `engine/features.py` (280+ lines)
- [ ] File exists: `activation_beep.py` (140+ lines)
- [ ] File exists: `Jarvis_en_windows_v3_0_0.ppn` (Porcupine model)
- [ ] File modified: `run.py` (enhanced, 190+ lines)
- [ ] File modified: `main.py` (beep import added)

### Hardware Check
- [ ] Microphone connected and working
- [ ] Speakers/Headphones working
- [ ] Microphone volume not muted (check Windows Settings)
- [ ] No software blocking microphone access

### Quick Verification
```bash
# Test imports
python -c "from engine.features import hotword; print('✅')"
python -c "from activation_beep import play_activation_beep; print('✅')"

# Test microphone
python -c "import pyaudio; pa = pyaudio.PyAudio(); print(f'✅ {pa.get_device_count()} devices')"

# Test beep (should play a sound)
python -c "from activation_beep import play_activation_beep; play_activation_beep()"
```

---

## 🚀 Launch Phase

### Before Starting Jarvis
- [ ] All installation checks passed
- [ ] All files verified
- [ ] Hardware connected
- [ ] No other audio-blocking applications running
- [ ] Documentation files saved locally

### Start Jarvis
```bash
python run.py
```

### Expected Console Output
```
============================================================
[🚀] JARVIS INITIALIZATION
============================================================
[📋] Multi-process launcher
[📍] Process 1: Main GUI Application
[🎙️] Process 2: Background Hotword Detection
============================================================

[✅] IPC Queue created for hotword→main communication
[⚙️] Creating processes...
[✅] Process 1: Jarvis-Main (PID pending)
[✅] Process 2: Jarvis-Hotword (PID pending)

[🚀] Starting processes...
[✅] Jarvis-Main started (PID: XXXX)
[✅] Jarvis-Hotword started (PID: XXXX)

============================================================
[✨] JARVIS IS RUNNING
============================================================
[🎤] Say 'Jarvis' to activate
[⏹️] Press Ctrl+C to stop
```

---

## 🎙️ First Use Checklist

### Test 1: Wake Word Detection
- [ ] Say "Jarvis" clearly
- [ ] Wait for beep sound (should play 880Hz tone)
- [ ] Observe "Jarvis activated by hotword!" in console
- [ ] See "Yes, how can I help you?" in UI

### Test 2: Command Processing
- [ ] After activation, say a command
- [ ] Example: "open google" or "what's the weather?"
- [ ] Observe command is recognized and processed
- [ ] Get appropriate response

### Test 3: Auto-Return to Listening
- [ ] After command completes, system automatically returns to listening
- [ ] Say "Jarvis" again
- [ ] Should detect wake word again (new beep)

### Test 4: Cooldown Verification
- [ ] Say "Jarvis" once (beep plays)
- [ ] Immediately say "Jarvis" again (should be ignored during 2s cooldown)
- [ ] Wait 2 seconds
- [ ] Say "Jarvis" again (should detect and beep)

### Test 5: Graceful Shutdown
- [ ] Press Ctrl+C during passive listening
- [ ] Both processes should terminate cleanly
- [ ] All resources should be released
- [ ] No error messages

---

## 🔍 Troubleshooting Checklist

### If Beep Doesn't Play
- [ ] Check volume/mute in Windows Settings
- [ ] Test pygame: `python -c "import pygame; pygame.mixer.init()"`
- [ ] Run direct beep test: `python activation_beep.py`
- [ ] Check speakers/headphones are connected

### If Wake Word Not Detected
- [ ] Check microphone works in other apps
- [ ] Increase microphone volume in Windows Settings
- [ ] Reduce background noise
- [ ] Speak clearly and naturally
- [ ] Try adjusting microphone distance

### If Processes Won't Start
- [ ] Check Python version: `python --version` (need 3.7+)
- [ ] Check all packages installed: `pip list | grep -E "pvporcupine|pyaudio|numpy|pygame"`
- [ ] Check Porcupine model path in `engine/features.py`
- [ ] Check permissions (no read-only folders)

### If Jarvis Freezes
- [ ] Press Ctrl+C to force shutdown
- [ ] Check console output for error messages
- [ ] Verify microphone isn't occupied by other process
- [ ] Try restarting system

---

## 📊 Performance Checklist

### During Passive Listening
- [ ] CPU usage: 2-5% (check Task Manager)
- [ ] Memory stable: ~50-80 MB hotword process
- [ ] No excessive disk I/O
- [ ] No CPU spikes (should be smooth)

### During Detection
- [ ] CPU spike to 8-12% briefly
- [ ] Beep plays within 100ms
- [ ] Response time acceptable

### Overall
- [ ] GUI remains responsive
- [ ] No lag or delays
- [ ] Smooth operation
- [ ] No crashes or errors

---

## 🔧 Configuration Checklist

### If You Want to Adjust Behavior

#### Change Beep Frequency
- [ ] Edit `activation_beep.py`
- [ ] Modify: `BEEP_FREQUENCY = 880` (to desired Hz)
- [ ] Save and restart Jarvis

#### Change Cooldown Duration
- [ ] Edit `engine/features.py`
- [ ] Modify: `COOLDOWN_SECONDS = 2.0` (to desired seconds)
- [ ] Save and restart Jarvis

#### Change Beep Duration
- [ ] Edit `activation_beep.py`
- [ ] Modify: `BEEP_DURATION = 0.15` (to desired seconds)
- [ ] Save and restart Jarvis

#### Use Different Wake Word
- [ ] Visit https://console.picovoice.ai/
- [ ] Train custom model with desired wake word
- [ ] Download .ppn file
- [ ] Update path in `engine/features.py`
- [ ] Restart Jarvis

---

## 📚 Documentation Checklist

### Recommended Reading Order
- [ ] `README_HOTWORD.md` (this file overview)
- [ ] `HOTWORD_QUICKSTART.md` (5-minute setup)
- [ ] `REQUIREMENTS_HOTWORD.md` (installation details)
- [ ] `HOTWORD_IMPLEMENTATION.md` (full documentation)
- [ ] `ARCHITECTURE_DIAGRAMS.md` (technical diagrams)

### Support Resources Available
- [ ] Quick start guide ready
- [ ] Troubleshooting guide available
- [ ] Architecture documentation complete
- [ ] Code comments comprehensive
- [ ] Error messages informative

---

## 🎯 Success Criteria Checklist

### ✅ Functional Requirements
- [ ] Microphone active at all times
- [ ] Wake word "Jarvis" detected
- [ ] Beep feedback plays on detection
- [ ] Command listening works after activation
- [ ] Existing command pipeline unchanged
- [ ] Auto-return to passive listening
- [ ] Cooldown prevents false retriggers

### ✅ Technical Requirements
- [ ] Python implementation
- [ ] Uses Porcupine (Picovoice)
- [ ] Uses approved libraries only
- [ ] Multi-process architecture
- [ ] IPC communication working
- [ ] Minimal CPU/memory usage
- [ ] No breaking changes

### ✅ Quality Requirements
- [ ] Comprehensive logging
- [ ] Proper error handling
- [ ] Clean shutdown
- [ ] Extensive documentation
- [ ] Code comments clear
- [ ] User guides available
- [ ] Troubleshooting complete

---

## 🎉 Post-Launch Checklist

### First 24 Hours
- [ ] Run Jarvis for extended period (test stability)
- [ ] Try various commands to ensure compatibility
- [ ] Test in different environments (noise levels)
- [ ] Verify no memory leaks (monitor Task Manager)
- [ ] Check all features still work

### After Successful First Day
- [ ] Save this checklist for reference
- [ ] Bookmark documentation files
- [ ] Note any customizations made
- [ ] Create backup of modified files
- [ ] Consider enabling logging for debugging

### Regular Maintenance
- [ ] Monitor system performance monthly
- [ ] Update packages as needed: `pip install --upgrade pvporcupine pyaudio`
- [ ] Clean up any temporary files
- [ ] Review console logs periodically
- [ ] Keep documentation updated

---

## 📞 Quick Reference

### Common Commands
| Task | Command |
|------|---------|
| Start Jarvis | `python run.py` |
| Install packages | `pip install pvporcupine pyaudio numpy pygame` |
| Test imports | `python -c "from engine.features import hotword"` |
| Test beep | `python activation_beep.py` |
| Stop Jarvis | `Ctrl+C` |

### Key Files
| File | Purpose |
|------|---------|
| `run.py` | Main launcher |
| `engine/features.py` | Hotword detection |
| `activation_beep.py` | Beep sound |
| `main.py` | Main application (modified) |
| `Jarvis_en_windows_v3_0_0.ppn` | Wake word model |

### Diagnostic Commands
```bash
# Check Python
python --version

# Check packages
pip list | grep -E "pvporcupine|pyaudio|numpy|pygame"

# Test hotword import
python -c "from engine.features import hotword; print('OK')"

# Test beep import
python -c "from activation_beep import play_activation_beep; print('OK')"

# Check microphone
python -c "import pyaudio; print(pyaudio.PyAudio().get_device_count())"
```

---

## 🚦 Status Indicators

### ✅ Green Light (Ready to Use)
- All packages installed
- All files verified
- Hardware working
- Console shows "JARVIS IS RUNNING"
- Beep plays on wake word
- Commands process normally

### 🟡 Yellow Light (Minor Issue)
- Missing optional packages
- Microphone volume low
- Background noise present
- Slight performance overhead
- Check troubleshooting guide

### 🔴 Red Light (Critical Issue)
- Packages not installed
- Porcupine model missing
- Microphone not detected
- Processes won't start
- Follow troubleshooting guide

---

## 📝 Notes Section

Use this space to document:
- Your test results
- Custom configurations
- Performance observations
- Issues encountered
- Solutions found

```
[Date] [Issue] [Solution]
_________________________________________________________________________________
_________________________________________________________________________________
_________________________________________________________________________________
_________________________________________________________________________________
_________________________________________________________________________________
```

---

## 🎊 Completion

When you've checked all items in each section, you're ready to enjoy hands-free Jarvis hotword activation!

**Status:** ✅ Ready for Production Use

**Next Step:** Start Jarvis with `python run.py` and say "Jarvis" to activate!

---

**Checklist Version:** 1.0  
**Last Updated:** January 2026  
**Created for:** Jarvis Hotword Activation v1.0
