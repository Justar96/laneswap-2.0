FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Expose ports for API and web monitor
EXPOSE 8000 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the API server
CMD ["python", "-m", "laneswap.api.server"] 