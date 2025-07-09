import time
import csv
from datetime import datetime

def update_session_metrics(metric_name, value=None):
    """Update a specific metric with a value or increment it by 1"""
    global metrics, start_time, last_update_time, carry_forward_profiles, carry_forward_messages
    
    if start_time is None:
        print("[WARNING] No active session. Call begin_session() first.")
        return
        
    current_time = time.time()
    elapsed_time = current_time - start_time
    
    # Convert elapsed time to hours and minutes for display
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    time_str = f"{hours:02d}:{minutes:02d}"
    
    # Update the metric
    if value is not None:
        # Direct value update
        metrics[metric_name] = value
        if metric_name == "execution_time":
            print(f"[INFO] Updated {metric_name} to {time_str}")
        else:
            print(f"[INFO] Updated {metric_name} to {value}")
    else:
        # Increment by 1
        metrics[metric_name] = metrics.get(metric_name, 0) + 1
        print(f"[INFO] Incremented {metric_name} to {metrics[metric_name]}")
    
    # Update last update time
    last_update_time = current_time
    
    # Update the summary table
    log_execution_time(is_final=False)

def log_execution_time(is_final=False):
    """Log the execution time and metrics in a formatted table"""
    global metrics, start_time, last_update_time, carry_forward_profiles, carry_forward_messages
    
    if start_time is None:
        print("[WARNING] No active session. Call begin_session() first.")
        return
        
    current_time = time.time()
    elapsed_time = current_time - start_time
    
    # Convert elapsed time to hours and minutes
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    time_str = f"{hours:02d}:{minutes:02d}"
    
    # Update the execution time metric with the formatted string
    metrics["execution_time"] = time_str
    
    # Calculate rates per hour
    profiles_per_hour = (metrics.get("profiles_visited", 0) / elapsed_time) * 3600 if elapsed_time > 0 else 0
    messages_per_hour = (metrics.get("sent_messages", 0) / elapsed_time) * 3600 if elapsed_time > 0 else 0
    
    # Calculate success rates
    match_rate = (metrics.get("profiles_matched", 0) / metrics.get("profiles_visited", 1)) * 100
    message_rate = (metrics.get("sent_messages", 0) / metrics.get("profiles_matched", 1)) * 100
    
    # Calculate carry forward metrics
    total_carried_forward = carry_forward_profiles + metrics.get("unvisited_profiles", 0)
    total_carried_forward_messages = carry_forward_messages + metrics.get("pending_messages", 0)
    
    # Print the summary table
    print("\n" + "="*100)
    print(f"{'Metric':<30} {'Value':<15} {'Rate/Hour':<15} {'Success Rate':<15} {'Carry Forward':<15}")
    print("-"*100)
    print("{:<30} {:<15} {:<15.2f} {:<15.1f}% {:<15}".format(
        'Profiles Visited',
        metrics.get('profiles_visited', 0),
        profiles_per_hour,
        match_rate,
        total_carried_forward
    ))
    print("{:<30} {:<15} {:<15} {:<15} {:<15}".format(
        'Profiles Matched',
        metrics.get('profiles_matched', 0),
        '-',
        '-',
        '-'
    ))
    print("{:<30} {:<15} {:<15.2f} {:<15.1f}% {:<15}".format(
        'Messages Sent',
        metrics.get('sent_messages', 0),
        messages_per_hour,
        message_rate,
        '-'
    ))
    print("{:<30} {:<15} {:<15} {:<15} {:<15}".format(
        'Already Sent',
        metrics.get('already_sent', 0),
        '-',
        '-',
        '-'
    ))
    print("{:<30} {:<15} {:<15} {:<15} {:<15}".format(
        'Execution Time',
        time_str,
        '-',
        '-',
        '-'
    ))
    print("="*100)
    
    if is_final:
        print("\nFinal Summary:")
        print(f"Total Execution Time: {time_str}")
        print(f"Total Profiles Visited: {metrics.get('profiles_visited', 0)}")
        print(f"Total Profiles Matched: {metrics.get('profiles_matched', 0)}")
        print(f"Total Messages Sent: {metrics.get('sent_messages', 0)}")
        print(f"Total Already Sent: {metrics.get('already_sent', 0)}")
        print(f"Total Carry Forward Profiles: {total_carried_forward}")
        print(f"Total Carry Forward Messages: {total_carried_forward_messages}")
        print(f"Average Profiles per Hour: {profiles_per_hour:.2f}")
        print(f"Average Messages per Hour: {messages_per_hour:.2f}")
        print(f"Match Rate: {match_rate:.1f}%")
        print(f"Message Success Rate: {message_rate:.1f}%")
        
        # Update the CSV file with the final metrics
        try:
            with open("Summary-table.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.fromtimestamp(start_time).strftime("%m/%d/%Y %H:%M"),
                    datetime.fromtimestamp(current_time).strftime("%m/%d/%Y %H:%M"),
                    metrics.get("profiles_fetched", 0),
                    metrics.get("profiles_visited", 0),
                    metrics.get("profiles_matched", 0),
                    metrics.get("sent_messages", 0),
                    metrics.get("deleted_users", 0),
                    metrics.get("responses_received", 0),
                    metrics.get("already_sent", 0),
                    total_carried_forward,
                    total_carried_forward_messages,
                    time_str  # Using the formatted time string (HH:MM)
                ])
        except Exception as e:
            print(f"[ERROR] Failed to write to Summary-table.csv: {e}")