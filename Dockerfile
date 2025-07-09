# Dockerfile

# Step 1: Use an official Python runtime as a parent image
FROM python:3.9-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the Django project files to the container
COPY . /app/

# Step 5: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Step 7: Expose the port Django will run on
EXPOSE 8000

# Step 8: Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
