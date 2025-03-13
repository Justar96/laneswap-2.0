# LaneSwap Examples Module

The examples module provides sample code and demonstration applications for the LaneSwap system, helping users understand how to use the library in various scenarios.

## Available Examples

### Simple Service (`simple_service.py`)

A simple service that sends heartbeats at regular intervals.

#### Key Features

- **Basic Heartbeat Sending**: Demonstrates how to send heartbeats
- **Automatic Heartbeats**: Uses the auto-heartbeat feature
- **Metadata**: Includes service metadata
- **Error Handling**: Demonstrates error handling
- **Command-line Arguments**: Configurable via command-line arguments

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.simple_service

# Run with custom API URL
python -m laneswap.examples.simple_service --api-url http://localhost:8000

# Run with custom service name
python -m laneswap.examples.simple_service --name "custom-service"

# Run with custom heartbeat interval
python -m laneswap.examples.simple_service --interval 10
```

### Progress Service (`progress_service.py`)

A service that demonstrates progress tracking for long-running tasks.

#### Key Features

- **Progress Task Creation**: Shows how to create progress tasks
- **Progress Updates**: Demonstrates updating progress
- **Task Completion**: Shows how to complete tasks
- **Multiple Tasks**: Manages multiple concurrent tasks
- **Random Progress**: Simulates varying progress rates

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.progress_service

# Run with custom API URL
python -m laneswap.examples.progress_service --api-url http://localhost:8000

# Run with custom number of tasks
python -m laneswap.examples.progress_service --tasks 5

# Run with custom task duration
python -m laneswap.examples.progress_service --duration 60
```

### Discord Webhook Example (`discord_webhook_example.py`)

Demonstrates how to use the Discord webhook adapter for notifications.

#### Key Features

- **Webhook Configuration**: Shows how to configure the Discord webhook
- **Status Notifications**: Demonstrates status change notifications
- **Error Notifications**: Shows error notifications
- **Stale Service Notifications**: Demonstrates stale service notifications
- **Recovery Notifications**: Shows service recovery notifications

#### Usage Example

```bash
# Run with default settings (requires DISCORD_WEBHOOK_URL environment variable)
python -m laneswap.examples.discord_webhook_example

# Run with custom webhook URL
python -m laneswap.examples.discord_webhook_example --webhook-url "https://discord.com/api/webhooks/..."

# Run with custom username and avatar
python -m laneswap.examples.discord_webhook_example --username "LaneSwap Bot" --avatar-url "https://example.com/avatar.png"
```

### Mock API Server (`mock_api_server.py`)

A mock API server that simulates the LaneSwap API for testing and demonstration.

#### Key Features

- **Service Simulation**: Simulates multiple services with different statuses
- **Random Status Changes**: Periodically changes service statuses
- **API Endpoints**: Implements the same endpoints as the real API
- **No Dependencies**: Runs without requiring MongoDB or other dependencies
- **Configurable**: Customizable number of services and update interval

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.mock_api_server

# Run with custom port
python -m laneswap.examples.mock_api_server --port 9000

# Run with custom number of services
python -m laneswap.examples.mock_api_server --services 10

# Run with custom update interval
python -m laneswap.examples.mock_api_server --interval 5
```

### Terminal Monitor Example (`terminal_monitor_example.py`)

Demonstrates how to use the terminal monitor for real-time service monitoring.

#### Key Features

- **Terminal UI**: Shows the colorful terminal UI
- **Real-time Updates**: Displays real-time service status updates
- **Keyboard Controls**: Demonstrates keyboard controls
- **Non-Terminal Mode**: Shows how to run in non-terminal mode
- **Custom Configuration**: Demonstrates configuration options

#### Usage Example

```bash
# Run with default settings (connects to localhost:8000)
python -m laneswap.examples.terminal_monitor_example

# Run with custom API URL
python -m laneswap.examples.terminal_monitor_example --api-url http://localhost:8000

# Run with custom refresh interval
python -m laneswap.examples.terminal_monitor_example --refresh 5.0

# Run in non-terminal mode
python -m laneswap.examples.terminal_monitor_example --no-terminal

# Run in paused mode
python -m laneswap.examples.terminal_monitor_example --paused
```

### Verify Installation (`verify_installation.py`)

A utility for verifying that LaneSwap is correctly installed and configured.

#### Key Features

- **Dependency Checking**: Verifies that all required dependencies are installed
- **Import Validation**: Checks that key components can be imported
- **Configuration Validation**: Verifies that the configuration is valid
- **Connectivity Testing**: Tests connections to external services
- **Detailed Reporting**: Provides detailed information about validation results

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.verify_installation

# Run with strict mode
python -m laneswap.examples.verify_installation --strict

# Run without printing results
python -m laneswap.examples.verify_installation --quiet
```

### System Check (`system_check.py`)

A comprehensive system check that tests all LaneSwap components.

#### Key Features

- **Component Testing**: Tests all LaneSwap components
- **Integration Testing**: Tests integration between components
- **Performance Testing**: Tests performance under load
- **Error Handling**: Tests error handling
- **Reporting**: Generates a detailed report

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.system_check

# Run with custom API URL
python -m laneswap.examples.system_check --api-url http://localhost:8000

# Run specific tests
python -m laneswap.examples.system_check --tests api,client,storage

# Run with verbose output
python -m laneswap.examples.system_check --verbose
```

### Simple Progress (`simple_progress.py`)

A minimal example of progress tracking.

#### Key Features

- **Basic Progress Tracking**: Shows the basics of progress tracking
- **Single Task**: Focuses on a single task
- **Linear Progress**: Demonstrates linear progress updates
- **Minimal Code**: Uses minimal code for clarity

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.simple_progress

# Run with custom API URL
python -m laneswap.examples.simple_progress --api-url http://localhost:8000

# Run with custom task name
python -m laneswap.examples.simple_progress --task-name "Custom Task"

# Run with custom total steps
python -m laneswap.examples.simple_progress --total-steps 200
```

### Configuration Example (`config_example.py`)

Demonstrates how to configure LaneSwap programmatically.

#### Key Features

- **Programmatic Configuration**: Shows how to configure LaneSwap in code
- **Environment Variables**: Demonstrates loading configuration from environment variables
- **Configuration File**: Shows loading configuration from a file
- **Default Values**: Explains default configuration values
- **Validation**: Demonstrates configuration validation

#### Usage Example

```bash
# Run with default settings
python -m laneswap.examples.config_example

# Run with custom configuration file
python -m laneswap.examples.config_example --config-file config.json

# Run with environment variables
LANESWAP_API_PORT=9000 LANESWAP_CHECK_INTERVAL=15 python -m laneswap.examples.config_example
```

### CLI Example (`cli_example.sh`)

A shell script demonstrating how to use the LaneSwap CLI.

#### Key Features

- **CLI Commands**: Shows all available CLI commands
- **Service Management**: Demonstrates service management commands
- **Heartbeat Sending**: Shows how to send heartbeats via CLI
- **Progress Tracking**: Demonstrates progress tracking via CLI
- **System Validation**: Shows how to validate the system

#### Usage Example

```bash
# Run the entire example
bash laneswap/examples/cli_example.sh

# Run specific sections
bash laneswap/examples/cli_example.sh services
bash laneswap/examples/cli_example.sh heartbeats
bash laneswap/examples/cli_example.sh progress
```

## Running the Examples

Most examples can be run directly as Python modules:

```bash
# Run an example
python -m laneswap.examples.<example_name>

# Get help for an example
python -m laneswap.examples.<example_name> --help
```

Some examples require additional setup:

1. **Discord Webhook Example**: Requires a Discord webhook URL
2. **MongoDB Examples**: Require a MongoDB instance
3. **API Server Examples**: Require the API server to be running

## Example Dependencies

The examples have the following dependencies:

- **Core LaneSwap Library**: All examples depend on the core library
- **FastAPI and Uvicorn**: Required for API server examples
- **Motor**: Required for MongoDB examples
- **Aiohttp**: Required for client examples
- **Tabulate**: Required for terminal monitor examples

## Best Practices

When using the examples as a reference for your own code, keep these best practices in mind:

1. **Error Handling**: Always implement proper error handling
2. **Resource Cleanup**: Close connections and clean up resources
3. **Configuration**: Use environment variables or configuration files for settings
4. **Logging**: Configure logging for better debugging
5. **Async/Await**: Use async/await correctly for asynchronous code
6. **Context Managers**: Use context managers for resource management
7. **Type Hints**: Use type hints for better code quality
8. **Documentation**: Document your code with docstrings
9. **Testing**: Write tests for your code
10. **Security**: Use HTTPS in production and handle sensitive data securely 