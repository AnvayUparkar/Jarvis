
import threading
import time
import logging

class Watchdog:
    """
    Monitors critical threads and logs warnings if they become unresponsive.
    """
    def __init__(self, timeout=30):
        self.timeout = timeout
        self._heartbeats = {}
        self._lock = threading.Lock()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._stop_event = threading.Event()
        self._monitor_thread.start()

    def touch(self, thread_name):
        """Update the heartbeat for a specific thread."""
        with self._lock:
            self._heartbeats[thread_name] = time.time()

    def _monitor_loop(self):
        print("[🛡️ WATCHDOG] Monitoring started...")
        while not self._stop_event.is_set():
            time.sleep(5)
            with self._lock:
                current_time = time.time()
                for name, last_beat in self._heartbeats.items():
                    if current_time - last_beat > self.timeout:
                        print(f"[⚠️ WATCHDOG] ALERT: Thread '{name}' unresponsive for {current_time - last_beat:.1f}s!")
                        logging.warning(f"Thread '{name}' unresponsive for {current_time - last_beat:.1f}s")
                        
    def stop(self):
        self._stop_event.set()
