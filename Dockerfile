# Use an official Python image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH to the working directory
ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]
