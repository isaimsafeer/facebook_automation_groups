import csv
import os
import time
from datetime import datetime

def add_session_data():
    # File path
    summary_csv_file = "Summary-table.csv"
    
    # Check if file exists, create if it doesn't
    file_exists = os.path.isfile(summary_csv_file)
    if not file_exists:
        print(f"Creating new {summary_csv_file} file...")
        with open(summary_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Start time", "End time", "Profiles Fetched", "Profiles Visited",
                "Profiles Matched", "Sent Messages", "Deleted Users", "Responses received",
                "Already Sent", "Carry forward Profiles", "Carry forward Messages", "Time"
            ])
    
    # Get user input for session data
    print("\n=== Add New Session Data ===")
    
    try:
        # Timestamps
        start_time = input("Enter start time (MM/DD/YYYY HH:MM) or press Enter for current time: ")
        if not start_time:
            start_time = datetime.now().strftime('%m/%d/%Y %H:%M')
        
        end_time = input("Enter end time (MM/DD/YYYY HH:MM) or press Enter for current time: ")
        if not end_time:
            end_time = datetime.now().strftime('%m/%d/%Y %H:%M')
        
        # Metrics
        profiles_fetched = int(input("Profiles Fetched: ") or "0")
        profiles_visited = int(input("Profiles Visited: ") or "0")
        profiles_matched = int(input("Profiles Matched: ") or "0")
        sent_messages = int(input("Sent Messages: ") or "0")
        deleted_users = int(input("Deleted Users: ") or "0")
        responses_received = int(input("Responses received: ") or "0")
        already_sent = int(input("Already Sent: ") or "0")
        carry_forward_profiles = int(input("Carry forward Profiles: ") or "0")
        carry_forward_messages = int(input("Carry forward Messages: ") or "0")
        
        session_time = input("Session Time (e.g., '60.5 seconds'): ")
        if not session_time:
            session_time = "0 seconds"
        
        # Create row data
        row_data = [
            start_time,
            end_time,
            profiles_fetched,
            profiles_visited,
            profiles_matched,
            sent_messages,
            deleted_users,
            responses_received,
            already_sent,
            carry_forward_profiles,
            carry_forward_messages,
            session_time
        ]
        
        # Check if all activity metrics are zero
        if (profiles_fetched == 0 and profiles_visited == 0 and profiles_matched == 0 and
            sent_messages == 0 and deleted_users == 0 and responses_received == 0 and
            already_sent == 0):
            print("\nSkipping session with all zero metrics. No data added to summary table.")
            return
        
        # Write to CSV
        with open(summary_csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)
        
        print(f"\nSession data successfully added to {summary_csv_file}")
        
    except ValueError as e:
        print(f"Error: Please enter valid numbers for metrics. {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_session_data() 