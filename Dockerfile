# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (e.g., PostgreSQL client)
RUN apt-get update && apt-get install -y libpq-dev

# Copy the current directory contents into the container
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application with Gunicorn
CMD ["gunicorn", "truyenhay.wsgi:application", "--bind", "0.0.0.0:8000"]
