# LaneSwap Service Monitoring with Discord and CLI

This document provides examples and instructions for using LaneSwap's Discord webhook integration and enhanced CLI features for service monitoring.

## Discord Webhook Integration

LaneSwap now supports Discord webhooks for service monitoring, allowing you to receive notifications when service status changes or when specific events occur.

### Setting Up Discord Webhooks

#### 1. Create a Discord Webhook

1. In your Discord server, go to Server Settings > Integrations > Webhooks
2. Click "New Webhook"
3. Name your webhook (e.g., "LaneSwap Monitor")
4. Choose the channel where notifications should be sent
5. Copy the webhook URL

#### 2. Configure the Default Webhook

```bash
# Set up the default Discord webhook
laneswap discord setup --webhook-url "https://discord.com/api/webhooks/your-webhook-url" --username "LaneSwap Monitor"
```

#### 3. Configure Service-Specific Webhooks

```bash
# Register a webhook for a specific service
laneswap discord register --service-id "your-service-id" --webhook-url "https://discord.com/api/webhooks/your-webhook-url" --levels "warning,error"

# List configured webhooks
laneswap discord list

# Test a webhook
laneswap discord test --service-id "your-service-id" --level "warning" --message "This is a test notification"
```

## Enhanced CLI Service Management

LaneSwap now provides a comprehensive set of CLI commands for managing services.

### Service Registration and Heartbeats

```bash
# Register a new service
laneswap service register --name "My Service" --metadata '{"version": "1.0.0", "environment": "production"}'

# Send a heartbeat
laneswap service heartbeat --id "your-service-id" --status "healthy" --message "Service is running normally"

# List all services
laneswap service list

# Get details for a specific service
laneswap service list --id "your-service-id"
```

### Service Monitoring

```bash
# Run a heartbeat daemon that sends regular heartbeats
laneswap service daemon --id "your-service-id" --interval 30 --status "healthy"

# Monitor a service and send Discord notifications on status changes
laneswap service monitor --id "your-service-id" --interval 60 --webhook-url "https://discord.com/api/webhooks/your-webhook-url"

# Configure a Discord webhook for a service
laneswap service webhook --id "your-service-id" --webhook-url "https://discord.com/api/webhooks/your-webhook-url" --levels "warning,error"
```

## Web Monitor

LaneSwap includes a web-based dashboard for monitoring services.

```bash
# Start the web monitor
laneswap dashboard --port 8080 --api-url "http://localhost:8000"
```

## Example Workflow

Here's a complete example workflow for setting up service monitoring with Discord notifications:

1. Register a service:
   ```bash
   laneswap service register --name "API Server" --metadata '{"version": "1.0.0"}'
   # Note the service ID returned
   ```

2. Configure a Discord webhook for the service:
   ```bash
   laneswap service webhook --id "your-service-id" --webhook-url "https://discord.com/api/webhooks/your-webhook-url"
   ```

3. Start the heartbeat daemon in one terminal:
   ```bash
   laneswap service daemon --id "your-service-id" --interval 30
   ```

4. Start the service monitor in another terminal:
   ```bash
   laneswap service monitor --id "your-service-id" --interval 60 --webhook-url "https://discord.com/api/webhooks/your-webhook-url"
   ```

5. Start the web monitor:
   ```bash
   laneswap dashboard
   ```

Now you have:
- A service sending regular heartbeats
- Discord notifications when the service status changes
- A web dashboard for monitoring the service

## Advanced Configuration

For more advanced configuration options, refer to the LaneSwap documentation or use the `--help` flag with any command:

```bash
laneswap service --help
laneswap discord --help
``` 