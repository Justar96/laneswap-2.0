#!/bin/bash
# Example script demonstrating LaneSwap CLI features
# This script shows how to use the LaneSwap CLI to:
# 1. Register a service
# 2. Configure a Discord webhook
# 3. Send heartbeats
# 4. Monitor service status

# Exit on error
set -e

# Configuration
API_URL="http://localhost:8000"
WEBHOOK_URL="YOUR_DISCORD_WEBHOOK_URL"  # Replace with your Discord webhook URL
SERVICE_NAME="CLI Example Service"

echo "LaneSwap CLI Example"
echo "===================="
echo

# Check if the API server is running
echo "Checking if API server is running..."
if ! curl -s "$API_URL/health" > /dev/null; then
    echo "API server is not running. Starting it..."
    # Start the API server in the background
    laneswap start_server --port 8000 &
    API_PID=$!
    echo "API server started with PID: $API_PID"
    # Wait for the server to start
    sleep 3
else
    echo "API server is already running"
fi

echo

# Register a service
echo "Registering service: $SERVICE_NAME"
SERVICE_ID=$(laneswap service register --name "$SERVICE_NAME" --metadata '{"example": true, "source": "cli_example.sh"}' | grep "Service ID:" | awk '{print $3}')
echo "Service registered with ID: $SERVICE_ID"
echo

# Configure Discord webhook for the service
if [[ "$WEBHOOK_URL" != "YOUR_DISCORD_WEBHOOK_URL" ]]; then
    echo "Configuring Discord webhook for service"
    laneswap service webhook --id "$SERVICE_ID" --webhook-url "$WEBHOOK_URL" --levels "info,warning,error"
    echo
else
    echo "Skipping Discord webhook configuration (no webhook URL provided)"
    echo "To enable Discord notifications, edit this script and set WEBHOOK_URL to your Discord webhook URL"
    echo
fi

# Send a healthy heartbeat
echo "Sending HEALTHY heartbeat"
laneswap service heartbeat --id "$SERVICE_ID" --status "healthy" --message "Service is running normally"
echo

# Send a warning heartbeat
echo "Sending WARNING heartbeat"
laneswap service heartbeat --id "$SERVICE_ID" --status "warning" --message "High resource usage detected" --metadata '{"cpu": 85, "memory": 75}'
echo

# Send an error heartbeat
echo "Sending ERROR heartbeat"
laneswap service heartbeat --id "$SERVICE_ID" --status "error" --message "Service encountered an error" --metadata '{"error_code": 500, "error_message": "Internal server error"}'
echo

# Get service details
echo "Getting service details"
laneswap service list --id "$SERVICE_ID"
echo

# Start the web monitor in the background (if not already running)
echo "Checking if web monitor is running..."
if ! curl -s "http://localhost:8080" > /dev/null 2>&1; then
    echo "Starting web monitor in the background"
    laneswap dashboard --port 8080 --api-url "$API_URL" &
    MONITOR_PID=$!
    echo "Web monitor started with PID: $MONITOR_PID"
    
    # Open the web monitor in the default browser
    echo "Opening web monitor in browser"
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:8080" &
    elif command -v open > /dev/null; then
        open "http://localhost:8080" &
    else
        echo "Could not open browser automatically. Please open http://localhost:8080 manually."
    fi
else
    echo "Web monitor is already running"
fi

echo
echo "Example completed!"
echo "You can now:"
echo "1. View the service in the web monitor at http://localhost:8080"
echo "2. Run 'laneswap service daemon --id \"$SERVICE_ID\" --interval 30' to start a heartbeat daemon"
echo "3. Run 'laneswap service monitor --id \"$SERVICE_ID\" --interval 60 --webhook-url \"$WEBHOOK_URL\"' to monitor status changes"
echo

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    if [[ -n "$API_PID" ]]; then
        echo "Stopping API server (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi
    if [[ -n "$MONITOR_PID" ]]; then
        echo "Stopping web monitor (PID: $MONITOR_PID)"
        kill $MONITOR_PID 2>/dev/null || true
    fi
    echo "Done"
}

# Register cleanup function to run on exit
trap cleanup EXIT

# Keep the script running to maintain the background processes
echo "Press Ctrl+C to exit"
while true; do
    sleep 1
done 