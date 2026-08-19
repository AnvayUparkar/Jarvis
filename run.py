# run.py - Jarvis Multiprocessing Entry Point
"""
Launches Jarvis in dual-process mode:
- Process 1: Main Jarvis application with GUI and command handling
- Process 2: Background hotword detection listener (Porcupine wake word "Jarvis")

Communication: IPC Queue for hotword activation signals
"""

import multiprocessing
import subprocess
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import time

# NOTE: Do NOT import `main` here. It contains heavy dependencies (Wav2Lip, etc.)
# that would slow down or block the hotword detection process.
# Imports are deferred to inside the process functions where they're needed.


def startJarvis(command_queue, conversation_mode_active):
    """Process 1: Main Jarvis application with GUI and command processing"""
    print("\n" + "="*60)
    print("[🤖 JARVIS] Process 1 (Main Application) is starting...")
    print("="*60)
    try:
        from main import start
        start(command_queue, conversation_mode_active)  # Pass the queue and the synchronization event
    except Exception as e:
        print(f"[❌ JARVIS] Fatal error in main Jarvis process: {e}")
        sys.exit(1)


def listenHotword(command_queue, conversation_mode_active):
    """Process 2: Background hotword detection listener"""
    print("\n" + "="*60)
    print("[🎙️ HOTWORD] Process 2 (Hotword Listener) is starting...")
    print("="*60)
    try:
        # Import hotword detection function
        from engine.features import hotword
        print("[✅ HOTWORD] Successfully imported hotword detection module")
        print("[🔊 HOTWORD] Initializing Porcupine for 'Jarvis' wake word detection...")
        
        # Start continuous hotword listening
        hotword(command_queue, conversation_mode_active)
        
    except ImportError as e:
        print(f"[❌ HOTWORD] Import error: Could not import hotword module")
        print(f"[📋 HOTWORD] Details: {e}")
        print(f"[📁 HOTWORD] Make sure 'engine/features.py' exists and is accessible")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[❌ HOTWORD] File not found: {e}")
        print(f"[📁 HOTWORD] Check that the Porcupine model file exists")
        sys.exit(1)
    except Exception as e:
        print(f"[❌ HOTWORD] Fatal error in hotword process: {e}")
        print(f"[📋 HOTWORD] Error type: {type(e).__name__}")
        sys.exit(1)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("[🚀] JARVIS INITIALIZATION")
    print("="*60)
    print("[📋] Multi-process launcher")
    print("[📍] Process 1: Main GUI Application")
    print("[🎙️] Process 2: Background Hotword Detection")
    print("="*60 + "\n")
    
    try:
        # Create inter-process queue for hotword activation signals
        command_queue = multiprocessing.Queue()
        print("[✅] IPC Queue created for hotword→main communication")
        
        # Create inter-process event for Conversation Mode sync
        conversation_mode_active = multiprocessing.Event()
        print("[✅] IPC Event created for Conversation Mode synchronization")
        
        # Create the processes
        print("[⚙️] Creating processes...")
        p1 = multiprocessing.Process(target=startJarvis, args=(command_queue, conversation_mode_active), name="Jarvis-Main")
        p2 = multiprocessing.Process(target=listenHotword, args=(command_queue, conversation_mode_active), name="Jarvis-Hotword")
        print(f"[✅] Process 1: {p1.name} (PID pending)")
        print(f"[✅] Process 2: {p2.name} (PID pending)")
        
        # Start the processes
        print("\n[🚀] Starting processes...")
        p1.start()
        print(f"[✅] {p1.name} started (PID: {p1.pid})")
        
        time.sleep(1)  # Brief delay to let main process initialize
        
        p2.start()
        print(f"[✅] {p2.name} started (PID: {p2.pid})")
        
        print("\n" + "="*60)
        print("[✨] JARVIS IS RUNNING")
        print("="*60)
        print("[🎤] Say 'Jarvis' to activate")
        print("[⏹️] Press Ctrl+C to stop\n")
        
        # Wait for the Jarvis main process to finish
        p1.join()
        
        # If Jarvis stops, terminate the hotword listener if it's still running
        if p2.is_alive():
            print("\n[⏹️] Main process stopped. Terminating hotword listener...")
            p2.terminate()
            p2.join(timeout=5)  # Wait max 5 seconds for clean termination
            
            if p2.is_alive():
                print("[⚠️] Hotword process did not terminate gracefully, killing...")
                p2.kill()
                p2.join()

        print("\n[🛑] System stopped gracefully")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n[⏸️] Interrupted by user (Ctrl+C)")
        print("[🧹] Cleaning up processes...")
        
        try:
            if 'p1' in locals() and p1.is_alive():
                p1.terminate()
                p1.join(timeout=3)
                if p1.is_alive():
                    p1.kill()
                    p1.join()
                print(f"[✅] {p1.name} terminated")
            
            if 'p2' in locals() and p2.is_alive():
                p2.terminate()
                p2.join(timeout=3)
                if p2.is_alive():
                    p2.kill()
                    p2.join()
                print(f"[✅] {p2.name} terminated")
                
            print("[✅] Cleanup complete")
            
        except Exception as e:
            print(f"[⚠️] Error during cleanup: {e}")
        
        print("\n[🛑] System stopped\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[❌] Fatal error in launcher: {e}")
        print(f"[📋] Error type: {type(e).__name__}")
        
        # Attempt cleanup
        try:
            if 'p1' in locals() and p1.is_alive():
                p1.terminate()
            if 'p2' in locals() and p2.is_alive():
                p2.terminate()
        except:
            pass
        
        sys.exit(1)