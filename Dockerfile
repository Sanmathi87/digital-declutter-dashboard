# Start from an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (helps Docker cache this step for faster rebuilds)
COPY requirements.txt .

# Install all required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Tell Docker this container will use port 5000
EXPOSE 5000

# Command to run when the container starts
CMD ["python", "app.py"]