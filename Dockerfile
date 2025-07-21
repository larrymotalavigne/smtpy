FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get clean

# Install Python dependencies first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose ports
EXPOSE 80

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "views.web:app", "--host", "0.0.0.0", "--port", "80"] 
