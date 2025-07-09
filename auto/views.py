from django.shortcuts import render, redirect
from django.http import HttpResponse
import csv
import io,pandas as pd
from django.contrib.auth import authenticate, login
import os
import shutil
from auto.settings import STATIC_ROOT
# Create your views here.

def interface(request):
    if not request.user.is_authenticated:
        print('User not logged In........')
        return redirect('/login')
    if request.method == 'POST':
        # Get the selected dropdown option
        selected_option = request.POST.get('dropdown_option')
        print(selected_option)
        # Get the uploaded file
        # uploaded_file = request.FILES.get('csv_file')
        if selected_option=='facebook':
            return redirect('facebook')
        elif selected_option=='instagram':
           return redirect('instagram')
        # Process the file only if it exists
        # if uploaded_file:
        #     # Read and process the CSV file
        #     # file_data = uploaded_file.read().decode('utf-8')
        #     # csv_reader = csv.reader(io.StringIO(file_data))
        #     data=pd.read_csv(uploaded_file)
            
            # Example: Process CSV data and print each row

            # for row in csv_reader:
            #     print(row)
                
            # Do something with `selected_option` and CSV data here
            # For example, save data to the database, apply filters, etc.
            
            # return HttpResponse(f"File uploaded successfully with option '{selected_option}'")

    return render(request,'interface.html')

def login1(request):
    if request.user.is_authenticated:
        print('User already logged In........')
        return redirect('/')
    if request.method == 'POST':
        username=request.POST.get('email')
        password=request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print('welcome buddy...')
            login(request, user)
            return redirect('/')  # Redirect to a success page.
        else:
            print('Wrong Credentials......')
            return redirect('/login')
    return render(request,'login.html')

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def remove_directory_by_name(parent_dir, dir_name):
    # Construct the full path of the directory to remove
    target_dir = os.path.join(parent_dir, dir_name)
    
    # Check if the directory exists
    if os.path.isdir(target_dir):
        # Remove the directory and all its contents
        shutil.rmtree(target_dir)
        print(f"Directory '{target_dir}' has been removed.")
    else:
        print(f"Directory '{target_dir}' does not exist.")

def remove1(request):
    print(f'remove session function....{request.user.username}')
    parent_directory = f'{STATIC_ROOT}\\sessions'  # Replace with the actual parent directory path
    directory_name = f'{request.user.username}' 
    remove_directory_by_name(parent_directory, directory_name)
    return redirect('/')