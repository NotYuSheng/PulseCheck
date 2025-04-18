# Use a minimal Python base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY . .

# Set environment variables for the FastAPI app
ENV DATA_DIR=/app/services_data

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
