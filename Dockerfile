FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y postfix && \
    apt-get clean

# Install Python dependencies first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose ports
EXPOSE 80 8025
# EXPOSE 25  # Uncomment if you want to expose SMTP

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "views.web:app", "--host", "0.0.0.0", "--port", "80"] 
