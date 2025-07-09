import os
import sys
import signal
import threading
import time

# Global flag for Ctrl+C detection
CTRL_C_PRESSED = False

# Signal handler for Ctrl+C
def signal_handler(sig, frame):
    global CTRL_C_PRESSED
    CTRL_C_PRESSED = True
    print("\n[INFO] Ctrl+C detected! Initiating emergency exit...")
    
    # Create a last resort kill thread
    def delayed_kill():
        for i in range(3, 0, -1):
            print(f"[INFO] Terminating in {i} seconds...")
            time.sleep(1)
        print("[INFO] Force terminating now!")
        os._exit(1)
    
    # Start the last resort kill thread
    last_resort = threading.Thread(target=delayed_kill)
    last_resort.daemon = True
    last_resort.start()
    
    # Try direct exit
    os._exit(0)

# Watchdog thread that monitors for Ctrl+C and forces termination
def watchdog_thread():
    while True:
        time.sleep(0.5)
        if CTRL_C_PRESSED:
            print("[INFO] Watchdog detected Ctrl+C flag! Forcing exit...")
            os._exit(1)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Start watchdog thread
watchdog = threading.Thread(target=watchdog_thread)
watchdog.daemon = True
watchdog.start()

print("Test script started. Press Ctrl+C to test emergency exit...")
print("This script will run for 60 seconds unless terminated.")

# Simulate a long-running process
try:
    for i in range(60):
        print(f"Running... {i}/60 seconds elapsed", end="\r")
        time.sleep(1)
    print("\nScript completed normally.")
except KeyboardInterrupt:
    print("\n[INFO] KeyboardInterrupt caught in main thread!")
    print("[INFO] Emergency termination in progress...")
    # Try the most direct approach to kill all Python processes
    try:
        import subprocess
        subprocess.Popen("taskkill /F /IM python.exe", shell=True)
    except:
        pass
    # Last resort
    os._exit(1) 