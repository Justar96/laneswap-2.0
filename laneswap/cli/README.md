# LaneSwap CLI Module

The CLI module provides command-line tools for interacting with the LaneSwap system, allowing users to manage services, send heartbeats, and monitor system health.

## Components

### Main CLI (`commands.py`)

The main CLI implementation, providing commands for all LaneSwap operations.

#### Key Features

- **Command Groups**: Organized command structure with subcommands
- **Interactive Mode**: Interactive prompts for required parameters
- **Rich Output**: Colorful and formatted output
- **Error Handling**: Comprehensive error handling
- **Help Text**: Detailed help text for all commands
- **Validation**: Input validation for all parameters

#### Usage Example

```bash
# Show help
laneswap --help

# Start the API server
laneswap server

# List all services
laneswap services list

# Get details for a specific service
laneswap services get <service-id>

# Register a new service
laneswap services register --name "my-service"

# Send a heartbeat
laneswap services heartbeat <service-id> --status healthy

# Validate the system
laneswap validate
```

### Service Commands (`service_commands.py`)

Commands for managing services and heartbeats.

#### Key Features

- **Service Registration**: Register new services
- **Service Listing**: List all registered services
- **Service Details**: Get detailed information about a service
- **Heartbeat Sending**: Send heartbeats for services
- **Service Deletion**: Delete services

#### Usage Example

```bash
# Register a new service
laneswap services register --name "my-service" --metadata '{"version": "1.0.0"}'

# List all services
laneswap services list

# Get details for a specific service
laneswap services get <service-id>

# Send a heartbeat
laneswap services heartbeat <service-id> --status healthy --message "Service is running normally"

# Delete a service
laneswap services delete <service-id>
```

### Terminal Monitor CLI (`terminal_monitor.py`)

Command-line interface for the terminal monitor.

#### Key Features

- **API URL Configuration**: Specify the API server URL
- **Refresh Interval**: Configure the refresh interval
- **Terminal Mode**: Enable or disable terminal mode
- **Pause Mode**: Start in paused mode

#### Usage Example

```bash
# Start the terminal monitor with default settings
laneswap-term

# Start with custom API URL
laneswap-term --api-url http://localhost:8000

# Start with custom refresh interval
laneswap-term --refresh 5.0

# Start in non-terminal mode
laneswap-term --no-terminal

# Start in paused mode
laneswap-term --paused
```

### Validation Commands (`validate.py`)

Commands for validating the LaneSwap system.

#### Key Features

- **Dependency Checking**: Verify that all required dependencies are installed
- **Import Validation**: Check that key components can be imported
- **Configuration Validation**: Verify that the configuration is valid
- **Connectivity Testing**: Test connections to external services

#### Usage Example

```bash
# Run validation with default options
laneswap validate

# Run validation with strict mode
laneswap validate --strict

# Run validation without printing results
laneswap validate --quiet
```

### CLI Utilities (`utils.py`)

Utility functions for the CLI.

#### Key Features

- **Output Formatting**: Functions for formatting CLI output
- **Input Validation**: Functions for validating user input
- **Error Handling**: Functions for handling and displaying errors
- **Configuration Loading**: Functions for loading configuration

## Command Structure

The LaneSwap CLI has the following command structure:

```
laneswap
├── server                  # Start the API server
├── services                # Service management commands
│   ├── list                # List all services
│   ├── get                 # Get details for a service
│   ├── register            # Register a new service
│   ├── heartbeat           # Send a heartbeat for a service
│   └── delete              # Delete a service
├── progress                # Progress tracking commands
│   ├── list                # List all progress tasks
│   ├── get                 # Get details for a progress task
│   ├── start               # Start a new progress task
│   ├── update              # Update a progress task
│   └── delete              # Delete a progress task
├── validate                # Validate the system
└── version                 # Show version information
```

## Integration with Other Modules

The CLI module integrates with other LaneSwap modules:

- **API Module**: Communicates with the API server
- **Client Module**: Uses the client library for API communication
- **Core Module**: Uses core types and utilities
- **Terminal Module**: Uses the terminal monitor for service monitoring

## Advanced Usage

### Custom Commands

You can add custom commands to the CLI by extending the command groups:

```python
import click
from laneswap.cli.commands import cli

@cli.group()
def custom():
    """Custom commands for LaneSwap."""
    pass

@custom.command()
@click.argument("name")
def hello(name):
    """Say hello to someone."""
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    cli()
```

### Environment Variables

The CLI supports configuration via environment variables:

```bash
# Set the API URL
export LANESWAP_API_URL="http://localhost:8000"

# Set the MongoDB connection string
export LANESWAP_MONGODB_URI="mongodb://localhost:27017"

# Set the Discord webhook URL
export LANESWAP_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
```

### Configuration File

The CLI can also be configured using a configuration file:

```bash
# Create a configuration file
cat > ~/.laneswap.json << EOF
{
  "api": {
    "url": "http://localhost:8000"
  },
  "mongodb": {
    "connection_string": "mongodb://localhost:27017",
    "database_name": "laneswap"
  },
  "discord": {
    "webhook_url": "https://discord.com/api/webhooks/..."
  }
}
EOF

# Use the configuration file
laneswap --config ~/.laneswap.json services list
```

## Best Practices

1. **Use Help Text**: Use the `--help` option to get detailed help for commands
2. **JSON Format**: Use JSON format for metadata and other complex parameters
3. **Service IDs**: Store service IDs in environment variables for easy access
4. **Error Handling**: Check command exit codes for errors
5. **Scripting**: Use the CLI in scripts for automation
6. **Terminal Monitor**: Use the terminal monitor for real-time monitoring
7. **Validation**: Run validation before using the system
8. **Configuration**: Use environment variables or configuration files for common settings
9. **Secure Connections**: Use HTTPS in production
10. **Logging**: Use the `--verbose` option for detailed logging 