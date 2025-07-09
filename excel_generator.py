import pandas as pd
from datetime import datetime
import os

def generate_excel_report():
    # Create a new Excel writer object
    output_file = f'Facebook_Report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    
    # Sheet 1: Execution Log
    try:
        execution_log = pd.read_csv('execution_log.csv')
        execution_log.to_excel(writer, sheet_name='Execution Log', index=False)
    except Exception as e:
        print(f"Error processing execution log: {e}")
        pd.DataFrame().to_excel(writer, sheet_name='Execution Log')

    # Sheet 2: Visited Accounts
    try:
        visited_accounts = pd.read_csv('visited_accounts.csv')
        visited_accounts.to_excel(writer, sheet_name='Visited Accounts', index=False)
    except Exception as e:
        print(f"Error processing visited accounts: {e}")
        pd.DataFrame().to_excel(writer, sheet_name='Visited Accounts')

    # Sheet 3: Unvisited Profiles
    try:
        unvisited_profiles = pd.read_csv('unvisited_profiles.csv')
        unvisited_profiles.to_excel(writer, sheet_name='Unvisited Profiles', index=False)
    except Exception as e:
        print(f"Error processing unvisited profiles: {e}")
        pd.DataFrame().to_excel(writer, sheet_name='Unvisited Profiles')

    # Sheet 4: Unread Users
    try:
        unread_users = pd.read_csv('unreadUsers.csv')
        unread_users.to_excel(writer, sheet_name='Unread Messages', index=False)
    except Exception as e:
        print(f"Error processing unread users: {e}")
        pd.DataFrame().to_excel(writer, sheet_name='Unread Messages')

    # Save and close the Excel file
    writer.close()
    
    # Read the file content
    with open(output_file, 'rb') as f:
        file_content = f.read()
    
    # Delete the temporary file
    os.remove(output_file)
    
    return file_content 