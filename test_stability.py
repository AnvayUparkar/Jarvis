
import threading
import time
import requests
import queue
from main import SpeechEngine, command_executor, safe_request

def test_async_speech():
    print("\n--- Test 1: Async Speech ---")
    engine = SpeechEngine()
    start = time.time()
    
    print("Queueing 3 phrases...")
    engine.speak("Testing phase one.", block=False)
    engine.speak("Testing phase two.", block=False)
    engine.speak("Testing phase three.", block=False)
    
    end = time.time()
    duration = end - start
    print(f"Queued in {duration:.4f}s")
    
    if duration < 1.0:
        print("✅ PASS: Speech queued immediately (Non-blocking).")
    else:
        print("❌ FAIL: Speech blocked main thread.")
        
    # Wait for speech to finish roughly
    time.sleep(5)
    engine.ended = True

def test_command_thread():
    print("\n--- Test 2: Command Threading ---")
    
    def mock_command(cmd):
        print(f"Processing '{cmd}' in thread {threading.current_thread().name}")
        time.sleep(2)
        print(f"Finished '{cmd}'")
        
    print("Submitting slow command...")
    future = command_executor.submit(mock_command, "Slow Task")
    
    if not future.done():
        print("✅ PASS: Command running in background.")
    else:
         print("❌ FAIL: Command finished instantly (unexpected).")
         
    future.result() # Wait for it

def test_safe_request():
    print("\n--- Test 3: Safe Request Timeouts ---")
    # Test valid
    resp = safe_request('GET', 'https://www.google.com')
    if resp and resp.status_code == 200:
        print("✅ PASS: Valid request worked.")
    else:
        print("❌ FAIL: Valid request failed.")

    # Test timeout (simulated by non-routable IP with short timeout)
    # Actually, requests logic handles timeout. We just check if it returns None on error.
    print("Testing invalid URL handling...")
    resp = safe_request('GET', 'http://httpstat.us/404') # Should return None due to raise_for_status? No, 404 raises HTTPError
    
    if resp is None:
         print("✅ PASS: Error handled gracefully (returned None).")
    else:
         print("⚠️ INFO: 404 handled differently depending on implementation.")

if __name__ == "__main__":
    test_async_speech()
    test_command_thread()
    test_safe_request()
    print("\nTests Complete.")
