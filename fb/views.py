from django.shortcuts import render, HttpResponse, redirect
import multiprocessing, io, threading, os, sys
import pandas as pd
from datetime import datetime
from .auto import main_handler
import re

def validate_university_file(file_content):
    """
    Validates and fixes a university file if possible
    
    Args:
        file_content: String content of the CSV file
        
    Returns:
        pandas.DataFrame: Validated university dataframe or None if cannot be fixed
        str: Error message if validation fails, None if successful
    """
    try:
        # First try to parse as normal CSV
        df = pd.read_csv(io.StringIO(file_content))
        
        # Check if the 'university' column exists
        if 'university' in df.columns:
            # Remove rows where the value is just "university" (column name duplicate)
            df = df[~(df['university'].str.lower().str.strip() == 'university')]
            # Remove empty values
            df = df[df['university'].notna() & (df['university'].str.strip() != '')]
            # Remove duplicates
            df = df.drop_duplicates(subset=['university'])
            print(f"Found {len(df)} valid university entries after cleaning")
            return df, None
            
        # If there's only one column, rename it to 'university'
        if len(df.columns) == 1:
            df = df.rename(columns={df.columns[0]: 'university'})
            # Clean data
            df = df[~(df['university'].str.lower().str.strip() == 'university')]
            df = df[df['university'].notna() & (df['university'].str.strip() != '')]
            df = df.drop_duplicates(subset=['university'])
            print(f"Renamed first column to 'university', found {len(df)} valid entries after cleaning")
            return df, None
            
        # If there are multiple columns, check if any column name contains 'uni'
        uni_columns = [col for col in df.columns if 'uni' in col.lower()]
        if uni_columns:
            df = df.rename(columns={uni_columns[0]: 'university'})
            df = df[['university']]  # Keep only the university column
            # Clean data
            df = df[~(df['university'].str.lower().str.strip() == 'university')]
            df = df[df['university'].notna() & (df['university'].str.strip() != '')]
            df = df.drop_duplicates(subset=['university'])
            print(f"Found column with 'uni' in name, using it as university column, found {len(df)} valid entries")
            return df, None
            
        # If no suitable column, try to take the first column
        df = df.iloc[:, 0].to_frame()
        df.columns = ['university']
        # Clean data
        df = df[~(df['university'].str.lower().str.strip() == 'university')]
        df = df[df['university'].notna() & (df['university'].str.strip() != '')]
        df = df.drop_duplicates(subset=['university'])
        print(f"No 'university' column found. Using first column, found {len(df)} valid entries")
        return df, "No 'university' column found. Using the first column as university names."
        
    except Exception as e:
        # If normal CSV parsing fails, try to extract universities line by line
        try:
            lines = file_content.strip().split('\n')
            universities = []
            
            # Skip potential header row if it contains 'university'
            start_idx = 0
            if lines and 'university' in lines[0].lower():
                start_idx = 1
                print("Skipping first line as it contains 'university'")
                
            # Extract university names from each line
            for i in range(start_idx, len(lines)):
                line = lines[i].strip()
                # Skip empty lines and lines containing just "university"
                if line and line.lower() != 'university':
                    universities.append(line)
                    
            if universities:
                df = pd.DataFrame({'university': universities})
                # Remove duplicates
                df = df.drop_duplicates()
                print(f"Extracted {len(df)} valid university names from plain text")
                return df, "File format fixed. Extracted university names from each line."
            else:
                return None, f"Could not extract university names from the file. Error: {str(e)}"
        except Exception as e2:
            return None, f"File format could not be fixed. Please ensure it's a valid CSV with a 'university' column. Error: {str(e2)}"

# Create your views here.
def facebook(request):
    if not request.user.is_authenticated:
        print('User not logged In........')
        return redirect('/')

    if request.method == 'POST':
        uploaded_file = request.FILES.get('csv_file')
        print(uploaded_file)
        file_data = uploaded_file.read().decode('utf-8')
        csv_reader = pd.read_csv(io.StringIO(file_data))

        univeri = request.FILES.get('uni')  
        print(univeri)
        file_data1 = univeri.read().decode('utf-8')
        # Validate university file format
        try:
            # Try to validate and fix the university file
            univer, warning_message = validate_university_file(file_data1)
            
            if univer is None:
                # If validation completely failed
                error_message = warning_message or "The university file format is invalid. Please use the provided template."
                return render(request, 'fb/upload.html', {'error': error_message})
            
            print(f"University file loaded with {len(univer)} entries")
            
            # If file is empty after processing
            if univer.empty:
                error_message = "The university file is empty after processing. Please add university names to the file."
                return render(request, 'fb/upload.html', {'error': error_message})
                
            # Make a copy of the university file to uniall.csv for standalone script use
            os.makedirs('main/staticfiles/sessions', exist_ok=True)
            os.makedirs('staticfiles/sessions', exist_ok=True)
            
            # Save to all required paths to ensure script can find the file
            univer.to_csv('main/staticfiles/sessions/uniall.csv', index=False)
            univer.to_csv('staticfiles/sessions/uniall.csv', index=False)
            univer.to_csv('staticfiles/uniall.csv', index=False)
            
            print(f"[INFO] Saved university file with {len(univer)} valid entries to all required paths")
            
            # If there was a warning but we could still process the file
            context = {'success': True}
            if warning_message:
                # Create a new dictionary with both keys
                context = {
                    'success': True,
                    'warning': f"University file loaded with warnings: {warning_message}"
                }
            else:
                # Just use the success key
                context = {'success': True}
        except Exception as e:
            error_message = f"Error processing university file: {str(e)}. Please ensure it's a valid CSV with a 'university' column."
            context = {'error': error_message}
            return render(request, 'fb/upload.html', context)
        
        # Make sure to update the session values for display in template
        # Store file names in session and database
        csv_filename = uploaded_file.name
        uni_filename = univeri.name
        
        # Update session values
        request.session['last_csv_file'] = csv_filename
        request.session['last_uni_file'] = uni_filename
        
        # Add timestamps
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request.session['last_csv_timestamp'] = current_time
        request.session['last_uni_timestamp'] = current_time
        
        # Set session to expire in 30 days
        request.session.set_expiry(30 * 24 * 60 * 60)
        
        # Force the session to be saved and refreshed
        request.session.save()
        
        print(f"[DEBUG] Updated session values: last_csv_file={csv_filename}, last_uni_file={uni_filename}")

        row = csv_reader.shape[0]
        print(row)

        processes = []
        max_workers = 1
        username = request.user.username
        print(username)

        # Start processes that run the task in parallel
        for i, row in csv_reader.iterrows():
            uname = row['username']
            pas = row['password']
            print(uname, pas)

            while len(processes) >= max_workers:
                # Iterate over the processes to check if any have finished
                for p in processes:
                    if not p.is_alive():  # If the process is not running
                        p.join()  # Clean up the process
                        processes.remove(p)  # Remove it from the list
                        break 

            # Pass the already loaded university DataFrame directly to main_handler
            process = multiprocessing.Process(target=main_handler, args=(uname, pas, univer))
            processes.append(process)
            process.start()

        # Wait for all processes to complete
        for process in processes:
            process.join()

        # Update the context with the success message after processing
        # Include the file names in the success context so they're immediately visible
        context = {
            'success': True,
            'message': "Files uploaded and processing completed!",
            'last_csv_file': csv_filename,
            'last_uni_file': uni_filename,
            'last_csv_timestamp': current_time,
            'last_uni_timestamp': current_time
        }
        # Return early after POST processing is done
        return render(request, 'fb/upload.html', context)
        
    # This code only runs for GET requests
    # Get last uploaded filenames from session (if they exist)
    last_csv_file = request.session.get('last_csv_file', None)
    last_uni_file = request.session.get('last_uni_file', None)
    last_csv_timestamp = request.session.get('last_csv_timestamp', None)
    last_uni_timestamp = request.session.get('last_uni_timestamp', None)
    
    print(f"[DEBUG] GET request - Session contents: {dict(request.session)}")
    
    context = {
        'last_csv_file': last_csv_file,
        'last_uni_file': last_uni_file,
        'last_csv_timestamp': last_csv_timestamp,
        'last_uni_timestamp': last_uni_timestamp,
    }
    
    # Print debug info
    print(f"[DEBUG] GET request - Session values: last_csv_file={last_csv_file}, last_uni_file={last_uni_file}")
    
    return render(request, 'fb/upload.html', context)


import csv
import os
from django.shortcuts import render
from django.conf import settings

def display_csv(request):
    try:
        # Create a new Excel writer object
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Sheet 1: Users
        try:
            if os.path.exists('visited_accounts.csv'):
                users_df = pd.read_csv('visited_accounts.csv')
                # Transform status values
                users_df['status'] = users_df['status'].apply(
                    lambda x: 'Yes' if x.lower() in ['unmatched', 'matched', 'locked', 'pending', 'messaged'] else x.capitalize()
                )
                # Rename columns to match frontend
                users_df = users_df.rename(columns={
                    'link': 'Profile Link',
                    'name': 'Name',
                    'timestamp': 'Timestamp',
                    'status': 'Visited',
                    'searched_by': 'Search By'
                })
                users_df.to_excel(writer, sheet_name='Users', index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name='Users')
        except Exception as e:
            print(f"Error processing users: {e}")
            pd.DataFrame().to_excel(writer, sheet_name='Users')


        # Sheet 2: Messages
        try:
            # Get message data from visited_accounts.csv
            messages_data = []
            if os.path.exists('visited_accounts.csv'):
                df = pd.read_csv('visited_accounts.csv')
                # Filter for rows with 'pending' or 'messaged' status
                filtered_df = df[df['status'].str.lower().isin(['pending', 'messaged'])]
                if not filtered_df.empty:
                    messages_data = []
                    for _, row in filtered_df.iterrows():
                        status = row['status'].lower()
                        delivered = 'Yes' if status == 'messaged' else 'No'
                        delivered_time = row['timestamp'] if status == 'messaged' else '-'
                        messages_data.append({
                            'Name': row['name'],
                            'Find Time': row['timestamp'],
                            'Delivered': delivered,
                            'Delivered Time': delivered_time
                        })
            messages_df = pd.DataFrame(messages_data)
            messages_df.to_excel(writer, sheet_name='Messages', index=False)
        except Exception as e:
            print(f"Error processing messages: {e}")
            pd.DataFrame().to_excel(writer, sheet_name='Messages')

        

        # Sheet 3: Conversations
        try:
            if os.path.exists('unreadUsers.csv'):
                conversations_df = pd.read_csv('unreadUsers.csv')
                # Rename columns to match frontend
                conversations_df = conversations_df.rename(columns={
                    'username': 'Username',
                    'timestamp': 'Timestamp',
                    'link': 'Profile Link'
                })
                conversations_df.to_excel(writer, sheet_name='Conversations', index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name='Conversations')
        except Exception as e:
            print(f"Error processing conversations: {e}")
            pd.DataFrame().to_excel(writer, sheet_name='Conversations')

        # Sheet 4: Summary Table
        try:
            # Get the data from Summary-table.csv if it exists, otherwise create empty DataFrame
            try:
                summary_data = pd.read_csv('Summary-table.csv')
            except:
                summary_data = pd.DataFrame(columns=[
                    'Session Start', 'Session End', 'Duration', 'Profiles Fetched',
                    'Profiles Visited', 'Profiles Matched', 'Messages Sent',
                    'Responses Received', 'Already Sent', 'Deleted Users',
                    'Carry Forward Profiles', 'Carry Forward Messages'
                ])
            summary_data.to_excel(writer, sheet_name='Summary', index=False)
        except Exception as e:
            print(f"Error processing summary table: {e}")
            pd.DataFrame().to_excel(writer, sheet_name='Summary')    

        # Save the Excel file
        writer.close()
        output.seek(0)

        # Create the HttpResponse object with Excel mime type
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=Facebook_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        return response
        
    except Exception as e:
        print(f"Error generating Excel file: {e}")
        return HttpResponse(status=500)

def message_display(request):
    # Path to the visited_accounts.csv file
    csv_file_path = os.path.join(settings.BASE_DIR, 'visited_accounts.csv')
    message_data = []

    try:
        if os.path.exists(csv_file_path):
            df = pd.read_csv(csv_file_path)
            
            # Filter for rows with 'pending' or 'messaged' status
            filtered_df = df[df['status'].str.lower().isin(['pending', 'messaged'])]
            
            if not filtered_df.empty:
                # Process each row in the filtered dataframe
                for index, row in filtered_df.iterrows():
                    name = row['name']
                    timestamp = row['timestamp']
                    status = row['status'].lower()
                    
                    # Format timestamp for display
                    try:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
                        formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_timestamp = timestamp
                    
                    # Set values based on status
                    if status == 'pending':
                        delivered = 'No'
                        delivered_time = '-'
                    else:  # status == 'messaged'
                        delivered = 'Yes'
                        delivered_time = formatted_timestamp
                    
                    message_data.append({
                        'name': name,
                        'find_time': formatted_timestamp,
                        'delivered': delivered,
                        'delivered_time': delivered_time
                    })
                
                # Sort by find_time (newest first)
                message_data.sort(key=lambda x: x['find_time'], reverse=True)
    
    except Exception as e:
        print(f"Error processing message data: {e}")
    
    return render(request, 'message_display.html', {'data': message_data})

from django.shortcuts import render
from django.http import HttpResponse
import os

def sessions_table_view(request):
    return render(request, 'summary-table.html')

def get_execution_log_data(request):
    # Path to your CSV file - update to use Summary-table.csv
    csv_path = os.path.join(settings.BASE_DIR, 'Summary-table.csv')
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:
            csv_data = file.read()
        return HttpResponse(csv_data, content_type='text/csv')
    except FileNotFoundError:
        return HttpResponse("CSV file not found", status=404)

def users_view(request):
    """
    View function for displaying the visited Facebook users from the visited_accounts.csv file.
    Extracts data and formats it for display in the users_view.html template.
    """
    import os
    import csv
    import re
    from datetime import datetime
    
    # Path to the visited_accounts.csv file
    csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visited_accounts.csv')
    
    user_data = []
    
    try:
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                headers = next(csv_reader)  # Skip header row
                
                # Temporary set to track seen profile links to avoid duplicates
                seen_links = set()
                
                for row in csv_reader:
                    if len(row) >= 4:  # Ensure row has at least 4 columns (link, name, timestamp, status)
                        link = row[0]
                        
                        # Skip duplicate entries
                        if link in seen_links:
                            continue
                        
                        # Add to seen links set to avoid future duplicates
                        seen_links.add(link)
                        
                        name = row[1]
                        timestamp = row[2]
                        status = row[3]
                        
                        # Get the searched_by field if available (column 5)
                        searched_by = "Facebook"  # Default value
                        if len(row) >= 5 and row[4]:
                            searched_by = row[4]
                        
                        # Extract group name from the link using regex
                        # Example link: https://www.facebook.com/groups/1285008385191756/user/100069818904382/
                        group = "Direct"
                        group_url = None
                        
                        # For links from Facebook groups
                        if 'groups/' in link:
                            # Extract group ID and create group URL
                            group_match = re.search(r'groups/([^/]+)', link)
                            if group_match:
                                group_id = group_match.group(1)
                                group = f"Group: {group_id}"
                                group_url = f"https://www.facebook.com/groups/{group_id}/"
                        
                        # Extract group name from the name field if it contains " - " format
                        # Example: "Mind The Stairs - Mental Health Organisation"
                        if ' - ' in name:
                            parts = name.split(' - ', 1)
                            if len(parts) > 1:
                                user_name = parts[0].strip()
                                group_name = parts[1].strip()
                                if group_name:
                                    group = group_name
                                    # Update name to just include the user part
                                    name = user_name
                        
                        # Format timestamp
                        try:
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
                            formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_timestamp = timestamp
                        
                        # Transform status value for display
                        # If status is "unmatched", "locked", or similar, set display status to "Yes"
                        display_status = status.capitalize()
                        if display_status.lower() in ['unmatched', 'matched', 'locked' , 'pending', 'messaged']:
                            display_status = "Yes"
                        
                        user_data.append({
                            'link': link,
                            'name': name,
                            'timestamp': formatted_timestamp,
                            'status': display_status,
                            'group': group,
                            'group_url': group_url,
                            'search_by': searched_by
                        })
                
                # Sort by timestamp (newest first)
                user_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        print(f"Error reading visited_accounts.csv: {e}")
    
    return render(request, 'fb/users_view.html', {'user_data': user_data})

def conversations_view(request):
    """
    View function for displaying conversation data from unreadUsers.csv.
    Extracts username, timestamp, and link data for display in the conversations.html template.
    """
    import os
    import csv
    from datetime import datetime
    
    # Path to the unreadUsers.csv file
    csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'unreadUsers.csv')
    
    conversations_data = []
    
    try:
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                headers = next(csv_reader)  # Skip header row
                
                for row in csv_reader:
                    if len(row) >= 3:  # Ensure row has at least 3 columns (username, timestamp, link)
                        username = row[0]
                        timestamp = row[1]
                        link = row[2]
                        
                        # Format timestamp if needed
                        try:
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_timestamp = timestamp
                        
                        conversations_data.append({
                            'username': username,
                            'timestamp': formatted_timestamp,
                            'link': link
                        })
                
                # Sort by timestamp (newest first)
                conversations_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        print(f"Error reading unreadUsers.csv: {e}")
    
    return render(request, 'fb/conversations.html', {'conversations_data': conversations_data})

import requests

def get_ethnicity_from_fastapi(image_path):
    url = "http://localhost:5050/predict/"
    with open(image_path, "rb") as image_file:
        files = {
            "file": ("temp_image.jpg", image_file, "image/jpeg")  # <--- add content-type
        }
        response = requests.post(url, files=files)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json().get("detail", "Unknown error")}

# Example usage in a view
from django.http import JsonResponse

def predict_ethnicity_view(request):
    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]

        # Save image temporarily
        with open("temp_image.jpg", "wb") as f:
            for chunk in image.chunks():
                f.write(chunk)

        # Call FastAPI
        result = get_ethnicity_from_fastapi("temp_image.jpg")

        # Extract only ethnicity from the result
        if "ethnicity" in result:
            return JsonResponse({"ethnicity": result["ethnicity"]})
        else:
            return JsonResponse(result)  # Return error or fallback

    return JsonResponse({"error": "Invalid request"})

def ethnicity_form_view(request):
    if request.method == "POST" and request.FILES.get("image"):
        return predict_ethnicity_view(request)  # Use your view from above
    return render(request, "form.html")