#!/usr/bin/env python
# Script to update time_tracker.py with fixes for message tracking issues

import os
import re
import shutil
import time
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the specified file with timestamp in filename"""
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"[INFO] Created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {e}")
        return False

def update_time_tracker_main():
    """Update the main time_tracker.py file"""
    file_path = "time_tracker.py"
    
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    # Create backup
    if not backup_file(file_path):
        print("[ERROR] Failed to backup file. Aborting update.")
        return False
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Update 1: Fix carry_forward_messages to prevent negative values
        pattern = r'(elif metric_name == "carry_forward_messages":\s+)carry_forward_messages = count\s+print\(f"\[DEBUG\] Set carry_forward_messages to {carry_forward_messages}"\)'
        
        replacement = r'\1# Prevent negative values\n        carry_forward_messages = max(0, count)  # Never go below 0\n        print(f"[DEBUG] Set carry_forward_messages to {carry_forward_messages}")'
        
        updated_content = re.sub(pattern, replacement, content)
        
        # Update 2: Add validate_metrics function to ensure consistency
        validate_function = """
# Function to validate metric values for consistency
def validate_metrics():
    \"\"\"Ensure all metrics are consistent with each other\"\"\"
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
"""
        
        # Find a good place to add the function (before log_execution_time)
        pattern = r'def log_execution_time\(is_final=False\):'
        updated_content = re.sub(pattern, validate_function + "\n\ndef log_execution_time(is_final=False):", updated_content)
        
        # Update 3: Modify background_logging_thread to call validate_metrics
        pattern = r'(def background_logging_thread\(\):.+?while keep_logging:.+?)# Log current session data \(not final\)\s+log_execution_time\(is_final=False\)'
        replacement = r'\1# Validate metrics for consistency\n        validate_metrics()\n        \n        # Log current session data (not final)\n        log_execution_time(is_final=False)'
        
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        
        # Update 4: Add validation before final logging
        pattern = r'(def log_execution_time\(is_final=False\):.+?try:.+?)# If final log and already logged, exit'
        replacement = r'\1# Validate metrics if this is the final log\n        if is_final:\n            validate_metrics()\n            \n        # If final log and already logged, exit'
        
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"[INFO] Successfully updated {file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update {file_path}: {e}")
        return False

def update_fb_auto():
    """Update the fb/auto.py file to fix issues with notification handling and profile visits"""
    file_path = "fb/auto.py"
    
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    # Create backup
    if not backup_file(file_path):
        print("[ERROR] Failed to backup file. Aborting update.")
        return False
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Update 1: Fix validation in check_notifications function
        pattern = r'(# Update the response count for each valid chunk\s+)time_tracker\.update_session_metrics\("responses_received", 1\)'
        
        replacement = r'\1# Only count real messages, not system notifications\n                                                    if not chunk["message"].startswith("Messages and calls are") and not chunk["message"].startswith("You:"):\n                                                        time_tracker.update_session_metrics("responses_received", 1)\n                                                        print(f"[INFO] Updated Responses received count for valid message from sender: {username}")\n                                                    else:\n                                                        print(f"[INFO] Skipped system notification from: {username}")'
        
        updated_content = re.sub(pattern, replacement, content)
        
        # Update 2: Fix profiles_visited tracking in match_and_click_people function
        pattern = r'(# Update profile metrics.+?# Update visited count\s+)time_tracker\.update_session_metrics\("profiles_visited"\)'
        
        replacement = r'\1# Only count unique profile visits\n                        if profile_link not in visited_accounts_set:\n                            time_tracker.update_session_metrics("profiles_visited")\n                        else:\n                            print(f"[INFO] Profile {profile_link} already visited, not incrementing profiles_visited")'
        
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"[INFO] Successfully updated {file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update {file_path}: {e}")
        return False

def main():
    print("[INFO] Starting updates to fix Facebook message tracking issues")
    
    # Update time_tracker.py
    time_tracker_updated = update_time_tracker_main()
    
    # Update fb/auto.py
    fb_auto_updated = update_fb_auto()
    
    if time_tracker_updated and fb_auto_updated:
        print("\n[SUCCESS] All updates applied successfully!")
    else:
        print("\n[WARNING] Some updates could not be applied. Check the logs above.")
    
    print("\n[INFO] Please restart the application to apply the changes.")

if __name__ == "__main__":
    main() 