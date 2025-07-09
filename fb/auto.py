import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import random
from datetime import datetime, timedelta
from .variations import random_variation
import os
import threading
import time_tracker
import signal
import sys
import pyautogui
from selenium.webdriver.common.action_chains import ActionChains
import re
import csv
import traceback
import shutil

# Global set to store visited accounts
visited_accounts_set = set()
# Global variable for the driver instance
global driver
driver = None
# Global variable to store the currently logged-in username
current_logged_in_username = ""
# Global variables for retry tracking
retry_tracking_file = "pending_retry_tracking.csv"
retry_tracking = None

# Initialize the Selenium WebDriver
def init_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--enable-popup-blocking")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    # Use a relative path for the user data directory
    sessions_dir = os.path.join(os.getcwd(), "sessions")
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
        print(f"[INFO] Created sessions directory at: {sessions_dir}")
    
    options.add_argument(f'--user-data-dir={sessions_dir}')
    
    # Add debugging options
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--enable-logging")
    options.add_argument("--v=1")

    try:
        driver = uc.Chrome(options=options)
        print("[INFO] Chrome WebDriver started successfully.")
        return driver
    except Exception as e:
        print(f"[ERROR] Failed to start WebDriver: {e}")
        return None

def press_ctrl_c():
    # Press Ctrl+C multiple times to ensure all processes are terminated
    pyautogui.hotkey('ctrl', 'c')
    print("First Ctrl+C pressed...")
    time.sleep(1)  # Short delay between keypresses
    
    pyautogui.hotkey('ctrl', 'c')
    print("Second Ctrl+C pressed!")
    time.sleep(1)  # Short delay between keypresses

    # One more Ctrl+C for good measure
    pyautogui.hotkey('ctrl', 'c')
    print("Third Ctrl+C pressed!")
    print("11 p.m time limit reached, terminating all processes!")
    
    
    
    
    # Log data before exit
    import time_tracker
    time_tracker.log_execution_time(is_final=True)
    
    # Close browser driver if it exists
    time_tracker.quit_driver()
    
    # Force terminate the program
    import os
    os._exit(0)

def check_time_and_press_ctrl_c():
    """Background thread that checks the time and terminates the program at 11 PM."""
    print(f"[INFO] Program will terminate at 23:00 (11 PM)")
    
    while True:
        try:
            current_time = datetime.now()
            
            # Check for 11 PM
            if current_time.hour == 23 and current_time.minute == 0:
                print(f"[INFO] 11 PM reached: {current_time.strftime('%H:%M:%S')}")
                press_ctrl_c()
                break  # Exit the loop after triggering
                
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"[ERROR] Exception in time check thread: {e}")
            time.sleep(10)  # Wait longer if there's an error

# Function to log in if needed
def login_if_needed(driver, username, password):
    global current_logged_in_username
    
    if not username or not password:
        print("[ERROR] Username or password is empty. Skipping login attempt.")
        return False

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(5)  # Allow page to load

        # Check if the user is already logged in by looking for the "Home" link
        try:
            home_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home']"))
            )
            print(f"[INFO] Already logged in for {username}.")
            # Store the currently logged-in username in the global variable
            current_logged_in_username = username
            return True
        except TimeoutException:
            print("[INFO] Not logged in. Proceeding to login.")

        # If not logged in, proceed with login
        driver.get("https://www.facebook.com/login")
        time.sleep(5)  # Allow page to load

        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pass"))
        )
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "login"))
        )

        # Clear the input fields before sending keys
        email_input.clear()
        password_input.clear()

        email_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()
        time.sleep(15)  # Allow page to load

        # Check if login was successful by looking for the "Home" link again
        try:
            home_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home']"))
            )
            print(f"[INFO] Login successful for {username}.")
            # Store the currently logged-in username in the global variable
            current_logged_in_username = username
            return True
        except TimeoutException:
            print(f"[ERROR] Login failed for {username}.")
            return False

    except TimeoutException:
        print("[ERROR] Timeout while trying to log in.")
        return False
    except NoSuchElementException:
        print("[ERROR] Login elements not found.")
        return False
    except Exception as e:
        print(f"[ERROR] Error while trying to log in: {e}")
        return False

# Function to handle possible recovery from incomplete university processing
def check_university_processing_state(username):
    """
    Check if there's a state file indicating an incomplete university processing,
    and if found, mark it as processed to avoid reprocessing it.
    """
    recovery_file = f"university_in_progress_{username}.txt"
    processed_universities_file = "processed_universities.csv"
    
    if os.path.exists(recovery_file):
        try:
            # Read the university name from the recovery file
            with open(recovery_file, "r") as f:
                university_name = f.read().strip()
            
            if university_name:
                print(f"[INFO] Found partially processed university: '{university_name}'")
                
                # Normalize the name for matching
                normalized_name = normalize_university_name(university_name)
                print(f"[INFO] Normalized name for recovery: '{normalized_name}'")
                
                # Check if it's already in the processed list
                if os.path.exists(processed_universities_file):
                    try:
                        # Get previously processed universities
                        processed_list, normalized_set = safely_read_processed_universities(processed_universities_file, username)
                        
                        # Check if this university is already in the normalized set
                        if normalized_name in normalized_set:
                            print(f"[INFO] University '{university_name}' already marked as processed, skipping recovery")
                        else:
                            # Mark it as processed
                            print(f"[INFO] Marking recovered university '{university_name}' as processed")
                            safely_write_processed_university(processed_universities_file, university_name, username)
                    except Exception as e:
                        print(f"[ERROR] Error checking if university is already processed: {e}")
                        # Still try to mark as processed to be safe
                        safely_write_processed_university(processed_universities_file, university_name, username)
                else:
                    # No processed file exists, create it and mark university as processed
                    safely_write_processed_university(processed_universities_file, university_name, username)
                    print(f"[INFO] Created processed universities file and marked '{university_name}' as processed")
            
            # Delete the recovery file
            os.remove(recovery_file)
            print(f"[INFO] Recovery file deleted")
            
        except Exception as e:
            print(f"[ERROR] Error handling recovery file: {e}")
            # Try to delete the file even if there was an error
            try:
                os.remove(recovery_file)
            except:
                pass

# Function to normalize university names for matching
def normalize_university_name(name):
    """
    Normalize a university name for consistent matching by:
    - Converting to lowercase
    - Removing leading/trailing whitespace
    - Removing common words and prefixes that don't affect matching
    - Removing special characters
    
    Returns the normalized name for matching purposes.
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common prefixes that don't affect matching
    prefixes_to_remove = ["the ", "university of ", "the university of "]
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    
    # Remove common words that don't affect matching
    if normalized == "university":
        return ""  # This is just the column header, not a real university
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove special characters
    normalized = re.sub(r'\s+', ' ', normalized)     # Replace multiple spaces with single space
    
    return normalized.strip()

# Function to safely read processed universities
def safely_read_processed_universities(file_path, username):
    """
    Safely read the processed universities file and return a list of universities
    processed by the given username. Handles cases where the file might be corrupted.
    """
    processed_list = []
    
    # If file doesn't exist, return empty list
    if not os.path.exists(file_path):
        # Also return a set of normalized university names for efficient lookup
        normalized_set = set()
        return processed_list, normalized_set
        
    try:
        # First try the standard pandas read
        df = pd.read_csv(file_path)
        
        # Check if the DataFrame has the expected columns
        if set(['university', 'processed_by', 'timestamp']).issubset(df.columns):
            # Filter by username and get list of universities
            processed_list = df[df['processed_by'] == username]['university'].tolist()
            # Create a set of normalized university names for efficient lookup
            normalized_set = {normalize_university_name(uni) for uni in processed_list if uni}
            return processed_list, normalized_set
        else:
            print(f"[WARNING] Processed universities file has incorrect columns")
    except Exception as e:
        print(f"[WARNING] Error reading processed universities file: {e}")
    
    # If pandas read fails, try manual CSV parsing as fallback
    try:
        manual_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip header row
            
            # Find index of university and processed_by columns
            if header:
                try:
                    uni_idx = header.index('university')
                    user_idx = header.index('processed_by')
                    
                    # Read each row
                    for row in reader:
                        if len(row) > max(uni_idx, user_idx) and row[user_idx] == username:
                            manual_list.append(row[uni_idx])
                except ValueError:
                    print(f"[WARNING] Could not find required columns in CSV header")
        
        if manual_list:
            print(f"[INFO] Recovered {len(manual_list)} universities using fallback method")
            # Create a set of normalized university names for efficient lookup
            normalized_set = {normalize_university_name(uni) for uni in manual_list if uni}
            return manual_list, normalized_set
    except Exception as e:
        print(f"[WARNING] Manual CSV reading also failed: {e}")
    
    # If all reading methods fail, return empty list but recreate the file
    try:
        # Backup the existing file if it exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.bak.{int(time.time())}"
            os.rename(file_path, backup_path)
            print(f"[INFO] Backed up corrupted file to {backup_path}")
        
        # Create a new file with the correct headers
        pd.DataFrame(columns=['university', 'processed_by', 'timestamp']).to_csv(file_path, index=False)
        print(f"[INFO] Created new {file_path} with correct headers")
    except Exception as e:
        print(f"[ERROR] Could not create new processed universities file: {e}")
    
    # Return empty list and empty set if all methods fail
    return processed_list, set()

# Function to safely write to the processed universities file
def safely_write_processed_university(file_path, university, username):
    """
    Safely append a university to the processed universities file.
    Includes error handling and ensures the file isn't corrupted.
    """
    try:
        # Create a backup of the current file before writing
        if os.path.exists(file_path):
            temp_backup = f"{file_path}.temp"
            try:
                shutil.copy2(file_path, temp_backup)
            except Exception as backup_error:
                print(f"[WARNING] Could not create temp backup: {backup_error}")
        
        # Create the new entry
        new_entry = pd.DataFrame({
            'university': [university],
            'processed_by': [username],
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        
        # First try using pandas append mode
        try:
            # Check if file exists and has headers
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                new_entry.to_csv(file_path, mode='a', header=False, index=False)
            else:
                # Create new file with headers
                new_entry.to_csv(file_path, index=False)
            print(f"[INFO] Successfully marked '{university}' as processed by {username}")
            
            # If successful, remove the temp backup
            if os.path.exists(temp_backup):
                try:
                    os.remove(temp_backup)
                except:
                    pass
                    
            return True
        except Exception as e:
            print(f"[WARNING] Primary write method failed: {e}")
            
            # Fall back to direct CSV writing
            try:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    with open(file_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([university, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                else:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow(['university', 'processed_by', 'timestamp'])
                        # Write data
                        writer.writerow([university, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                
                print(f"[INFO] Successfully marked '{university}' as processed using fallback method")
                
                # If successful, remove the temp backup
                if os.path.exists(temp_backup):
                    try:
                        os.remove(temp_backup)
                    except:
                        pass
                        
                return True
            except Exception as csv_error:
                print(f"[ERROR] Fallback write method also failed: {csv_error}")
                
                # Restore from backup if possible
                if os.path.exists(temp_backup):
                    try:
                        shutil.copy2(temp_backup, file_path)
                        print(f"[INFO] Restored file from backup after write failure")
                    except Exception as restore_error:
                        print(f"[ERROR] Failed to restore from backup: {restore_error}")
                
                return False
    except Exception as outer_error:
        print(f"[ERROR] Failed to process university write: {outer_error}")
        return False

# Function to handle the process
def main_handler(username, password, univer):
    # Check for any incomplete university processing from previous run
    check_university_processing_state(username)
    
    # Start a new tracking session
    time_tracker.begin_session(username)
    
    # Log the university data source
    print(f"[INFO] Using provided university DataFrame with {len(univer)} universities")
    if 'university' in univer.columns:
        print(f"[INFO] First few universities: {', '.join(univer['university'].head(3).tolist())}")
    
    # Initialize metrics - reset for this session
    time_tracker.profiles_fetched = 0
    time_tracker.profiles_visited = 0
    time_tracker.profiles_matched = 0
    time_tracker.sent_messages = 0
    time_tracker.deleted_users = 0
    time_tracker.responses_received = 0
    time_tracker.already_sent = 0
    
    # Start the time check thread
    time_check_thread = threading.Thread(target=check_time_and_press_ctrl_c, daemon=True)
    time_check_thread.start()
    print("[INFO] Time check thread started - program will terminate at 11:00 PM")
    
    # Calculate initial carry forward counts
    if os.path.exists("visited_accounts.csv"):
        try:
            visited_accounts = pd.read_csv("visited_accounts.csv")
            # Ensure the CSV has the right columns
            required_columns = ['link', 'name', 'timestamp', 'status', 'searched_by', 'university']
            
            # Check if all required columns exist, if not, add them
            for col in required_columns:
                if col not in visited_accounts.columns:
                    # Add the missing column with default values
                    if col == 'searched_by':
                        visited_accounts[col] = 'Facebook'  # Default value for searched_by
                    else:
                        visited_accounts[col] = ''  # Empty string for other columns
                    print(f"[INFO] Added missing column '{col}' to visited_accounts.csv")
            
            # Save the updated file with all required columns
            visited_accounts.to_csv("visited_accounts.csv", index=False)
            
            pending_profiles = len(visited_accounts[visited_accounts['status'] == 'pending'])
            pending_messages = pending_profiles  # Assuming one message per pending profile
            
            # Initialize visited_accounts_set from the CSV file at startup
            global visited_accounts_set
            visited_accounts_set = set(visited_accounts['link'].tolist())
            print(f"[INFO] Loaded {len(visited_accounts_set)} previously visited profiles")
            
            # Add unvisited profiles from previous sessions to carry forward count
            unvisited_profiles_count = 0
            if os.path.exists("unvisited_profiles.csv"):
                unvisited_profiles = pd.read_csv("unvisited_profiles.csv")
                # Remove any profiles that are now in visited_accounts_set
                unvisited_profiles = unvisited_profiles[~unvisited_profiles['link'].isin(visited_accounts_set)]
                unvisited_profiles_count = len(unvisited_profiles)
                # Save the updated file
                unvisited_profiles.to_csv("unvisited_profiles.csv", index=False)
                print(f"[INFO] Found {unvisited_profiles_count} unvisited profiles from previous sessions")
            
            # Total carry forward is pending + unvisited
            total_carry_forward = pending_profiles + unvisited_profiles_count
            
            # Set carry forward metrics
            time_tracker.update_session_metrics("carry_forward_profiles", total_carry_forward)
            time_tracker.update_session_metrics("carry_forward_messages", pending_messages)
            
            print(f"[INFO] Starting with carry forward: {total_carry_forward} profiles, {pending_messages} messages")
        except Exception as e:
            print(f"[ERROR] Error calculating carry forward metrics: {e}")
    else:
        # Create the file with proper headers if it doesn't exist
        visited_accounts = pd.DataFrame(columns=['link', 'name', 'timestamp', 'status', 'searched_by', 'university'])
        visited_accounts.to_csv("visited_accounts.csv", index=False)
        print("[INFO] Created visited_accounts.csv with proper headers")
    
    global driver
    driver = init_driver()
    
    # Check if driver was initialized successfully
    if driver is None:
        print("[ERROR] Failed to initialize driver. Exiting.")
        return
        
    if not login_if_needed(driver, username, password):
        if driver is not None:
            driver.quit()
        return

    # Check for notifications right after login
    print("[INFO] Checking for notifications after login...")
    try:
        # Only proceed with driver operations if driver is not None
        if driver is not None:
        # First check if we're still on Facebook
            if "facebook.com" not in driver.current_url:
                print("[INFO] Not on Facebook, navigating back...")
                driver.get("https://www.facebook.com")
                time.sleep(3)
            
            # Now check for notifications
            notification_count = check_notifications(driver)
            if notification_count > 0:
                print(f"[INFO] Found and processed {notification_count} new notifications")
            else:
                print("[INFO] No new notifications found, continuing with search")
        else:
            print("[ERROR] Driver is None, cannot check notifications")
    except Exception as notification_error:
        print(f"[ERROR] Error checking notifications: {notification_error}")

    visited_accounts_file = "visited_accounts.csv"
    
    # Check or create the processed universities tracking file
    processed_universities_file = "processed_universities.csv"
    if not os.path.exists(processed_universities_file):
        # Create the file with headers
        pd.DataFrame(columns=['university', 'processed_by', 'timestamp']).to_csv(processed_universities_file, index=False)
        print(f"[INFO] Created {processed_universities_file} to track processed universities")
    
    # Load the processed universities using the safe function
    processed_by_user, normalized_processed = safely_read_processed_universities(processed_universities_file, username)
    
    print(f"[INFO] Found {len(processed_by_user)} universities already processed by {username}")
    
    # Log all processed universities for debugging
    if processed_by_user:
        print(f"[DEBUG] Already processed universities: {', '.join(processed_by_user[:10])}")
        if len(processed_by_user) > 10:
            print(f"[DEBUG] ... and {len(processed_by_user) - 10} more")
    
    # Create a list to store universities processed in this session
    processed_in_this_session = []
    
    # Only pick universities that haven't been processed yet
    universities_to_process = []
    for index, row in univer.iterrows():
        university_name = row['university']
        
        # Skip if university name is just "university" (column header)
        if not university_name or university_name.lower() == "university":
            continue
            
        # Normalize the name for comparison
        normalized_name = normalize_university_name(university_name)
        if not normalized_name:  # Skip empty names after normalization
            continue
        
        # Skip if university was already processed by this user using normalized names
        if normalized_name in normalized_processed:
            print(f"[INFO] Skipping already processed university: '{university_name}'")
            continue
            
        universities_to_process.append((index, university_name, normalized_name))
    
    print(f"[INFO] Found {len(universities_to_process)} universities left to process")
    
    # Process each university that hasn't been processed yet
    for index, university_name, normalized_name in universities_to_process:
        try:
            print(f"[INFO] Searching for university: {university_name} for {username}.")
            
            # Create a recovery file to track the current university being processed
            recovery_file = f"university_in_progress_{username}.txt"
            try:
                with open(recovery_file, "w") as f:
                    f.write(university_name)
                print(f"[INFO] Created recovery file for '{university_name}'")
            except Exception as e:
                print(f"[WARNING] Could not create recovery file: {e}")
            
            # Mark this university as processed BEFORE we start processing
            # This prevents reprocessing if the script crashes during university processing
            if safely_write_processed_university(processed_universities_file, university_name, username):
                # Add to our in-memory lists to avoid duplicates in this session
                processed_by_user.append(university_name)
                normalized_processed.add(normalized_name)
                processed_in_this_session.append(university_name)
                print(f"[INFO] Marked university '{university_name}' as processed (normalized: '{normalized_name}')")
            
            # Now actually process the university
            if driver is not None:
                driver.get(f"https://www.facebook.com/search/groups?q={university_name}")
                time.sleep(4)

                set_public_groups_filter(driver)

                # Pass `username` and `password`
                match_and_click_searched_items(driver, univer, visited_accounts_file, university_name, username, password)
                
                # Check for notifications after completing university search
                print("[INFO] Checking for new notifications after university search...")
                try:
                    # First check if we're still on Facebook
                    if "facebook.com" not in driver.current_url:
                        print("[INFO] Not on Facebook, navigating back...")
                        driver.get("https://www.facebook.com")
                        time.sleep(3)
                    
                    # Now check for notifications
                    notification_count = check_notifications(driver)
                    if notification_count > 0:
                        print(f"[INFO] Found and processed {notification_count} new notifications")
                    else:
                        print("[INFO] No new notifications found, continuing with search")
                except Exception as notification_error:
                    print(f"[ERROR] Error checking notifications: {notification_error}")
            else:
                print("[ERROR] Driver is None, cannot search for university")
            
            # Remove the recovery file since processing is complete
            try:
                if os.path.exists(recovery_file):
                    os.remove(recovery_file)
                    print(f"[INFO] Removed recovery file for '{university_name}'")
            except Exception as e:
                print(f"[WARNING] Could not remove recovery file: {e}")
            
            # Force update of summary table after each university
            time_tracker.log_execution_time(is_final=False)

        except WebDriverException as e:
            if "invalid session id" in str(e):
                print("[ERROR] Invalid session id. Reinitializing driver...")
                if driver is not None:
                    driver.quit()
                    driver = init_driver()
                    if driver is None:
                        print("[ERROR] Failed to reinitialize driver. Exiting.")
                        return
                    
                if not login_if_needed(driver, username, password):
                    if driver is not None:
                        driver.quit()
                        return
            else:
                print(f"[ERROR] Unexpected error while searching for university: {e}")
    
    # Log the universities that were processed in this session
    if processed_in_this_session:
        print(f"[INFO] Universities processed in this session ({len(processed_in_this_session)}):")
        for i, uni in enumerate(processed_in_this_session):
            print(f"  {i+1}. {uni}")
    else:
        print(f"[INFO] No new universities were processed in this session.")

    # Calculate final carry forward counts for next session
    if os.path.exists("visited_accounts.csv"):
        try:
            visited_accounts = pd.read_csv("visited_accounts.csv")
            final_pending_profiles = len(visited_accounts[visited_accounts['status'] == 'pending'])
            
            # Update unvisited_profiles.csv to remove any newly visited profiles
            if os.path.exists("unvisited_profiles.csv"):
                unvisited_profiles = pd.read_csv("unvisited_profiles.csv")
                # Remove any profiles that are now in visited_accounts_set
                unvisited_profiles = unvisited_profiles[~unvisited_profiles['link'].isin(visited_accounts_set)]
                unvisited_profiles_count = len(unvisited_profiles)
                # Save the updated file
                unvisited_profiles.to_csv("unvisited_profiles.csv", index=False)
                print(f"[INFO] Updated unvisited profiles: {unvisited_profiles_count} remaining")
                
                # Calculate final carry forward for the next session
                final_carry_forward = final_pending_profiles + unvisited_profiles_count
                time_tracker.update_session_metrics("carry_forward_profiles", final_carry_forward)
                
                # Update carry forward messages (only pending profiles need messages)
                time_tracker.update_session_metrics("carry_forward_messages", final_pending_profiles)
                
                print(f"[INFO] Ending with carry forward profiles: {final_carry_forward}")
                print(f"[INFO] Ending with carry forward messages: {final_pending_profiles}")
            else:
                time_tracker.update_session_metrics("carry_forward_profiles", final_pending_profiles)
                time_tracker.update_session_metrics("carry_forward_messages", final_pending_profiles)
                print(f"[INFO] Ending with pending profiles: {final_pending_profiles}")
                print(f"[INFO] Ending with pending messages: {final_pending_profiles}")
        except Exception as e:
            print(f"[ERROR] Error calculating final metrics: {e}")
    
    # Clean up any remaining recovery file at the end
    try:
        recovery_file = f"university_in_progress_{username}.txt"
        if os.path.exists(recovery_file):
            os.remove(recovery_file)
            print(f"[INFO] Removed lingering recovery file for {username}")
    except Exception as e:
        print(f"[WARNING] Could not remove lingering recovery file: {e}")
    
    # Ensure summary table is updated at the end
    time_tracker.log_execution_time(is_final=True)
    
    # Stop the background logging
    time_tracker.stop_background_logging()

    if driver is not None:
        driver.quit()

def set_public_groups_filter(driver):
    try:
        # Click on the filter to set it to public groups only
        public_groups_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='switch' and @type='checkbox' and contains(@aria-label, 'Public groups')]"))
        )
        public_groups_filter.click()
        time.sleep(5)  # Wait for the filter to apply

        print("[INFO] Set the filter to public groups only.")

    except TimeoutException:
        print("[ERROR] Timeout while waiting for the public groups filter to be clickable.")
    except NoSuchElementException:
        print("[ERROR] Public groups filter element not found.")
    except Exception as e:
        print("[ERROR] Error while setting the filter to public groups only: {e}")

def match_and_click_searched_items(driver, univer, visited_accounts_file, university_name, username, password):
    try:
        # Create a dictionary to track which university matched each group
        group_university_map = {}
        
        # Find all searched items
        searched_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='article']//a"))
        )

        # Get all university names from the uploaded file for strict matching
        all_university_names = univer['university'].tolist()
        
        # Remove the column name "university" if it accidentally got included in the data
        all_university_names = [uni for uni in all_university_names if uni.lower() != "university"]
        print(f"[INFO] Filtered out column name 'university' from the list of universities to search")
        
        # Also check for case variations and empty strings
        all_university_names = [uni for uni in all_university_names if uni and uni.strip() and uni.lower() != "university"]
        print(f"[INFO] Will match against {len(all_university_names)} valid universities from uploaded file")
        
        # Convert to lowercase for case-insensitive matching
        all_university_names_lower = [uni.lower() for uni in all_university_names]
        
        # Skip current university name if it's just "university"
        if university_name.lower() == "university":
            print(f"[INFO] Skipping invalid university name: '{university_name}'")
            return
        
        # Extract links of matched items that actually match universities in the file
        matched_links = []
        for item in searched_items:
            title = item.text
            link = item.get_attribute('href')
            
            # Only proceed if we have a non-empty title and link
            if not title or not link:
                continue
                
            # Check if any university from our list is in the title
            is_relevant = False
            matched_university = None
            
            # First, check for an exact match with the current search university
            if university_name.lower() in title.lower():
                is_relevant = True
                matched_university = university_name
            else:
                # If not an exact match with current search term, check all universities
                for uni in all_university_names:
                    # Check for matches that are at least 60% of the university name length
                    # This avoids matching very short substrings
                    min_match_length = max(5, len(uni) * 0.6)  # At least 5 chars or 60% of uni name
                    
                    # Only count as match if substantial part of university name appears in title
                    if len(uni) >= min_match_length and uni.lower() in title.lower():
                        is_relevant = True
                        matched_university = uni
                        break
            
            # Add to matched links only if it's relevant
            if is_relevant:
                print(f"[INFO] Found relevant group: '{title}' - Matched university: '{matched_university}'")
                matched_links.append(link)
                group_university_map[link] = matched_university
            else:
                print(f"[DEBUG] Skipping irrelevant group: '{title}'")

        # Limit to top 3 matched links
        matched_links = matched_links[:3]
        print(f"[INFO] Found {len(matched_links)} relevant groups to process")

        # Click on matched links one by one
        for link in matched_links:
            if link not in visited_accounts_set:
                driver.get(link)
                time.sleep(5)  # Wait for the page to load
                print(f"[INFO] Clicked on the link: {link}")

                # Click on the "People" tab
                click_people_tab(driver)

                # Get the matched university for this group
                matched_university = group_university_map.get(link, "")
                print(f"[INFO] Using matched university for this group: '{matched_university}'")

                # Match university name with people in the "People" tab and click on their profile
                match_and_click_people(driver, univer, visited_accounts_file, link, username, password, matched_university)
            else:
                print(f"[INFO] Skipping already visited group: {link}")
                # Skip already seen groups, but don't count as already sent
                # This isn't a duplicate message, just a previously visited group

    except TimeoutException:
        print("[ERROR] Timeout while waiting for the searched items to be clickable.")
    except NoSuchElementException:
        print("[ERROR] Searched items element not found.")
    except Exception as e:
        print(f"[ERROR] Error while matching and clicking on the searched items: {e}")

def click_people_tab(driver):
    try:
        # Find the "People" tab
        people_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'members') and contains(@role, 'tab')]"))
        )
        # Scroll the "People" tab into view
        driver.execute_script("arguments[0].scrollIntoView(false);", people_tab)
        time.sleep(1)  # Wait for the scrolling to complete

        # Click on the "People" tab
        people_tab.click()
        time.sleep(5)  # Wait for the people tab to load

        print("[INFO] Clicked on the 'People' tab.")

    except TimeoutException:
        print("[ERROR] Timeout while waiting for the 'People' tab to be clickable.")
    except NoSuchElementException:
        print("[ERROR] 'People' tab element not found.")
    except Exception as e:
        print("[ERROR] Error while clicking on the 'People' tab: {e}")

def match_and_click_people(driver, univer, visited_accounts_file, group_link, username, password, matched_university):
    try:
        # Maximum number of retries for stale elements
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Initialize variables for infinite scrolling
                last_height = driver.execute_script("return document.body.scrollHeight")
                no_change_count = 0
                max_no_change = 15  # Number of times height can remain unchanged before we consider we've reached the end
                max_scroll_attempts = 300000  # Increased max scroll attempts to a much higher value
                scroll_attempts = 0
                
                print("[INFO] Scrolling through the page to load all profiles...")
                
                # Keep scrolling until we're sure we've reached the end
                while scroll_attempts < max_scroll_attempts and no_change_count < max_no_change:
                    # Scroll down
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for content to load
                    
                    # Check if page height has changed after scrolling
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        no_change_count += 1
                    else:
                        # Reset the no change counter if the height changes
                        no_change_count = 0
                    
                    last_height = new_height
                    scroll_attempts += 1
                
                print(f"[INFO] Completed scrolling after {scroll_attempts} attempts")

                # Now find all people items after scrolling is complete
                people_items = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x2lah0s.x193iq5w.x1gslohp.x12nagc.xzboxd6.x14l7nz5 a")
                    )
                )

                print(f"[INFO] Found {len(people_items)} people items after complete scrolling.")
                random_variation()

                # All profile links (including irrelevant ones)
                all_profile_links = []
                # Only relevant profile links (not already visited)
                relevant_profile_links = []
                
                # Get all the links first to avoid stale element issues
                for item in people_items:
                    try:
                        link = item.get_attribute('href')
                        if link:
                            all_profile_links.append(link)
                    except Exception as e:
                        print(f"[WARNING] Error getting link from element: {e}")
                
                # Pre-filter the links to get only valid profile links
                valid_profile_links = []
                for link in all_profile_links:
                    if link and ("profile.php?id=" in link or "/user/" in link):
                        valid_profile_links.append(link)
                    else:
                        print(f"[DEBUG] Skipped non-profile link: {link}")
                
                # Deduplicate links - sometimes Facebook shows the same profile multiple times
                valid_profile_links = list(set(valid_profile_links))
                
                # Now check which profiles haven't been visited yet
                for link in valid_profile_links:
                        if link not in visited_accounts_set:
                            relevant_profile_links.append(link)
                        else:
                            print(f"[INFO] Skipping already visited profile: {link}")

                # Save all unvisited profiles to a file for future sessions
                # Get the actual count of profiles saved to the CSV
                actual_saved_count = save_unvisited_profiles(relevant_profile_links)
                
                # Only show relevant profile links count - now using the actual saved count
                print(f"[INFO] Found {actual_saved_count} new relevant profile links.")
                
                # Update the time_tracker with the count of ACTUALLY SAVED profiles
                time_tracker.update_profiles_count(actual_saved_count)

                # Track profiles visited
                profiles_visited = 0
                
                # Create a list to store usernames
                usernames_list = []
                
                for link in relevant_profile_links:
                    # Add to visited_accounts_set BEFORE navigating to prevent future visits
                    # and to prevent duplicate visits within the same session
                    visited_accounts_set.add(link)
                        
                    # Refresh the page state by navigating to the link directly
                    driver.get(link)
                    time.sleep(5)
                    print(f"[INFO] Checking profile: {link}")
                    
                    # Increment profiles visited
                    profiles_visited += 1
                    time_tracker.update_session_metrics("profiles_visited")

                    # Click View Profile and check the overview section in one function
                    process_profile(driver, univer, visited_accounts_file, link, username, password, matched_university)

                # Update visited count in summary
                print(f"[INFO] Visited {profiles_visited} profiles in this group")
                
                # Update summary table after processing profiles in this group
                time_tracker.log_execution_time(is_final=False)
                
                # If we get here without errors, break the retry loop
                break
                
            except (StaleElementReferenceException, WebDriverException) as e:
                retry_count += 1
                print(f"[WARNING] Stale element or WebDriver error, retrying ({retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    print("[ERROR] Maximum retries reached, giving up.")
                    raise
                # Refresh the page to get a fresh DOM
                driver.refresh()
                time.sleep(5)

    except TimeoutException:
        print("[ERROR] Timeout while waiting for the people items to be clickable.")
    except NoSuchElementException:
        print("[ERROR] People items element not found.")
    except Exception as e:
        print(f"[ERROR] Error while matching and clicking on the people items: {e}")

def process_profile(driver, univer, visited_accounts_file, profile_link, username, password, matched_university):
    global current_logged_in_username
    
    try:
        # Click "View Profile" button
        view_profile_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'View profile')]"))
        )
        view_profile_link.click()
        time.sleep(5)  # Wait for the profile page to load
        print("[INFO] Clicked on the 'View Profile' link.")

        # Now check the overview section
        return check_overview_section(driver, univer, visited_accounts_file, profile_link, username, password, matched_university)
    
    except Exception as e:
        print(f"[ERROR] Error in process_profile: {e}")
        # Mark profile as locked/error in the visited accounts file
        user_name = "Unknown" # Default name for locked profiles
        try:
            # Try to get the name if possible
            user_name = extract_text_from_element(driver, "//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x14qwyeo xw06pyt x579bpy xjkpybl x1xlr1w8 xzsf02u x1yc453h']")
        except:
            pass
            
        # No need to add to visited_accounts_set here since we already did before navigation
        
        # Add to visited accounts with error status and include the global username
        search_username = current_logged_in_username if current_logged_in_username else username
        new_entry = pd.DataFrame({
            "link": [profile_link], 
            "name": [user_name], 
            "timestamp": [pd.Timestamp.now()], 
            "status": ["locked"], 
            "searched_by": [search_username],
            "university": [matched_university]
        })
        
        # Use the safe CSV write function to avoid duplicates
        safe_write_to_csv(new_entry, visited_accounts_file)
        
        return "error"

def send_message(driver, message, visited_accounts, visited_accounts_file, profile_link):
    try:
        # Add a longer delay to ensure page is fully loaded
        time.sleep(10)
        
        # First check if we're on an actual profile page
        try:
            current_url = driver.current_url
            if "facebook.com" not in current_url:
                print(f"[ERROR] Not on Facebook - current URL: {current_url}")
                return False
            
            if "/profile.php" not in current_url and "/user/" not in current_url and "/groups/" not in current_url:
                print(f"[ERROR] Not on a profile page - current URL: {current_url}")
                return False
        except Exception as e:
            print(f"[ERROR] Error checking current URL: {e}")
            return False
        
        # Try multiple approaches to find the message button with retries
        message_button = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Looking for message button (attempt {attempt+1}/{max_retries})...")
                
                # Approach 1: Standard XPath
                try:
                    message_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft'][normalize-space()='Message']"))
                    )
                    print("[INFO] Found message button with standard XPath")
                    break
                except Exception:
                    print("[INFO] Standard XPath for message button failed, trying alternative approaches")
                
                # Approach 2: More general XPath
                try:
                    message_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Message') and contains(@class, 'x1lliihq')]"))
                    )
                    print("[INFO] Found message button with general XPath")
                    break
                except Exception:
                    print("[INFO] General XPath for message button failed, trying next approach")
                
                # Approach 3: Find by div with specific text
                try:
                    message_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@role, 'button') and .//span[contains(text(), 'Message')]]"))
                    )
                    print("[INFO] Found message button with role and text XPath")
                    break
                except Exception:
                    print("[INFO] Role+text XPath for message button failed")
                
                # If we reach here, no approach worked in this attempt
                if attempt < max_retries - 1:
                    print(f"[INFO] Message button not found in attempt {attempt+1}, refreshing page and retrying...")
                    try:
                        driver.refresh()
                        time.sleep(10)  # Wait longer after refresh
                    except Exception as e:
                        print(f"[ERROR] Error refreshing page: {e}")
            
            except Exception as e:
                print(f"[ERROR] Error in message button search attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before next attempt
        
        if message_button is None:
            print("[ERROR] Failed to find message button after all attempts")
            return False
        
        # Try to click with multiple methods
        click_success = False
        try:
            # Method 1: Standard click
            message_button.click()
            click_success = True
            print("[INFO] Clicked message button with standard click")
        except Exception as e:
            print(f"[WARNING] Standard click failed: {e}")
            
            try:
                # Method 2: JavaScript click
                driver.execute_script("arguments[0].click();", message_button)
                click_success = True
                print("[INFO] Clicked message button with JavaScript")
            except Exception as e:
                print(f"[WARNING] JavaScript click failed: {e}")
                
                try:
                    # Method 3: ActionChains click
                    ActionChains(driver).move_to_element(message_button).click().perform()
                    click_success = True
                    print("[INFO] Clicked message button with ActionChains")
                except Exception as e:
                    print(f"[ERROR] All click methods failed: {e}")
        
        if not click_success:
            print("[ERROR] Could not click message button with any method")
            return False
            
        # Wait longer for the message window to load
        time.sleep(10)

        # First check if there's any actual message history (not profile info)
        print("[DEBUG] Checking for existing messages in message history...")
        
        # Try multiple selectors to find message history
        message_found = False
        
        # Look for actual chat messages, not profile information
        try:
            print("[DEBUG] Looking for actual chat bubbles...")
            # This selector targets ONLY actual chat bubbles, not profile information
            chat_bubbles = driver.find_elements(By.XPATH, "//div[contains(@class, 'x78zum5') and contains(@class, 'xh8yej3')]//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1hq5gj4')]")
            
            if chat_bubbles and len(chat_bubbles) > 0:
                print(f"[DEBUG] Found {len(chat_bubbles)} potential chat bubbles")
                # Check if any bubble contains our test message
                for i, bubble in enumerate(chat_bubbles):
                    try:
                        bubble_text = bubble.text.strip()
                        # Skip empty or very long texts (likely profile info)
                        if not bubble_text or len(bubble_text) > 200:
                            continue
                            
                        print(f"[DEBUG] Chat bubble {i+1} text: '{bubble_text}'")
                        # Check for actual message content, not UI elements or profile info
                        if ("Hi" in bubble_text or "hi" in bubble_text or "how are you" in bubble_text.lower()) and len(bubble_text) < 20:
                            print("[INFO] Message already sent to this profile before - found in chat bubbles.")
                            # Track as already sent - INCREMENT BY EXACTLY 1
                            time_tracker.update_session_metrics("already_sent", 1)
                            print("[INFO] Already sent count incremented by 1")
                            
                            # Update status in visited_accounts.csv to "already_sent"
                            if profile_link in visited_accounts['link'].values:
                                visited_accounts.loc[visited_accounts['link'] == profile_link, 'status'] = 'already_sent'
                                visited_accounts.to_csv(visited_accounts_file, index=False)
                                print(f"[INFO] Updated status of {profile_link} to 'already_sent' in CSV")
                            
                            # Close the message box - try multiple methods
                            safe_close_message_box(driver)
                            message_found = True
                            return True
                    except Exception as e:
                        print(f"[WARNING] Error checking chat bubble text: {e}")
                        continue
            else:
                print("[DEBUG] No chat bubbles found - this appears to be a new conversation")
        except Exception as e:
            print(f"[WARNING] Error checking chat bubbles: {e}")
        
        # Check if message thread is empty based on UI elements
        try:
            # Look for the "empty thread" indicator or message input placeholder
            empty_thread_indicators = driver.find_elements(By.XPATH, "//div[contains(text(), 'New message') or contains(text(), 'Say hi')]")
            if empty_thread_indicators:
                print("[DEBUG] This appears to be an empty message thread based on UI elements.")
                # Continue with sending message
            else:
                print("[DEBUG] No empty thread indicators found.")
        except Exception as e:
            print(f"[WARNING] Error checking empty thread indicators: {e}")
        
        # If we still haven't found a message, try one final check for the input area
        if not message_found:
            try:
                # Check if the input area has a placeholder that says "Say hi" or similar
                input_placeholder = driver.find_elements(By.XPATH, "//div[contains(@class, 'xat24cr')]//p[contains(text(), 'Say hi') or contains(text(), 'Aa')]")
                if input_placeholder:
                    print("[DEBUG] Found input placeholder - this is likely a new conversation.")
                    # This is a new conversation, proceed with sending message
                else:
                    # Look for message composer area
                    composer = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
                    if composer:
                        print("[DEBUG] Found message composer - proceeding with new message.")
                    else:
                        print("[DEBUG] No message composer found - conversation state unclear.")
            except Exception as e:
                print(f"[WARNING] Error checking input area: {e}")

        # If no matching messages were found, proceed with sending
        if not message_found:
            print("[DEBUG] No existing matching messages found. Proceeding to send new message.")
            
            try:
                # Try multiple approaches to find the message box
                message_box = None
                
                # Approach 1: Standard XPath
                try:
                    message_box = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//p[@class='xat24cr xdj266r']"))
                        #EC.presence_of_element_located((By.XPATH, "//p[@class='xat24cr xdj266r'] | //div[@role='textbox' and @contenteditable='true']"))
                    )
                    print("[INFO] Found message box with standard XPath")
                except Exception:
                    print("[INFO] Standard XPath for message box failed, trying alternative approaches")
                
                # Approach 2: More general XPath for contenteditable divs
                if message_box is None:
                    try:
                        message_box = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                        )
                        print("[INFO] Found message box with general contenteditable XPath")
                    except Exception:
                        print("[INFO] General contenteditable XPath for message box failed")
                
                # Approach 3: Try to find by role only
                if message_box is None:
                    try:
                        message_box = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                        )
                        print("[INFO] Found message box with role XPath")
                    except Exception:
                        print("[INFO] Role XPath for message box failed")
                
                # If all approaches failed, try a final fallback
                if message_box is None:
                    try:
                        # Look for anything editable in the message dialog
                        message_dialog = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                        )
                        # Search within this dialog
                        message_box = message_dialog.find_element(By.XPATH, ".//div[contains(@class, 'xat24cr') or @contenteditable='true']")
                        print("[INFO] Found message box with dialog context search")
                    except Exception:
                        print("[ERROR] All approaches for finding message box failed")
                
                if message_box is None:
                    print("[ERROR] Could not find message box with any method")
                    # Update carry forward messages counter
                    time_tracker.increment_carried_forward_messages(1)
                    
                    # Add this profile to the retry tracking
                    update_retry_tracking(profile_link, increment=True)
                    
                    return False
                
                # Try different ways to enter text
                input_success = False
                
                # Method 1: Type letter by letter (most reliable)
                try:
                    print("[INFO] Attempting to enter message character by character...")
                    # Clear any existing text first
                    try:
                        message_box.clear()
                    except:
                        pass
                        
                    # Type the message letter by letter with random timing
                    for char in message:
                        message_box.send_keys(char)
                        time.sleep(random.uniform(0.1, 0.3))  # Random timing between keystrokes
                    
                    # Give a moment for the text to be registered
                    time.sleep(2)
                    
                    # Verify text was entered
                    try:
                        entered_text = message_box.text or message_box.get_attribute("textContent")
                        if entered_text and len(entered_text) > 0:
                            input_success = True
                            print(f"[INFO] Successfully entered message text: '{entered_text}'")
                        else:
                            print("[WARNING] Text appears to be empty after entering")
                    except:
                        # Can't verify, but assume it worked
                        input_success = True
                except Exception as e:
                    print(f"[WARNING] Character-by-character input failed: {e}")
                
                # Method 2: Use JavaScript directly
                if not input_success:
                    try:
                        print("[INFO] Attempting to enter message with JavaScript...")
                        js_script = f"arguments[0].textContent = '{message}';"
                        driver.execute_script(js_script, message_box)
                        time.sleep(2)
                        
                        # Trigger input event to make sure Facebook registers the text
                        driver.execute_script("""
                            var event = new Event('input', {
                                bubbles: true,
                                cancelable: true,
                            });
                            arguments[0].dispatchEvent(event);
                        """, message_box)
                        
                        input_success = True
                        print("[INFO] Entered message text with JavaScript")
                    except Exception as e:
                        print(f"[WARNING] JavaScript input method failed: {e}")
                
                # Method 3: ActionChains
                if not input_success:
                    try:
                        print("[INFO] Attempting to enter message with ActionChains...")
                        ActionChains(driver).move_to_element(message_box).click().send_keys(message).perform()
                        time.sleep(2)
                        input_success = True
                        print("[INFO] Entered message text with ActionChains")
                    except Exception as e:
                        print(f"[WARNING] ActionChains input method failed: {e}")
                
                if not input_success:
                    print("[ERROR] All text input methods failed")
                    # Update carry forward messages counter
                    time_tracker.increment_carried_forward_messages(1)
                    
                    # Add this profile to the retry tracking
                    update_retry_tracking(profile_link, increment=True)
                    
                    return False
                
                # Now try to send the message by pressing Enter
                send_success = False
                
                # Method 1: Send keys Enter
                try:
                    print("[INFO] Sending message with Enter key...")
                    message_box.send_keys(Keys.RETURN)
                    time.sleep(8)  # Wait for the message to be sent
                    send_success = True
                    print("[INFO] Message sent with Enter key")
                except Exception as e:
                    print(f"[WARNING] Enter key method failed: {e}")
                
                # Method 2: Try to find and click a send button
                if not send_success:
                    try:
                        print("[INFO] Looking for send button...")
                        send_button = driver.find_element(By.XPATH, "//div[@aria-label='Press enter to send']")
                        send_button.click()
                        time.sleep(8)
                        send_success = True
                        print("[INFO] Message sent by clicking send button")
                    except Exception as e:
                        print(f"[WARNING] Send button click failed: {e}")
                
                # Method 3: JavaScript Enter key
                if not send_success:
                    try:
                        print("[INFO] Simulating Enter key with JavaScript...")
                        driver.execute_script("""
                            var keyEvent = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            });
                            arguments[0].dispatchEvent(keyEvent);
                        """, message_box)
                        time.sleep(8)
                        send_success = True
                        print("[INFO] Message sent with JavaScript Enter key")
                    except Exception as e:
                        print(f"[WARNING] JavaScript Enter key method failed: {e}")
                
                if send_success:
                    print("[INFO] Message sent successfully.")
                    # Track sent messages
                    time_tracker.update_session_metrics("sent_messages")
                    
                    # Close the message box
                    safe_close_message_box(driver)
                    time.sleep(5)
    
                    # Update status to "messaged" since we sent a new message
                    visited_accounts.loc[visited_accounts['link'] == profile_link, 'status'] = 'messaged'
                    visited_accounts.to_csv(visited_accounts_file, index=False)
                    print(f"[INFO] Updated status of {profile_link} to 'messaged' in CSV")
    
                    # No need to add the profile link to visited_accounts_set again
                    # It was already added before navigating to the profile
    
                    # Check for notifications after successfully sending a message
                    print("[INFO] Checking for notifications after sending message...")
                    try:
                        # First check if we're still on Facebook
                        if "facebook.com" not in driver.current_url:
                            print("[INFO] Not on Facebook, navigating back...")
                            driver.get("https://www.facebook.com")
                            time.sleep(3)
                        
                        # Now check for notifications
                        notification_count = check_notifications(driver)
                        if notification_count > 0:
                            print(f"[INFO] Found and processed {notification_count} new notifications")
                        else:
                            print("[INFO] No new notifications found")
                    except Exception as notification_error:
                        print(f"[ERROR] Error checking notifications: {notification_error}")
                    
                    return True
                else:
                    print("[ERROR] Failed to send message with all methods")
                    # Update carry forward messages counter
                    time_tracker.increment_carried_forward_messages(1)
                    
                    # Add this profile to the retry tracking
                    update_retry_tracking(profile_link, increment=True)
                    
                    # Close the message box and return
                    safe_close_message_box(driver)
                    return False

            except Exception as e:
                print(f"[ERROR] Failed to send message: {e}")
                return False
        
        # If we found matching messages, we'll reach here and return True
        # as the message was already sent
        return True
        
    except TimeoutException as e:
        print(f"[ERROR] Timeout while waiting for the message button or input box to be clickable: {e}")
        return False
    except NoSuchElementException as e:
        print(f"[ERROR] Message button or input box element not found: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error while sending the message: {e}")
        return False

def safe_close_message_box(driver):
    """Try the most reliable method to safely close the message box"""
    try:
        # Only use the working method based on logs
        try:
            close_button = driver.find_element(By.XPATH, "//div[@aria-label='Close chat']")
            driver.execute_script("arguments[0].click();", close_button)
            time.sleep(1)
            print("[INFO] Message box closed successfully with JavaScript click.")
            return
        except Exception as e:
            print(f"[WARNING] Failed to close with primary method: {e}")
        
        # Fallback to Escape key if button click fails
        print("[INFO] Trying to close message box with Escape key")
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        print("[INFO] Message box closed with Escape key.")
        
    except Exception as e:
        print(f"[WARNING] Failed to close message box: {e}")
        # Even if we fail to close the box, continue with the flow

def smooth_scroll(driver, scroll_amount):
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(4)

def scroll_to_element_smoothly(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
    time.sleep(4)

def extract_text_from_element(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return element.text
    except (TimeoutException, NoSuchElementException):
        return None

def try_click_messenger_icon(driver, element):
    """
    Specialized function to attempt to click the messenger icon using multiple approaches
    Returns True if successful, False otherwise
    """
    try:
        print("[DEBUG] Trying to locate messenger icon directly from notification element")
        messages_icon = None
        
        # Based on the logs, the other approaches consistently fail 
        # So going directly to the approach that works - finding the parent of notification
        try:
            print("[DEBUG] Finding clickable parent of notification element")
            # Go up from notification element to find clickable parent
            notification_parent = element.find_element(By.XPATH, "./ancestor::div[contains(@role, 'button') or @tabindex='0'][1]")
            if notification_parent:
                messages_icon = notification_parent
                print("[DEBUG] Found clickable parent of notification")
        except Exception as e:
            print(f"[DEBUG] Failed to find parent: {e}")
            # If parent approach fails, try a fallback approach
            try:
                print("[DEBUG] Trying fallback with general messenger icon selector")
                messages_icon = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Messenger" or contains(@aria-label, "message")]'))
                )
                print("[DEBUG] Found message icon using general selector")
            except Exception as e:
                print(f"[DEBUG] General selector failed: {e}")
        
        # If we found the icon, try to click it with multiple methods
        if messages_icon:
            print("[DEBUG] Found message icon, now trying to click")
            clicked = False
            
            # Try multiple clicking methods
            try:
                # First try moving to the element before clicking
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(messages_icon).pause(1).click().perform()
                print("[DEBUG] Clicked messenger icon using ActionChains with pause")
                clicked = True
            except Exception as e:
                print(f"[DEBUG] ActionChains click failed: {e}")
                
                try:
                    # Try plain click
                    messages_icon.click()
                    print("[DEBUG] Clicked messenger icon using regular click")
                    clicked = True
                except Exception as e:
                    print(f"[DEBUG] Regular click failed: {e}")
                    
                    try:
                        # Try JavaScript click
                        driver.execute_script("arguments[0].click();", messages_icon)
                        print("[DEBUG] Clicked messenger icon using simple JavaScript click")
                        clicked = True
                    except Exception as e:
                        print(f"[DEBUG] Simple JavaScript click failed: {e}")
                        
                        try:
                            # Try advanced JavaScript click
                            driver.execute_script("""
                                var element = arguments[0];
                                var event = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                element.dispatchEvent(event);
                            """, messages_icon)
                            print("[DEBUG] Clicked messenger icon using advanced JavaScript event")
                            clicked = True
                        except Exception as e:
                            print(f"[DEBUG] Advanced JavaScript click failed: {e}")
            
            if clicked:
                print("[INFO] Successfully clicked on messages icon.")
                time.sleep(3)  # Wait for messages panel to load
                return True
            else:
                print("[ERROR] Could not click messenger icon with any method")
                return False
        else:
            print("[ERROR] Could not find messages icon with any approach")
            return False
    
    except Exception as e:
        print(f"[ERROR] Error finding or clicking messenger icon: {e}")
        return False

def check_notifications(driver):
    """
    Checks for the presence of new messenger notifications and extracts usernames from unread notifications.
    If notifications are found (count >= 1), clicks on the messages icon and extracts usernames.
    
    Args:
        driver: The Selenium WebDriver instance
        
    Returns:
        int: The number of notifications, or 0 if none found
    """
    try:
        print("[DEBUG] Checking for messenger notifications specifically...")
        
        # Add a delay to ensure notification count appears (3-4 seconds as mentioned)
        print("[INFO] Pausing for 5 seconds to allow notifications to appear...")
        time.sleep(5)
        
        # Try multiple approaches to find the messenger notifications
        messenger_notification_elements = []
        
        # Approach 1: Using the specific mount path with dynamic ID
        try:
            # Specific path using dynamic mount ID pattern
            messenger_elements_1 = driver.find_elements(
                By.XPATH, 
                '//*[starts-with(@id, "mount_0_0")]/div/div[1]/div/div[2]/div[5]/div[1]/div[2]//span[@data-visualcompletion="ignore-dynamic"]//span'
            )
            if messenger_elements_1:
                print(f"[DEBUG] Found {len(messenger_elements_1)} messenger elements using approach 1")
                messenger_notification_elements = messenger_elements_1
        except Exception as e:
            print(f"[DEBUG] Approach 1 failed: {e}")
            
        # Approach 2: Fall back to looking for messenger icon with notification badge if first approach failed
        if not messenger_notification_elements:
            try:
                # Find messenger icon first
                messenger_icon = driver.find_element(
                    By.XPATH,
                    '//div[@aria-label="Messenger" or contains(@aria-label, "message")]'
                )
                if messenger_icon:
                    print("[DEBUG] Found messenger icon, now looking for notification badge")
                    # Look for notification badge within the messenger icon's parent container
                    notification_badges = driver.find_elements(
                        By.XPATH,
                        '//div[@aria-label="Messenger" or contains(@aria-label, "message")]/ancestor::div[1]//span[@data-visualcompletion="ignore-dynamic"]//span'
                    )
                    if notification_badges:
                        print(f"[DEBUG] Found {len(notification_badges)} notification badges using approach 2")
                        messenger_notification_elements = notification_badges
            except Exception as e:
                print(f"[DEBUG] Approach 2 failed: {e}")
                
        # Initialize notification count
        notification_count = 0
        
        # If messenger notifications are found, extract the number
        if messenger_notification_elements:
            print(f"[INFO] Found {len(messenger_notification_elements)} messenger notification element(s)")
            for i, element in enumerate(messenger_notification_elements):
                try:
                    # Get the text which should contain the number of notifications
                    notification_text = element.text.strip()
                    print(f"[INFO] Messenger notification element {i+1} text: '{notification_text}'")
                    
                    # Convert to integer if it's a number
                    if notification_text and notification_text.isdigit():
                        notification_count = int(notification_text)
                        print(f"[INFO] Found {notification_count} messenger notifications.")
                        
                        # We'll update responses_received only after validating the sender later
                        # Removing premature update that was here
                        
                        # If notification count is 1 or more, click on the messages icon
                        if notification_count >= 1:
                            try:
                                print(f"[INFO] Attempting to click messages icon for {notification_count} notification(s)")
                                
                                # Use the specialized function to click the messenger icon
                                if try_click_messenger_icon(driver, element):
                                    # If successfully clicked, check if messages panel opened
                                    try:
                                        messages_panel = driver.find_element(By.XPATH, "//div[@role='dialog']")
                                        if messages_panel:
                                            print("[INFO] Messages panel opened successfully.")
                                            
                                            # Extract usernames from messages
                                            try:
                                                # Wait for message items to load
                                                time.sleep(2)
                                                
                                                # Add a function to detect the specific direct message format
                                                def detect_direct_message_format(text, element=None):
                                                    """Detect Facebook direct message format with better emoji/sticker handling"""
                                                    if not text and not element:
                                                        return None
                                                        
                                                    # Try to get text content using JavaScript if element is provided
                                                    if element:
                                                        try:
                                                            # Get text content including emojis using JavaScript
                                                            js_text = driver.execute_script("""
                                                                function getTextWithEmojis(element) {
                                                                    // Get all text nodes and their content
                                                                    const walker = document.createTreeWalker(
                                                                        element,
                                                                        NodeFilter.SHOW_TEXT,
                                                                        null,
                                                                        false
                                                                    );
                                                                    let text = '';
                                                                    let node;
                                                                    while (node = walker.nextNode()) {
                                                                        text += node.textContent;
                                                                    }
                                                                    return text;
                                                                }
                                                                return getTextWithEmojis(arguments[0]);
                                                            """, element)
                                                            if js_text:
                                                                text = js_text
                                                        except Exception as e:
                                                            print(f"[DEBUG] Error getting text with emojis: {e}")
                                                    
                                                    # Split by newlines and clean up
                                                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                                                    
                                                    # Need at least 3 lines for a valid message (name, message, timestamp)
                                                    if len(lines) < 3:
                                                        return None
                                                    
                                                    try:
                                                        # First line is usually the username
                                                        username = lines[0]
                                                        
                                                        # Find the timestamp line (usually contains time indicators)
                                                        timestamp_line = None
                                                        timestamp_index = -1
                                                        for i, line in enumerate(lines):
                                                            if re.search(r'\b\d+[mhd]\b', line) or '·' in line:
                                                                timestamp_line = line
                                                                timestamp_index = i
                                                                break
                                                        
                                                        if timestamp_index == -1:
                                                            return None
                                                        
                                                        # Everything between username and timestamp is the message
                                                        message_lines = lines[1:timestamp_index]
                                                        message = ' '.join(message_lines)
                                                        
                                                        # Clean up timestamp
                                                        timestamp = timestamp_line.replace('·', '').strip()
                                                        
                                                        # Validate the extracted data
                                                        if (username and len(username) > 1 and 
                                                            message and len(message) > 0 and 
                                                            timestamp):
                                                            return {
                                                                "username": username,
                                                                "message": message,
                                                                "timestamp": timestamp,
                                                                "has_emoji": '😀' in text or '😊' in text or '👍' in text,  # Basic emoji detection
                                                                "is_sticker": 'sticker' in text.lower() or '🎨' in text
                                                            }
                                                    except Exception as e:
                                                        print(f"[DEBUG] Error parsing message format: {e}")
                                                        
                                                    return None
                                                
                                                # New approach to extract all message chunks with better emoji handling
                                                all_message_chunks = []
                                                
                                                # Track how many valid chunks we've processed
                                                valid_chunks_processed = 0
                                                # Maximum chunks to process based on notification count
                                                max_chunks_to_process = notification_count
                                                print(f"[INFO] Will process up to {max_chunks_to_process} valid message chunks based on notification count")
                                                
                                                for item in message_items:
                                                    # Stop if we've processed enough chunks already
                                                    if valid_chunks_processed >= max_chunks_to_process:
                                                        print(f"[INFO] Reached the notification count limit of {max_chunks_to_process} valid chunks. Stopping processing.")
                                                        break
                                                        
                                                    try:
                                                        # Get the raw text and element for better emoji handling
                                                        raw_text = item.text.strip()
                                                        if not raw_text:
                                                            continue
                                                            
                                                        print(f"[DEBUG] Processing message chunk: '\n{raw_text}'")
                                                        
                                                        # Try to detect direct message format with element for better emoji handling
                                                        direct_message = detect_direct_message_format(raw_text, item)
                                                        if direct_message:
                                                            print(f"[DEBUG] Detected message: '{direct_message['username']}' said '{direct_message['message']}' at '{direct_message['timestamp']}'")
                                                            if direct_message['has_emoji']:
                                                                print("[DEBUG] Message contains emojis")
                                                            if direct_message['is_sticker']:
                                                                print("[DEBUG] Message contains stickers")
                                                                
                                                            all_message_chunks.append(direct_message)
                                                            valid_chunks_processed += 1
                                                            print(f"[INFO] Added message from '{direct_message['username']}' to valid messages")
                                                            
                                                            # Stop if we've hit our limit
                                                            if valid_chunks_processed >= max_chunks_to_process:
                                                                print(f"[INFO] Reached notification limit. Breaking early.")
                                                                break
                                                                
                                                            # Skip standard format check for this item
                                                            continue
                                                        
                                                        # Fallback to processing raw text line by line
                                                        lines = raw_text.split('\n')
                                                        
                                                        # Loop through lines to find all instances of "Active now" followed by a username
                                                        for i in range(len(lines) - 1):  # -1 because we need at least one line after
                                                            if lines[i].strip() == "Active now":
                                                                username = lines[i+1].strip()
                                                                # Skip if followed by message about encryption or empty
                                                                if (i+2 < len(lines) and 
                                                                    ("Messages and calls are secured" in lines[i+2] or
                                                                     "You:" in lines[i+2] or not lines[i+2].strip())):
                                                                    print(f"[DEBUG] Skipping system message for '{username}'")
                                                                    continue
                                                                    
                                                                # Check if username is valid
                                                                if username and len(username) > 1:
                                                                    # Extract message if available
                                                                    message = ""
                                                                    if i+2 < len(lines):
                                                                        message = lines[i+2].strip()
                                                                        
                                                                    # Extract timestamp if available
                                                                    timestamp = ""
                                                                    for j in range(i+1, min(i+5, len(lines))):
                                                                        if re.search(r'\b\d+[mhd]\b', lines[j]):
                                                                            timestamp = lines[j].strip()
                                                                            break
                                                                            
                                                                    # Add to chunks if we have valid data
                                                                    if message or timestamp:
                                                                        all_message_chunks.append({
                                                                            "username": username,
                                                                            "message": message,
                                                                            "timestamp": timestamp,
                                                                            "has_emoji": '😀' in raw_text or '😊' in raw_text or '😍' in raw_text,
                                                                            "is_sticker": 'sticker' in raw_text.lower() or '🎨' in raw_text
                                                                        })
                                                                        valid_chunks_processed += 1
                                                                        print(f"[INFO] Added fallback message from '{username}'")
                                                                        
                                                                        if valid_chunks_processed >= max_chunks_to_process:
                                                                            break
                                                    except Exception as e:
                                                        print(f"[WARNING] Error processing message chunk: {e}")
                                                        continue
                                                    except Exception as e:
                                                        print(f"[WARNING] Error processing line: {e}")
                                                        continue
                                                
                                                print(f"[DEBUG] Found {len(all_message_chunks)} valid message chunks")
                                                
                                                # Create a list to store all valid usernames found
                                                usernames_list = []
                                                
                                                # Extract usernames from all valid chunks
                                                for chunk in all_message_chunks:
                                                    username = chunk["username"]
                                                    print(f"[INFO] Extracted valid username: {username}")
                                                    usernames_list.append(username)
                                                    
                                                    # Update the response count for each valid chunk
                                                    # Only count real messages, not system notifications
                                                    if not chunk["message"].startswith("Messages and calls are") and not chunk["message"].startswith("You:"):
                                                        time_tracker.update_session_metrics("responses_received", 1)
                                                        print(f"[INFO] Updated Responses received count for valid message from sender: {username}")
                                                    else:
                                                        print(f"[INFO] Skipped system notification from: {username}")
                                                    print(f"[INFO] Updated Responses received count for sender: {username}")
                                                    
                                                # Extract href links for senders using the specified XPath
                                                sender_links = []
                                                sender_username_to_link_map = {}  # New map to associate usernames with links
                                                try:
                                                    print("[DEBUG] Extracting href links from sender profiles...")
                                                    # Try to find all sender links using the provided XPath
                                                    link_elements = driver.find_elements(
                                                        By.XPATH,
                                                        "//a[@aria-current='false' and contains(concat(' ', normalize-space(@class), ' '), ' x1lliihq ')]"
                                                    )
                                                    
                                                    print(f"[DEBUG] Found {len(link_elements)} potential sender link elements")
                                                    # Extract href attributes from found elements
                                                    for link_element in link_elements:
                                                        try:
                                                            href = link_element.get_attribute('href')
                                                            if href:
                                                                # Try to get the username text from the parent element or child elements
                                                                try:
                                                                    # First try to get text from child spans or divs
                                                                    profile_text = link_element.text.strip()
                                                                    
                                                                    # If that fails, try to find a span with the name inside the element
                                                                    if not profile_text:
                                                                        name_span = link_element.find_element(By.TAG_NAME, "span")
                                                                        if name_span:
                                                                            profile_text = name_span.text.strip()
                                                                    
                                                                    print(f"[DEBUG] Link element with href {href} has text: '{profile_text}'")
                                                                    
                                                                    # If we have a profile text, try to match with usernames
                                                                    if profile_text:
                                                                        # Clean up the profile text to get just the name
                                                                        profile_name = profile_text.split('\n')[0] if '\n' in profile_text else profile_text
                                                                        # Store in our map
                                                                        sender_username_to_link_map[profile_name] = href
                                                                        print(f"[DEBUG] Mapped username '{profile_name}' to link: {href}")
                                                                except Exception as profile_error:
                                                                    print(f"[DEBUG] Could not extract profile text: {profile_error}")
                                                                
                                                                sender_links.append(href)
                                                                print(f"[DEBUG] Extracted sender link: {href}")
                                                        except Exception as link_error:
                                                            print(f"[WARNING] Error extracting href from element: {link_error}")
                                                    
                                                    # If mapping didn't work, try one more approach
                                                    if not sender_username_to_link_map and len(usernames_list) == 1 and sender_links:
                                                        # If we have exactly one username and at least one link, look at conversation elements
                                                        try:
                                                            # Try to find conversation elements with active class
                                                            active_conversations = driver.find_elements(
                                                                By.XPATH,
                                                                "//div[contains(@class, 'x1ey2m1c') and contains(@class, 'xds687c')]//div[contains(@class, 'x78zum5')]"
                                                            )
                                                            
                                                            for conv in active_conversations:
                                                                try:
                                                                    conv_text = conv.text.strip()
                                                                    if usernames_list[0] in conv_text:
                                                                        # Find the link in this conversation element
                                                                        conv_link = conv.find_element(By.TAG_NAME, "a")
                                                                        if conv_link:
                                                                            href = conv_link.get_attribute('href')
                                                                            if href:
                                                                                sender_username_to_link_map[usernames_list[0]] = href
                                                                                print(f"[DEBUG] Found link for active conversation with {usernames_list[0]}: {href}")
                                                                except Exception as conv_error:
                                                                    print(f"[DEBUG] Error processing conversation element: {conv_error}")
                                                        except Exception as active_conv_error:
                                                            print(f"[DEBUG] Error finding active conversations: {active_conv_error}")
                                                            
                                                    # If we still don't have links for all usernames and we have at least one username, try a more direct approach
                                                    if len(usernames_list) > 0 and len(sender_links) > 0:
                                                        # For each username that doesn't have a link yet
                                                        for username in usernames_list:
                                                            if username not in sender_username_to_link_map:
                                                                # Find the element containing this username text
                                                                try:
                                                                    # Try to find an element containing the username
                                                                    username_elements = driver.find_elements(
                                                                        By.XPATH,
                                                                        f"//span[contains(text(), '{username}')]"
                                                                    )
                                                                    
                                                                    for elem in username_elements:
                                                                        try:
                                                                            # Go up to find a clickable parent with href
                                                                            parent = elem
                                                                            for _ in range(5):  # Go up to 5 levels
                                                                                try:
                                                                                    parent = parent.find_element(By.XPATH, "..")
                                                                                    # Check if this parent has an 'a' tag
                                                                                    link_elems = parent.find_elements(By.TAG_NAME, "a")
                                                                                    if link_elems:
                                                                                        href = link_elems[0].get_attribute('href')
                                                                                        if href:
                                                                                            sender_username_to_link_map[username] = href
                                                                                            print(f"[DEBUG] Found link by DOM traversal for {username}: {href}")
                                                                                            break
                                                                                except:
                                                                                    break
                                                                        except Exception as e:
                                                                            print(f"[DEBUG] Error traversing DOM for {username}: {e}")
                                                                
                                                                except Exception as username_search_error:
                                                                    print(f"[DEBUG] Error searching for username element: {username_search_error}")
                                                    
                                                except Exception as link_search_error:
                                                    print(f"[ERROR] Failed to extract sender links: {link_search_error}")
                                                
                                                # Save usernames to CSV if we found any
                                                if usernames_list:
                                                    try:
                                                        # Determine the path for the csv file in the main directory
                                                        unread_users_csv = os.path.join(os.getcwd(), "unreadUsers.csv")
                                                        
                                                        # Check if file exists and create it with headers if not
                                                        if not os.path.exists(unread_users_csv):
                                                            with open(unread_users_csv, 'w', newline='', encoding='utf-8') as f:
                                                                writer = csv.writer(f)
                                                                writer.writerow(['username', 'timestamp', 'link'])
                                                                print(f"[INFO] Created new unreadUsers.csv file with headers")
                                                        
                                                        # Read existing entries to avoid duplicates
                                                        existing_usernames = set()
                                                        try:
                                                            with open(unread_users_csv, 'r', encoding='utf-8') as f:
                                                                reader = csv.reader(f)
                                                                header = next(reader, None)  # Skip header
                                                                
                                                                # Check if the 'link' column exists in the header
                                                                has_link_column = header and 'link' in header
                                                                
                                                                for row in reader:
                                                                    if row:  # Ensure row is not empty
                                                                        existing_usernames.add(row[0].lower())  # Add lowercase for case-insensitive comparison
                                                        except Exception as read_error:
                                                            print(f"[WARNING] Error reading existing unreadUsers.csv: {read_error}")
                                                            
                                                        # Check if we need to update the header to include the link column
                                                        if os.path.exists(unread_users_csv):
                                                            try:
                                                                # Read the existing file to check columns
                                                                with open(unread_users_csv, 'r', encoding='utf-8') as f:
                                                                    reader = csv.reader(f)
                                                                    header = next(reader, None)  # Get header row
                                                                
                                                                # If header doesn't include 'link', update the file
                                                                if header and 'link' not in header:
                                                                    # Read all existing data
                                                                    with open(unread_users_csv, 'r', encoding='utf-8') as f:
                                                                        reader = csv.reader(f)
                                                                        header = next(reader, None)  # Skip header
                                                                        existing_data = list(reader)
                                                                    
                                                                    # Write back with new header and existing data plus empty link column
                                                                    with open(unread_users_csv, 'w', newline='', encoding='utf-8') as f:
                                                                        writer = csv.writer(f)
                                                                        writer.writerow(['username', 'timestamp', 'link'])  # New header
                                                                        for row in existing_data:
                                                                            writer.writerow(row + [''])  # Add empty link field
                                                                    
                                                                    print("[INFO] Updated unreadUsers.csv with new 'link' column")
                                                            except Exception as header_update_error:
                                                                print(f"[WARNING] Error updating header in unreadUsers.csv: {header_update_error}")
                                                        
                                                        # Append new entries
                                                        with open(unread_users_csv, 'a', newline='', encoding='utf-8') as f:
                                                            writer = csv.writer(f)
                                                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                            
                                                            new_count = 0
                                                            for i, username in enumerate(usernames_list):
                                                                # Skip if already in the file (case-insensitive)
                                                                if username.lower() in existing_usernames:
                                                                    print(f"[INFO] Skipping duplicate username: {username}")
                                                                    continue
                                                                
                                                                # Get link for this user if available
                                                                user_link = ''
                                                                # First check if we have a direct mapping
                                                                if username in sender_username_to_link_map:
                                                                    user_link = sender_username_to_link_map[username]
                                                                    print(f"[INFO] Found matched link for {username}: {user_link}")
                                                                # Fallback to index-based matching if we have no mapping
                                                                elif i < len(sender_links):
                                                                    user_link = sender_links[i]
                                                                    print(f"[INFO] Using fallback link for {username}: {user_link}")
                                                                
                                                                writer.writerow([username, now, user_link])
                                                                print(f"[INFO] Appended username to unreadUsers.csv: {username} with link: {user_link}")
                                                                new_count += 1
                                                                existing_usernames.add(username.lower())  # Add to set to avoid duplicates within this batch
                                                            
                                                            print(f"[INFO] Added {new_count} new unread users to CSV")
                                                            
                                                    except Exception as csv_error:
                                                        print(f"[ERROR] Failed to save usernames to CSV: {csv_error}")
                                            
                                            except Exception as extraction_error:
                                                print(f"[ERROR] Failed to extract usernames from messages: {extraction_error}")
                                                traceback.print_exc()
                                    except Exception:
                                        print("[WARNING] Could not verify if messages panel opened.")
                            except Exception as click_error:
                                print(f"[ERROR] Failed to click on messages icon: {click_error}")
                        
                        return notification_count
                except StaleElementReferenceException:
                    print(f"[WARNING] Stale element reference for notification element {i+1}")
                    continue
                except Exception as e:
                    print(f"[ERROR] Error parsing notification count: {e}")
        
        print("[INFO] No new messenger notifications found.")
        return notification_count
        
    except Exception as e:
        print(f"[ERROR] Error checking messenger notifications: {e}")
        return 0

def check_overview_section(driver, univer, visited_accounts_file, profile_link, username, password, matched_university):
    global current_logged_in_username
    
    try:
        # Initialize variables
        # Already have matched_university from the group
        group_university = matched_university  # Store the group's matched university name
        profile_university = ""  # Will store university detected directly from profile
        
        # We've already added the profile to visited_accounts_set before navigating
        # So we can skip this check now
        about_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='About']"))
        )
        driver.execute_script("arguments[0].click();", about_button)
        time.sleep(7)

        studies_xpath = "//div[contains(@class, 'x13faqbe') and contains(@class, 'x78zum5') and contains(@class, 'xdt5ytf')]//span[contains(text(), 'Studies')]"
        studies_text = extract_text_from_element(driver, studies_xpath)

        # Extract the user's name
        user_name = extract_text_from_element(driver, "//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x14qwyeo xw06pyt x579bpy xjkpybl x1xlr1w8 xzsf02u x1yc453h']")

        status = "unmatched"
        if studies_text and studies_text.strip():
            # Print the full studies text for debugging
            print(f"[DEBUG] Found studies text: '{studies_text}'")
            
            # Convert to lowercase for case-insensitive matching
            studies_text_lower = studies_text.lower()
            
            # Create a filtered university list excluding the column name
            filtered_unis = []
            for _, row in univer.iterrows():
                university_name = row['university']
                # Skip if the university name is just the column name "university"
                if university_name.lower() == "university":
                    print(f"[DEBUG] Skipping column header '{university_name}' in study field matching")
                    continue
                filtered_unis.append(university_name)
            
            for university_name in filtered_unis:
                university_lower = university_name.lower()
                
                # Only match if the university name is substantial (at least 5 chars)
                # and represents at least 60% of the complete university name
                min_match_length = max(5, len(university_name) * 0.6)
                
                if len(university_name) >= min_match_length and university_lower in studies_text_lower:
                    status = "pending"
                    # Track matched profiles
                    time_tracker.update_session_metrics("profiles_matched")
                    # Also increment the carry forward messages count for this match
                    time_tracker.increment_carried_forward_messages()
                    print(f"[INFO] University match found: '{university_name}' in studies text: '{studies_text}'")
                    profile_university = university_name  # Store the matched university name from studies
                    break

        # Use the university detected directly from profile if found, otherwise use the group's university
        final_university = profile_university if profile_university else group_university
        if profile_university:
            print(f"[INFO] Using university detected from profile studies: '{profile_university}'")
        elif group_university:
            print(f"[INFO] Using university detected from group: '{group_university}'")
        
        # Include the global username in the new entry for "Search by" column
        search_username = current_logged_in_username if current_logged_in_username else username
        new_entry = pd.DataFrame({
            "link": [profile_link], 
            "name": [user_name], 
            "timestamp": [pd.Timestamp.now()], 
            "status": [status], 
            "searched_by": [search_username],
            "university": [final_university if status == "pending" else ""]
        })
        
        # Use the safe CSV write function to avoid duplicates
        safe_write_to_csv(new_entry, visited_accounts_file)

        # No need to add to visited_accounts_set here since we already did before navigation

        # Process messages after checking each profile
        process_pending_messages(username, password)
        
        return status

    except Exception as e:
        print(f"[ERROR] Error in check_overview_section or locked profile: {e}")
        # Profile is already in visited_accounts_set, just record the error in the CSV
        user_name = "Unknown" # Default name for locked profiles
        try:
            # Try to get the name if possible
            user_name = extract_text_from_element(driver, "//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x14qwyeo xw06pyt x579bpy xjkpybl x1xlr1w8 xzsf02u x1yc453h']")
        except:
            pass
            
        # Add to visited accounts with error status and include the global username
        search_username = current_logged_in_username if current_logged_in_username else username
        new_entry = pd.DataFrame({
            "link": [profile_link], 
            "name": [user_name], 
            "timestamp": [pd.Timestamp.now()], 
            "status": ["locked"], 
            "searched_by": [search_username],
            "university": [matched_university]
        })
        
        # Use the safe CSV write function to avoid duplicates
        safe_write_to_csv(new_entry, visited_accounts_file)
        
        return "error"

def process_pending_messages(username, password):
    global driver, retry_tracking, retry_tracking_file
    
    # Add a validation check at the beginning
    if not is_driver_session_valid(driver):
        print("[INFO] Driver session invalid at start of process_pending_messages, reinitializing...")
        driver = init_driver()
        if not login_if_needed(driver, username, password):
            print("[ERROR] Failed to login with reinitialized driver")
            return False
        
    visited_accounts_file = "visited_accounts.csv"
    retry_tracking_file = "pending_retry_tracking.csv"
    
    # Check if the file exists and has the correct headers
    if not os.path.exists(visited_accounts_file):
        print("[INFO] Initializing visited_accounts.csv with correct headers.")
        # Create the file with the correct headers
        visited_accounts = pd.DataFrame(columns=['link', 'name', 'timestamp', 'status', 'searched_by', 'university'])
        visited_accounts.to_csv(visited_accounts_file, index=False)
    else:
        visited_accounts = pd.read_csv(visited_accounts_file)
        # Check if the required columns are present
        if not set(['link', 'name', 'timestamp', 'status', 'searched_by', 'university']).issubset(visited_accounts.columns):
            print("[INFO] Reinitializing visited_accounts.csv with correct headers.")
            visited_accounts = pd.DataFrame(columns=['link', 'name', 'timestamp', 'status', 'searched_by', 'university'])
            visited_accounts.to_csv(visited_accounts_file, index=False)

    # Initialize or load retry tracking file
    if not os.path.exists(retry_tracking_file):
        print("[INFO] Initializing retry tracking file.")
        retry_tracking = pd.DataFrame(columns=['link', 'retry_count', 'last_retry_timestamp'])
        retry_tracking.to_csv(retry_tracking_file, index=False)
    else:
        retry_tracking = pd.read_csv(retry_tracking_file)
        # Check if the required columns are present
        if not set(['link', 'retry_count', 'last_retry_timestamp']).issubset(retry_tracking.columns):
            print("[INFO] Reinitializing retry tracking file with correct headers.")
            retry_tracking = pd.DataFrame(columns=['link', 'retry_count', 'last_retry_timestamp'])
            retry_tracking.to_csv(retry_tracking_file, index=False)

    # Get accounts that are pending
    pending_accounts = visited_accounts[visited_accounts['status'] == 'pending']
    print(f"[INFO] Found {len(pending_accounts)} pending accounts.")

    # Get the last messaged timestamp
    messaged_accounts = visited_accounts[visited_accounts['status'] == 'messaged']
    if not messaged_accounts.empty:
        last_messaged_timestamp = pd.to_datetime(messaged_accounts['timestamp']).max()
    else:
        last_messaged_timestamp = None

    current_time = pd.Timestamp.now()

    # Check if 30 minutes have passed since the last messaged user
    if last_messaged_timestamp and (current_time - last_messaged_timestamp) < timedelta(minutes=30):
        print("[INFO] Limiting messages.")
        return

    if not pending_accounts.empty:
        # Sort pending accounts: first by retry_count (ascending), then by new profiles
        if not retry_tracking.empty:
            # Merge the pending accounts with retry tracking to get retry counts
            pending_with_retries = pd.merge(
                pending_accounts, 
                retry_tracking, 
                on='link', 
                how='left'
            )
            
            # Fill NaN retry counts with 0 (for profiles never retried)
            pending_with_retries['retry_count'] = pending_with_retries['retry_count'].fillna(0)
            
            # Convert to int
            pending_with_retries['retry_count'] = pending_with_retries['retry_count'].astype(int)
            
            # Sort by retry count (ascending), then by timestamp (oldest first)
            pending_with_retries = pending_with_retries.sort_values(
                by=['retry_count', 'timestamp']
            )
            
            # Use this sorted list instead of the original pending_accounts
            pending_accounts = pending_with_retries[pending_accounts.columns]
        
        # Store the current URL before processing messages
        current_url = driver.current_url if driver is not None else None
        
        if login_if_needed(driver, username, password):
            main_window_handle = driver.current_window_handle if driver is not None else None  # Store the main window handle
            processed_any_profile = False
            
            for index, row in pending_accounts.iterrows():
                profile_link = row['link']
                
                # Check if this profile has been retried too many times (skip after 2 retries)
                profile_retry_count = 0
                if not retry_tracking.empty:
                    profile_retry_info = retry_tracking[retry_tracking['link'] == profile_link]
                    if not profile_retry_info.empty:
                        profile_retry_count = int(profile_retry_info['retry_count'].iloc[0])
                
                if profile_retry_count >= 2:
                    print(f"[INFO] Skipping profile that failed twice: {profile_link}")
                    # Update status to 'retry_failed' to stop retrying
                    visited_accounts.loc[visited_accounts['link'] == profile_link, 'status'] = 'retry_failed'
                    visited_accounts.to_csv(visited_accounts_file, index=False)
                    continue
                
                # Get the status with a try-except to avoid linter errors
                try:
                    matching_rows = visited_accounts[visited_accounts['link'] == profile_link]
                    if not matching_rows.empty:
                        current_status = matching_rows['status'].iloc[0]
                    else:
                        current_status = "unknown"
                except Exception as e:
                    print(f"[ERROR] Error getting status for {profile_link}: {e}")
                    current_status = "unknown"
                
                # Only skip if the status is not 'pending'
                if current_status != 'pending':
                    print(f"[INFO] Skipping profile with status '{current_status}': {profile_link}")
                    continue

                print(f"[INFO] Processing pending profile: {profile_link} (retry count: {profile_retry_count})")

                try:
                    # Modified approach: Instead of opening in a new tab, navigate directly to the profile
                    # This is more reliable than opening new tabs which can cause session issues
                    print(f"[INFO] Navigating directly to profile: {profile_link}")
                    if driver is not None:
                        # Store current URL to return to later
                        original_url = driver.current_url
                        
                        # Navigate directly to the profile
                        driver.get(profile_link)
                        time.sleep(10)  # Give extra time for profile to load
                        
                        # Ensure the page is fully loaded
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        print("[INFO] Profile page loaded successfully.")
                    else:
                        print("[ERROR] Driver is None, cannot navigate to profile link.")
                        continue

                    # Check if profile is deleted or unavailable
                    try:
                        content_not_found = driver.find_elements(By.XPATH, "//div[contains(text(), \"This content isn't available\")]")
                        if content_not_found:
                            print("[INFO] Profile deleted or unavailable.")
                            # Track deleted users
                            time_tracker.update_session_metrics("deleted_users")
                            # Update the status
                            visited_accounts.loc[visited_accounts['link'] == profile_link, 'status'] = 'deleted'
                            visited_accounts.to_csv(visited_accounts_file, index=False)
                            # Navigate back to original URL
                            driver.get(original_url)
                            time.sleep(5)
                            continue
                    except Exception as e:
                        print(f"[ERROR] Error checking if profile is deleted: {e}")

                    # Check for message responses (if this user has messaged you back)
                    try:
                        message_responses = driver.find_elements(By.XPATH, "//span[contains(text(), 'Message') or contains(text(), 'Messenger')]")
                        if not message_responses:
                            print("[INFO] User has responded to a message.")
                            # Track responses received
                            time_tracker.update_session_metrics("responses_received")
                    except Exception as e:
                        print(f"[ERROR] Error checking for message responses: {e}")

                    # Step 4: Send the message - use personalized message with name and university
                    # Get name and university from the current profile data
                    user_name = row['name'] if not pd.isna(row['name']) else ""
                    user_university = row['university'] if not pd.isna(row['university']) else ""
                    
                    # Create personalized message using name and university
                    if user_name and user_university:
                        message_text = f"Hi {user_name}, are you a student of {user_university}?"
                    elif user_name:
                        message_text = f"Hi {user_name}, how are you?"
                    elif user_university:
                        message_text = f"Hi, are you a student of {user_university}?"
                    else:
                        message_text = "Hi, how are you?"
                        
                    print(f"[DEBUG] Attempting to send message: '{message_text}'")
                    send_success = send_message(driver, message_text, visited_accounts, visited_accounts_file, profile_link)
                    
                    # When a message is sent to a pending profile, decrement the carry forward messages count
                    # This ensures the carry forward messages accurately reflects pending messages only
                    if send_success and time_tracker.start_time is not None:
                        time_tracker.increment_carried_forward_messages(-1)  # Decrement by 1

                    # Step 5: No need to close tab since we navigated directly
                    
                    # Step 6: Update the timestamp only, don't override the status
                    visited_accounts.loc[visited_accounts['link'] == profile_link, 'timestamp'] = pd.Timestamp.now()
                    visited_accounts.to_csv(visited_accounts_file, index=False)

                    # Step 7: Navigate back to the original URL
                    if driver is not None and original_url:
                        driver.get(original_url)
                        time.sleep(5)
                        print("[INFO] Navigated back to original page.")
                    else:
                        print("[ERROR] Cannot navigate back - driver or original_url is None.")

                    # Step 8: Update summary table after sending a message
                    # Only update if we have an active session
                    if time_tracker.start_time is not None:
                        time_tracker.log_execution_time(is_final=False)

                    # Remove from retry tracking if message sending was successful
                    if send_success:
                        update_retry_tracking(profile_link, increment=False)
                        retry_tracking.to_csv(retry_tracking_file, index=False)
                    
                    processed_any_profile = True
                    break  # Process only one pending profile per run

                except Exception as e:
                    print(f"[ERROR] Exception in process_pending_messages: {e}")
                    # Check if this is an invalid session error
                    if "invalid session id" in str(e):
                        print("[INFO] Invalid session detected, reinitializing driver...")
                        try:
                            # Quit the old driver if it exists
                            if driver is not None:
                                try:
                                    driver.quit()
                                except:
                                    pass  # Ignore errors when quitting an already invalid driver
                            
                            # Reinitialize the driver
                            driver = init_driver()
                            if login_if_needed(driver, username, password):
                                print("[INFO] Successfully reinitialized driver and logged in")
                                # Update the main window handle
                                main_window_handle = driver.current_window_handle
                                # Still increment retry count for this profile
                            else:
                                print("[ERROR] Failed to reinitialize driver and login")
                                # Continue with normal retry handling
                        except Exception as reinit_error:
                            print(f"[ERROR] Failed to reinitialize driver: {reinit_error}")
                    
                    # Increment retry count for this profile (regardless of error type)
                    update_retry_tracking(profile_link, increment=True)
                    
                    # Save updated retry tracking
                    retry_tracking.to_csv(retry_tracking_file, index=False)
                    
                    # Try to restore the original page context
                    try:
                        if "invalid session id" not in str(e) and driver is not None and main_window_handle is not None:
                            driver.switch_to.window(str(main_window_handle))
                            if driver.current_url != current_url and current_url is not None:
                                driver.get(current_url)
                                time.sleep(5)
                                print("[INFO] Restored original page context after error.")
                    except Exception as restore_error:
                        print(f"[ERROR] Failed to restore page context: {restore_error}")
                        # Check if this is an invalid session error that happened during restoration
                        if "invalid session id" in str(restore_error):
                            print("[INFO] Invalid session detected during restoration, reinitializing driver...")
                            try:
                                if driver is not None:
                                    try:
                                        driver.quit()
                                    except:
                                        pass
                                driver = init_driver()
                                if login_if_needed(driver, username, password):
                                    print("[INFO] Successfully reinitialized driver and logged in after restoration failure")
                                    main_window_handle = driver.current_window_handle
                            except Exception as second_reinit_error:
                                print(f"[ERROR] Failed to reinitialize driver after restoration failure: {second_reinit_error}")
                    
                    # Process the next profile only if no profile has been processed successfully yet
                    if not processed_any_profile:
                        print(f"[INFO] Profile {profile_link} has failed. Moving to next profile.")
                        continue
                    else:
                        print("[INFO] Already processed a profile successfully, stopping now.")
                        break

def save_unvisited_profiles(profile_links):
    """Save unvisited profiles to a CSV file for future sessions and return the count of saved profiles"""
    unvisited_file = "unvisited_profiles.csv"
    
    try:
        # Create a DataFrame for the new profiles
        new_profiles_df = pd.DataFrame({"link": profile_links, "timestamp": [pd.Timestamp.now()] * len(profile_links)})
        
        # If the file exists, read it and concatenate with new profiles
        if os.path.exists(unvisited_file):
            existing_profiles = pd.read_csv(unvisited_file)
            # Combine existing and new profiles
            combined_profiles = pd.concat([existing_profiles, new_profiles_df])
            # Remove duplicates
            combined_profiles = combined_profiles.drop_duplicates(subset=['link'])
            # Remove any profiles that are already in visited_accounts_set
            combined_profiles = combined_profiles[~combined_profiles['link'].isin(visited_accounts_set)]
            # Count how many NEW unique profiles were added
            new_profile_count = len(combined_profiles) - len(existing_profiles)
            new_profile_count = max(0, new_profile_count)  # Ensure it's not negative
            # Save the updated file
            combined_profiles.to_csv(unvisited_file, index=False)
            print(f"[INFO] Saved {new_profile_count} new unvisited profiles (total: {len(combined_profiles)})")
            return new_profile_count
        else:
            # Create new file - all profiles are new
            new_filtered_df = new_profiles_df[~new_profiles_df['link'].isin(visited_accounts_set)]
            new_filtered_df.to_csv(unvisited_file, index=False)
            print(f"[INFO] Created new unvisited profiles file with {len(new_filtered_df)} profiles")
            return len(new_filtered_df)
    except Exception as e:
        print(f"[ERROR] Failed to save unvisited profiles: {e}")
        return 0

def safe_write_to_csv(new_entry, csv_file):
    """
    Safely write new entries to CSV without creating duplicates
    Args:
        new_entry: pandas DataFrame with new data
        csv_file: path to the CSV file
    """
    try:
        # If file exists, read it and remove duplicates
        if os.path.exists(csv_file):
            existing_df = pd.read_csv(csv_file)
            
            # Check if the required columns exist in the existing dataframe
            required_columns = ['link', 'name', 'timestamp', 'status', 'searched_by', 'university']
            for col in required_columns:
                if col not in existing_df.columns:
                    # Add the missing column with default values
                    if col == 'searched_by':
                        existing_df[col] = 'Facebook'  # Default value for searched_by
                    else:
                        existing_df[col] = ''  # Empty string for other columns
                    print(f"[INFO] Added missing column '{col}' to {csv_file}")
            
            # Make sure all required columns exist in the new entry
            for col in required_columns:
                if col not in new_entry.columns:
                    if col == 'searched_by':
                        new_entry[col] = 'Facebook'  # Default value
                    else:
                        new_entry[col] = ''  # Empty string for other columns
            
            # Check if the entry already exists (by link)
            link = new_entry['link'].iloc[0]
            if link in existing_df['link'].values:
                # Update the existing entry with the new timestamp
                existing_df.loc[existing_df['link'] == link, 'timestamp'] = new_entry['timestamp'].iloc[0]
                # If status is provided and not empty, update it too
                if 'status' in new_entry.columns and not pd.isna(new_entry['status'].iloc[0]):
                    existing_df.loc[existing_df['link'] == link, 'status'] = new_entry['status'].iloc[0]
                # If searched_by is provided and not empty, update it too
                if 'searched_by' in new_entry.columns and not pd.isna(new_entry['searched_by'].iloc[0]):
                    existing_df.loc[existing_df['link'] == link, 'searched_by'] = new_entry['searched_by'].iloc[0]
                # If university is provided and not empty, update it too
                if 'university' in new_entry.columns and not pd.isna(new_entry['university'].iloc[0]) and new_entry['university'].iloc[0] != '':
                    existing_df.loc[existing_df['link'] == link, 'university'] = new_entry['university'].iloc[0]
                # Save the updated DataFrame
                existing_df.to_csv(csv_file, index=False)
                print(f"[INFO] Updated existing entry for {link} in CSV")
            else:
                # Append new entry 
                combined_df = pd.concat([existing_df, new_entry], ignore_index=True)
                # Save the updated DataFrame
                combined_df.to_csv(csv_file, index=False)
                print(f"[INFO] Added new entry for {link} to CSV")
        else:
            # Create new file with header - ensure all required columns exist
            required_columns = ['link', 'name', 'timestamp', 'status', 'searched_by', 'university']
            for col in required_columns:
                if col not in new_entry.columns:
                    if col == 'searched_by':
                        new_entry[col] = 'Facebook'  # Default value
                    else:
                        new_entry[col] = ''  # Empty string for other columns
            
            new_entry.to_csv(csv_file, index=False)
            print(f"[INFO] Created new CSV file with first entry: {new_entry['link'].iloc[0]}")
    except Exception as e:
        print(f"[ERROR] Error writing to CSV: {e}")
        # Fallback to direct append in case of error
        try:
            # Make sure all required columns exist in the new entry for the fallback
            required_columns = ['link', 'name', 'timestamp', 'status', 'searched_by', 'university']
            for col in required_columns:
                if col not in new_entry.columns:
                    if col == 'searched_by':
                        new_entry[col] = 'Facebook'  # Default value
                    else:
                        new_entry[col] = ''  # Empty string for other columns
            
            # Create file with headers if it doesn't exist
            write_header = not os.path.exists(csv_file)
            new_entry.to_csv(csv_file, mode='a', header=write_header, index=False)
            print("[WARNING] Used fallback CSV write method")
        except Exception as e2:
            print(f"[ERROR] Fallback CSV write failed too: {e2}")

# Add this new function after the init_driver function
def is_driver_session_valid(driver):
    """Check if the WebDriver session is still valid"""
    if driver is None:
        return False
    try:
        # A simple operation to test if the session is valid
        driver.current_url
        return True
    except WebDriverException:
        print("[ERROR] WebDriver session is invalid")
        return False

# Track number of Ctrl+C attempts and the exit thread
ctrl_c_count = 0
exit_thread = None
CTRL_C_PRESSED = False  # Global flag to detect Ctrl+C across threads

# Create a panic file to detect if we're already in the process of shutting down
def create_panic_file():
    try:
        with open("TERMINATING.lock", "w") as f:
            import time
            f.write(f"Termination started at {time.time()}")
    except:
        pass

def check_panic_file():
    return os.path.exists("TERMINATING.lock")

def remove_panic_file():
    try:
        if os.path.exists("TERMINATING.lock"):
            os.remove("TERMINATING.lock")
    except:
        pass

# Add proper signal handler for SIGINT (Ctrl+C)
def signal_handler(sig, frame):
    global CTRL_C_PRESSED, driver  # Need global when we modify module variables
    CTRL_C_PRESSED = True  # Set the global flag
    
    print("\n[CRITICAL] *** CTRL+C DETECTED - FORCE TERMINATING PYTHON PROCESS ***")
    
    # Try to quit the driver if it exists
    try:
        if driver is not None:
            driver.quit()
            print("[INFO] Successfully closed browser driver")
            os._exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to close driver: {e}")
    
    # Directly call os._exit to terminate immediately
    print("[CRITICAL] Force terminating now!")
    os._exit(1)  # Use the most aggressive exit possible - DO NOT DEFER OR DELAY THIS CALL

# Add a special watchdog thread that will monitor for Ctrl+C and force terminate if needed
def watchdog_thread():
    """A simplified watchdog that monitors for Ctrl+C flag and forces termination if main thread is stuck"""
    import time
    import os
    
    while True:
        try:
            # Sleep for a short interval
            time.sleep(1)
            
            # Check if Ctrl+C has been pressed
            if CTRL_C_PRESSED:
                print("\n[WATCHDOG] Ctrl+C detected by watchdog! Forcing termination...")
                # Just exit directly - don't try to create files or run subprocesses
                os._exit(1)
        except:
            # Ignore any errors in the watchdog
            pass

# Helper function to initialize and update retry tracking
def update_retry_tracking(profile_link, increment=True):
    """
    Initialize retry tracking if needed and update the retry count for a profile.
    
    Args:
        profile_link: The link to the profile to update
        increment: If True, increment the retry count; if False, remove the profile from tracking
        
    Returns:
        True if successful, False otherwise
    """
    global retry_tracking, retry_tracking_file
    
    try:
        # Initialize retry_tracking if it's None
        if retry_tracking is None:
            if os.path.exists(retry_tracking_file):
                retry_tracking = pd.read_csv(retry_tracking_file)
            else:
                retry_tracking = pd.DataFrame(columns=['link', 'retry_count', 'last_retry_timestamp'])
                retry_tracking.to_csv(retry_tracking_file, index=False)
                print(f"[INFO] Created new {retry_tracking_file}")
        
        # Check if profile is already in retry tracking
        if profile_link in retry_tracking['link'].values:
            if increment:
                # Increment the retry count
                profile_index = retry_tracking[retry_tracking['link'] == profile_link].index[0]
                current_count = int(retry_tracking.at[profile_index, 'retry_count'])
                retry_tracking.at[profile_index, 'retry_count'] = current_count + 1
                # Update the timestamp
                retry_tracking.at[profile_index, 'last_retry_timestamp'] = pd.Timestamp.now()
                print(f"[INFO] Incremented retry count for {profile_link} to {current_count + 1}")
            else:
                # Remove the profile from tracking since it was successful
                retry_tracking = retry_tracking[retry_tracking['link'] != profile_link]
                print(f"[INFO] Removed {profile_link} from retry tracking (successful send)")
        else:
            # Only add new entry if we're incrementing (failure case)
            if increment:
                # Add new entry
                new_row = pd.DataFrame({
                    'link': [profile_link],
                    'retry_count': [1],  # Start with 1 on first failure
                    'last_retry_timestamp': [pd.Timestamp.now()]
                })
                retry_tracking = pd.concat([retry_tracking, new_row], ignore_index=True)
                print(f"[INFO] Added new profile {profile_link} to retry tracking with count 1")
        
        # Save updated retry tracking
        retry_tracking.to_csv(retry_tracking_file, index=False)
        print(f"[INFO] Successfully updated retry tracking for {profile_link}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update retry tracking: {e}")
        return False

if __name__ == "__main__":
    try:
        # Remove any existing panic file at startup
        remove_panic_file()
        
        # Register signal handler for Ctrl+C
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        print("[INFO] Registered signal handler for Ctrl+C.")
        
        # Start the watchdog thread
        watchdog = threading.Thread(target=watchdog_thread, daemon=True)
        watchdog.start()
        print("[INFO] Started watchdog thread to monitor for Ctrl+C.")

        # Create the visited_accounts.csv with proper headers if it doesn't exist
        if not os.path.exists("visited_accounts.csv"):
            visited_accounts = pd.DataFrame(columns=['link', 'name', 'timestamp', 'status', 'searched_by', 'university'])
            visited_accounts.to_csv("visited_accounts.csv", index=False)
            print("[INFO] Created visited_accounts.csv with proper headers")
        else:
            # Check if the file has all required columns
            try:
                visited_accounts = pd.read_csv("visited_accounts.csv")
                required_columns = ['link', 'name', 'timestamp', 'status', 'searched_by', 'university']
                
                # Add any missing columns
                missing_columns = False
                for col in required_columns:
                    if col not in visited_accounts.columns:
                        if col == 'searched_by':
                            visited_accounts[col] = 'Facebook'  # Default value
                        else:
                            visited_accounts[col] = ''  # Empty string for other columns
                        missing_columns = True
                        print(f"[INFO] Added missing column '{col}' to visited_accounts.csv")
                
                # Save the file if columns were added
                if missing_columns:
                    visited_accounts.to_csv("visited_accounts.csv", index=False)
                    print("[INFO] Updated visited_accounts.csv with new required columns")
            except Exception as e:
                print(f"[ERROR] Error checking visited_accounts.csv: {e}")
        
        # Load account credentials
        accounts = pd.read_csv("account.csv")
        
        # Get university data - check environment variable first, then common paths
        university_file = os.environ.get('UNIVERSITY_FILE')
        if university_file and os.path.exists(university_file):
            univer = pd.read_csv(university_file)
            print(f"[INFO] Loaded university file from environment variable: {university_file}")
        else:
            # Look in standard paths created by the web application
            university_paths = [
                "main/staticfiles/sessions/uniall.csv",
                "staticfiles/sessions/uniall.csv",
                "staticfiles/uniall.csv"
            ]
            
            univer = None
            for path in university_paths:
                if os.path.exists(path):
                    univer = pd.read_csv(path)
                    print(f"[INFO] Loaded university file from: {path}")
                    break
            
            # If no file found in standard paths, look for any university CSV file
            if univer is None:
                try:
                    uni_files = [f for f in os.listdir("staticfiles") if f.endswith(".csv") and "uni" in f.lower()]
                    if uni_files:
                        univer = pd.read_csv(f"staticfiles/{uni_files[0]}")
                        print(f"[INFO] Loaded university file from: staticfiles/{uni_files[0]}")
                except Exception as e:
                    print(f"[WARNING] Error searching for university files: {e}")
            
            # If still no file found, create a default list
            if univer is None:
                print("[WARNING] No university file found. Creating a default university list.")
                univer = pd.DataFrame({"university": ["University of Oxford", "University of Cambridge", 
                                                    "Imperial College London", "University of Edinburgh"]})
                # Save it for future use
                os.makedirs("main/staticfiles/sessions", exist_ok=True)
                univer.to_csv("main/staticfiles/sessions/uniall.csv", index=False)
                print("[INFO] Created default university file at main/staticfiles/sessions/uniall.csv")

        # Start global session log for processing pending messages
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        pending_log_file = os.path.join(log_dir, f"pending_processing_{timestamp}.log")
        print(f"[INFO] Starting pending messages processing log: {pending_log_file}")
        
        # Create a log file for pending messages processing
        pending_log = open(pending_log_file, 'w', encoding='utf-8')
        original_stdout = sys.stdout
        sys.stdout = time_tracker.TeeOutput(pending_log, original_stdout)
        
        print(f"\n{'='*80}\nPENDING MESSAGES PROCESSING STARTED: {timestamp}\n{'='*80}\n")

        # Process pending messages using a separate driver instance without metrics tracking
        driver = init_driver()
        try:
            max_retry_attempts = 5
            for i, row in accounts.iterrows():
                uname = row['username']
                pas = row['password']
                retry_count = 0
                success = False
                
                # Implement retry loop with a limit
                while not success and retry_count < max_retry_attempts:
                    try:
                        if login_if_needed(driver, uname, pas):
                            process_pending_messages(uname, pas)
                            success = True
                        else:
                            print(f"[ERROR] Failed to login for {uname}, retrying...")
                            # Try to reinitialize driver and retry
                            try:
                                if driver is not None:
                                    driver.quit()
                            except:
                                pass  # Ignore errors when quitting
                            
                            driver = init_driver()
                            retry_count += 1
                    except Exception as e:
                        print(f"[ERROR] Error processing pending messages for {uname}: {e}")
                        if "invalid session id" in str(e):
                            print(f"[INFO] Invalid session detected while processing pending messages for {uname}, reinitializing driver (attempt {retry_count+1}/{max_retry_attempts})...")
                            # Try to reinitialize driver and retry
                            try:
                                if driver is not None:
                                    driver.quit()
                            except:
                                pass  # Ignore errors when quitting
                            
                            driver = init_driver()
                            retry_count += 1
                        else:
                            # For other errors, log and continue to next account
                            print(f"[ERROR] Non-session error processing pending messages for {uname}: {e}")
                            break
                
                if not success and retry_count >= max_retry_attempts:
                    print(f"[ERROR] Maximum retry attempts ({max_retry_attempts}) reached for {uname}. Skipping account.")
        except Exception as outer_e:
            print(f"[ERROR] Unexpected error in pending messages processing: {outer_e}")
            traceback.print_exc()
        finally:
            if driver:
                try:
                    driver.quit()
                    print("[INFO] Closed driver after pending messages processing")
                except:
                    print("[WARNING] Error while closing driver after pending messages processing")
                    
        print(f"\n{'='*80}\nPENDING MESSAGES PROCESSING COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n")
        
        # Restore original stdout after pending processing
        sys.stdout = original_stdout
        pending_log.close()
        print(f"[INFO] Pending messages processing log saved to: {pending_log_file}")
        
        # Now run the main handler with proper session tracking
        for i, row in accounts.iterrows():
            uname = row['username']
            pas = row['password']
            main_handler(uname, pas, univer)

    except KeyboardInterrupt:
        print("\n[CRITICAL] Keyboard Interrupt detected in main thread!")
        
        # Try to quit the driver if it exists
        try:
            if driver is not None:
                driver.quit()
                print("[INFO] Successfully closed browser driver")
        except Exception as e:
            print(f"[ERROR] Failed to close driver: {e}")
            
        # Last resort immediate exit - no subprocess calls
        print("[CRITICAL] Directly terminating from KeyboardInterrupt handler...")
        os._exit(1)

    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        traceback.print_exc()  # Print detailed traceback for debugging
    
    finally:
        # Ensure the logging is stopped
        time_tracker.stop_background_logging()
        
        # Final update only if there was an active session
        if time_tracker.start_time is not None:
            try:
                time_tracker.log_execution_time(is_final=True)
                print("[INFO] Final summary table update completed.")
            except Exception as e:
                print(f"[ERROR] Failed to update summary table: {e}")
                
        # Make sure to restore original stdout if we haven't already
        if 'original_stdout' in locals() and sys.stdout != original_stdout:
            sys.stdout = original_stdout
            print("[INFO] Restored original stdout.")

