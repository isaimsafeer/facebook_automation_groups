import time
import csv
import os
import atexit
import signal
import sys
from datetime import datetime
import pandas as pd
import threading
import logging
from io import StringIO

# Add import with safeguard to prevent circular imports
try:
    from fb import auto as fb_auto
except ImportError:
    # Create a dummy module with a driver attribute if we can't import fb.auto
    class DummyModule:
        driver = None
    fb_auto = DummyModule()

# Session variables
start_time = None
csv_file = "execution_log.csv"
summary_csv_file = "Summary-table.csv"
lock_file = "execution_log.lock"
logged = False  # Flag to prevent multiple logs in one execution
username = None  # Store the current session's username

# Session metrics
profiles_fetched = 0
profiles_visited = 0
profiles_matched = 0
sent_messages = 0
deleted_users = 0
responses_received = 0
already_sent = 0
carry_forward_profiles = 0
carry_forward_messages = 0

# Flag to control background logging thread
keep_logging = True
logging_thread = None

# Terminal log capture
terminal_log_file = None
original_stdout = None
log_capture_enabled = False
session_log_path = None

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
    print(f"[INFO] Created logs directory at: {logs_dir}")

# Remove lock file at the start of script
if os.path.exists(lock_file):
    os.remove(lock_file)

# Setup logging to capture both console and file output
class TeeOutput:
    def __init__(self, file_stream, console_stream):
        self.file = file_stream
        self.console = console_stream

    def write(self, message):
        self.file.write(message)
        self.console.write(message)
        # Ensure file is flushed immediately to capture all output
        self.file.flush()

    def flush(self):
        self.file.flush()
        self.console.flush()

def start_session_logging():
    """Start capturing terminal output to a log file"""
    global terminal_log_file, original_stdout, log_capture_enabled, session_log_path, username

    # Create session-specific log filename with timestamp and username
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_part = f"_{username}" if username else ""
    log_filename = f"session_{timestamp}{user_part}.log"
    session_log_path = os.path.join(logs_dir, log_filename)

    try:
        # Open the log file
        terminal_log_file = open(session_log_path, 'w', encoding='utf-8')
        
        # Store the original stdout
        original_stdout = sys.stdout
        
        # Replace stdout with our custom output that writes to both console and file
        sys.stdout = TeeOutput(terminal_log_file, original_stdout)
        
        log_capture_enabled = True
        
        # Write session start header to the log
        session_start_msg = f"\n{'='*80}\nSESSION STARTED: {timestamp} - User: {username or 'N/A'}\n{'='*80}\n"
        print(session_start_msg)
        
        print(f"[INFO] Session logging started - output captured to: {session_log_path}")
    except Exception as e:
        # Revert to original stdout if there's an error
        if original_stdout:
            sys.stdout = original_stdout
        print(f"[ERROR] Failed to start session logging: {e}")

def stop_session_logging():
    """Stop capturing terminal output and close the log file"""
    global terminal_log_file, original_stdout, log_capture_enabled, session_log_path
    
    if log_capture_enabled and terminal_log_file and original_stdout:
        try:
            # Write session end footer
            session_end_msg = f"\n{'='*80}\nSESSION ENDED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n"
            print(session_end_msg)
            
            # Restore original stdout
            sys.stdout = original_stdout
            
            # Close the log file
            terminal_log_file.close()
            terminal_log_file = None
            
            log_capture_enabled = False
            
            print(f"[INFO] Session logging stopped - log saved to: {session_log_path}")
        except Exception as e:
            print(f"[ERROR] Failed to stop session logging properly: {e}")
    else:
        print("[INFO] No active session logging to stop")

# Initialize CSV files if they don't exist
def initialize_csv_files():
    encoding = 'utf-8-sig' if os.name == 'nt' else 'utf-8'
    
    # Initialize execution_log.csv
    if not os.path.exists(csv_file):
        try:
            with open(csv_file, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f)
                writer.writerow(["Start Time", "End Time", "Time ran", "Profiles Fetched"])
            print(f"[INFO] Created {csv_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create {csv_file}: {e}")
    
    # Initialize Summary-table.csv
    if not os.path.exists(summary_csv_file):
        try:
            with open(summary_csv_file, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Start time", "End time", "Username", "Profiles Fetched", "Profiles Visited",
                    "Profiles Matched", "Sent Messages", "Deleted Users", "Responses received",
                    "Already Sent", "Carry forward Profiles", "Carry forward Messages", "Time"
                ])
            print(f"[INFO] Created {summary_csv_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create {summary_csv_file}: {e}")

# Call initialization at module load time
initialize_csv_files()

# Function to migrate existing Summary-table.csv to include Username column
def migrate_summary_csv():
    """Add a Username column to existing Summary-table.csv if it doesn't have one"""
    if not os.path.exists(summary_csv_file):
        return  # Nothing to migrate if file doesn't exist
    
    try:
        # Read the existing CSV
        df = pd.read_csv(summary_csv_file)
        
        # Check if Username column already exists
        if "Username" not in df.columns:
            print("[INFO] Adding Username column to existing Summary-table.csv")
            
            # Create a new DataFrame with the desired column order
            new_columns = list(df.columns)
            # Insert Username after End time
            if "End time" in new_columns:
                username_position = new_columns.index("End time") + 1
                new_columns.insert(username_position, "Username")
                
                # Create new DataFrame with the updated columns
                new_df = pd.DataFrame(columns=new_columns)
                
                # Copy data from old DataFrame
                for col in df.columns:
                    new_df[col] = df[col]
                
                # Set default value for Username
                new_df["Username"] = "Unknown"
                
                # Save the updated file
                new_df.to_csv(summary_csv_file, index=False)
                print("[INFO] Successfully updated Summary-table.csv with Username column")
            else:
                print("[WARNING] Could not find 'End time' column in Summary-table.csv")
    except Exception as e:
        print(f"[ERROR] Failed to migrate Summary-table.csv: {e}")

# Run migration at module load time
migrate_summary_csv()

# Function to begin a new session
def begin_session(user=None):
    global start_time, logged, profiles_fetched, profiles_visited, profiles_matched
    global sent_messages, deleted_users, responses_received, already_sent, username
    
    # Set the username for this session
    username = user
    
    # Reset session metrics
    start_time = time.time()
    logged = False
    
    # Start capturing terminal output to a log file
    start_session_logging()
    
    # Start the background logging thread if not already running
    start_background_logging()
    
    print(f"[INFO] New tracking session started at {datetime.fromtimestamp(start_time).strftime('%m/%d/%Y %H:%M')}")
    if username:
        print(f"[INFO] Session username: {username}")

# Function to safely close the browser driver
def quit_driver():
    try:
        # First check the global driver from fb.auto module
        if hasattr(fb_auto, 'driver') and fb_auto.driver is not None:
            print("[INFO] Closing browser driver...")
            try:
                fb_auto.driver.quit()
                print("[INFO] Browser driver closed successfully")
            except Exception as e:
                print(f"[ERROR] Failed to close driver: {e}")
    except Exception as e:
        print(f"[ERROR] Error checking driver: {e}")

def update_profiles_count(count):
    """Update the count of profiles fetched for this session"""
    global profiles_fetched
    profiles_fetched += count

def update_session_metrics(metric_name, count=1):
    """Update any session metric by name"""
    global profiles_fetched, profiles_visited, profiles_matched, sent_messages
    global deleted_users, responses_received, already_sent
    global carry_forward_profiles, carry_forward_messages
    
    if metric_name == "profiles_fetched":
        profiles_fetched += count
        print(f"[DEBUG] Updated profiles_fetched to {profiles_fetched} (+{count})")
    elif metric_name == "profiles_visited":
        profiles_visited += count
        print(f"[DEBUG] Updated profiles_visited to {profiles_visited} (+{count})")
    elif metric_name == "profiles_matched":
        profiles_matched += count
        print(f"[DEBUG] Updated profiles_matched to {profiles_matched} (+{count})")
    elif metric_name == "sent_messages":
        sent_messages += count
        print(f"[DEBUG] Updated sent_messages to {sent_messages} (+{count})")
    elif metric_name == "deleted_users":
        deleted_users += count
        print(f"[DEBUG] Updated deleted_users to {deleted_users} (+{count})")
    elif metric_name == "responses_received":
        responses_received += count
        print(f"[DEBUG] Updated responses_received to {responses_received} (+{count})")
    elif metric_name == "already_sent":
        already_sent += count
        print(f"[DEBUG] Updated already_sent to {already_sent} (+{count})")
    elif metric_name == "carry_forward_profiles":
        carry_forward_profiles = count  # Set directly, not incremental
        print(f"[DEBUG] Set carry_forward_profiles to {carry_forward_profiles}")
    elif metric_name == "carry_forward_messages":
        carry_forward_messages = count  # Set directly, not incremental
        print(f"[DEBUG] Set carry_forward_messages to {carry_forward_messages}")
    else:
        print(f"[WARNING] Unknown metric name: {metric_name}")

def increment_carried_forward_messages(count=1):
    """Increment the carry forward messages count by the specified amount"""
    global carry_forward_messages
    carry_forward_messages += count
    print(f"[INFO] Incremented carry forward messages to {carry_forward_messages}")


# Function to validate metric values for consistency
def validate_metrics():
    """Ensure all metrics are consistent with each other"""
    global profiles_fetched, profiles_visited, profiles_matched
    global sent_messages, deleted_users, responses_received, already_sent
    global carry_forward_profiles, carry_forward_messages
    
    # Ensure all values are non-negative
    profiles_fetched = max(0, profiles_fetched)
    profiles_visited = max(0, profiles_visited) 
    profiles_matched = max(0, profiles_matched)
    sent_messages = max(0, sent_messages)
    deleted_users = max(0, deleted_users)
    responses_received = max(0, responses_received)
    already_sent = max(0, already_sent)
    carry_forward_profiles = max(0, carry_forward_profiles)
    carry_forward_messages = max(0, carry_forward_messages)
    
    # Ensure profiles_visited never exceeds profiles_fetched
    if profiles_visited > profiles_fetched and profiles_fetched > 0:
        profiles_visited = profiles_fetched
        print(f"[INFO] Adjusted profiles_visited to match profiles_fetched: {profiles_fetched}")
    
    # Ensure profiles_matched never exceeds profiles_visited
    if profiles_matched > profiles_visited and profiles_visited > 0:
        profiles_matched = profiles_visited
        print(f"[INFO] Adjusted profiles_matched to match profiles_visited: {profiles_visited}")

def format_elapsed_time(seconds):
    """
    Helper function to convert seconds to 00:MM format consistently.
    We're treating all times as minutes only (no hours) for clarity and consistency.
    """
    # Ensure seconds is a positive number
    seconds = max(0, seconds)
    
    # Convert seconds to minutes (rounded)
    total_minutes = round(seconds / 60)
    
    # Always format as 00:MM (always zeroed hours, only minutes matter)
    result = f"00:{int(total_minutes):02d}"
    
    # Print for debugging
    print(f"[DEBUG] Formatted {seconds:.1f} seconds as {total_minutes} minutes ({result})")
    
    # Return formatted string
    return result

def log_execution_time(is_final=False):
    global logged, start_time, username
    
    # If start_time is not set, we haven't begun a session yet
    if start_time is None:
        print("[WARNING] Cannot log execution time - no active session")
        return

    try:
        # Validate metrics if this is the final log
        if is_final:
            validate_metrics()
            
        # Skip if this is the final log but there's no activity
        if is_final and (profiles_fetched == 0 and profiles_visited == 0 and profiles_matched == 0 and
                          sent_messages == 0 and deleted_users == 0 and responses_received == 0 and
                          already_sent == 0):
            print("[INFO] Skipping final log for session with no activity")
            logged = True
            return
            
        # If final log and already logged, exit
        if is_final and logged:
            return

        # If final log, mark as logged
        if is_final:
            logged = True
            # Create a lock file (if it doesn't exist)
            try:
                with open(lock_file, "w") as f:
                    f.write("Logged")
            except Exception as e:
                print(f"[ERROR] Unable to create lock file: {e}")

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Skip if elapsed time is too short (less than 30 seconds) and no activity
        if elapsed_time < 30 and profiles_fetched == 0 and profiles_visited == 0 and not is_final:
            print("[INFO] Skipping log for inactive short session")
            return
        
        # Format elapsed time as HH:MM consistently
        elapsed_time_formatted = format_elapsed_time(elapsed_time)

        start_timestamp = datetime.fromtimestamp(start_time).strftime('%m/%d/%Y %H:%M')
        end_timestamp = datetime.fromtimestamp(end_time).strftime('%m/%d/%Y %H:%M')
        
        # Determine the username to log
        current_username = username if username is not None else "Unknown"
        
        # Set up encoding based on operating system
        encoding = 'utf-8-sig' if os.name == 'nt' else 'utf-8'
        
        # Set up a flag to check if the file exists
        summary_file_exists = os.path.exists(summary_csv_file)
        
        # Prepare row data for CSV
        summary_data = [
            start_timestamp,
            end_timestamp,
            current_username,
            profiles_fetched,
            profiles_visited,
            profiles_matched,
            sent_messages,
            deleted_users,
            responses_received,
            already_sent,
            carry_forward_profiles,
            carry_forward_messages,
            elapsed_time_formatted
        ]
        
        try:
            # Update existing row if present, or add new one
            if summary_file_exists:
                # Read existing data
                df = pd.read_csv(summary_csv_file, encoding=encoding)
                
                # Look for matching start time
                start_time_match_idx = df[df.iloc[:, 0] == start_timestamp].index
                
                if len(start_time_match_idx) > 0:
                    # Skip update if no activity
                    if (profiles_fetched == 0 and profiles_visited == 0 and profiles_matched == 0 and
                        sent_messages == 0 and deleted_users == 0 and responses_received == 0 and
                        already_sent == 0):
                        # Check if the existing row already has data
                        row_idx = start_time_match_idx[0]
                        if df.iloc[row_idx, 3:10].sum() > 0:  # Check if any activity metrics are > 0
                            print("[INFO] Skipping update to existing row with data")
                            return
                    
                    # Update the existing row (all columns except start time)
                    row_idx = start_time_match_idx[0]
                    # Only update columns after the first one (start time)
                    for col_idx in range(1, len(summary_data)):
                        if col_idx < len(df.columns):
                            df.iloc[row_idx, col_idx] = summary_data[col_idx]
                else:
                    # Add a new row only if there's activity or it's a real user session
                    if (profiles_fetched > 0 or profiles_visited > 0 or profiles_matched > 0 or 
                        sent_messages > 0 or deleted_users > 0 or responses_received > 0 or 
                        already_sent > 0):
                        df.loc[len(df)] = summary_data
                    else:
                        print("[INFO] Skipping adding new row with no activity metrics")
                        return
                
                # Save the updated data
                df.to_csv(summary_csv_file, index=False, encoding=encoding)
            else:
                # File doesn't exist, create it with headers
                with open(summary_csv_file, mode="w", newline="", encoding=encoding) as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        "Start time", "End time", "Username", "Profiles Fetched", "Profiles Visited",
                        "Profiles Matched", "Sent Messages", "Deleted Users", "Responses received",
                        "Already Sent", "Carry forward Profiles", "Carry forward Messages", "Time"
                    ])
                    writer.writerow(summary_data)
            
            if is_final:
                print(f"[INFO] Final update to {summary_csv_file} successful")
            else:
                print(f"[INFO] Periodic update to {summary_csv_file} successful")
        except Exception as e:
            print(f"[ERROR] Failed to update {summary_csv_file}: {e}")

        if is_final:
            print(f"Execution time logged: {elapsed_time_formatted}")
            print(f"Session metrics: Fetched: {profiles_fetched}, Visited: {profiles_visited}, Matched: {profiles_matched}")
            
            # When final log is recorded, stop session logging
            stop_session_logging()
    
    except Exception as e:
        print(f"[ERROR] Exception in log_execution_time: {e}")
        # Try one last time to write to files
        try:
            with open("error_log.txt", "a") as f:
                f.write(f"{datetime.now()}: Exception in logging: {e}\n")
        except:
            pass

def background_logging_thread():
    """Thread function that logs data at regular intervals"""
    global keep_logging
    
    log_interval = 10  # seconds between logs
    
    while keep_logging:
        # Validate metrics for consistency
        validate_metrics()
        
        # Validate metrics for consistency
        validate_metrics()
        
        # Log current session data (not final)
        log_execution_time(is_final=False)
        
        # Sleep for the interval
        for _ in range(log_interval):
            if not keep_logging:
                break
            time.sleep(1)

def start_background_logging():
    """Start the background logging thread if it's not already running"""
    global logging_thread, keep_logging
    
    # If thread is already running, don't start a new one
    if logging_thread is not None and logging_thread.is_alive():
        return
    
    # Reset the flag and start a new thread
    keep_logging = True
    logging_thread = threading.Thread(target=background_logging_thread, daemon=True)
    logging_thread.start()
    print("[INFO] Background logging thread started")

def stop_background_logging():
    """Stop the background logging thread"""
    global keep_logging, logging_thread
    keep_logging = False
    # Wait for thread to exit gracefully (with a timeout)
    if logging_thread is not None and logging_thread.is_alive():
        logging_thread.join(timeout=2)
    logging_thread = None
    print("[INFO] Background logging stopped")
    
    # Also stop the session logging if still active
    if log_capture_enabled:
        stop_session_logging()

# Register stop_background_logging to be called when the program exits
atexit.register(stop_background_logging)

# Handle exit signals properly
def handle_exit(signum, frame):
    """Handle exit signals (CTRL+C, etc.)"""
    global start_time, logged, terminal_log_file, original_stdout
    
    print(f"\n[INFO] Received signal {signum} - shutting down gracefully")
    
    # Log final execution time if not already done
    if start_time is not None and not logged:
        log_execution_time(is_final=True)
    
    # Stop background logging
    stop_background_logging()
    
    # Close browser driver
    quit_driver()
    
    # Stop session logging if it wasn't already stopped
    if log_capture_enabled:
        stop_session_logging()
    
    # Exit with appropriate error code
    sys.exit(0)

# Register the signal handlers
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# On Windows, register a Ctrl+C handler
if os.name == 'nt':
    try:
        import win32api
        
        def windows_handler(event):
            """Windows-specific event handler for Ctrl+C"""
            if event == 0:  # 0 is CTRL_C_EVENT
                # Simulate a Ctrl+C SIGINT
                handle_exit(signal.SIGINT, None)
                # Don't chain to other handlers
                return 1
            # Chain to the next handler
            return 0
        
        # Register Windows handler
        win32api.SetConsoleCtrlHandler(windows_handler, 1)
    except ImportError:
        # win32api not available, fall back to signal handlers
        print("[WARNING] win32api not available, using basic signal handlers")

# Function to ensure clean exit
def force_exit():
    """Force a clean exit from the program"""
    global start_time, logged, terminal_log_file, original_stdout
    
    print("\n[INFO] Forcing clean exit")
    
    # Log final execution time if not already done
    if start_time is not None and not logged:
        log_execution_time(is_final=True)
    
    # Stop background logging
    stop_background_logging()
    
    # Close browser driver
    quit_driver()
    
    # Stop session logging if it wasn't already stopped
    if log_capture_enabled:
        stop_session_logging()
    
    # Exit with appropriate error code
    sys.exit(0)
