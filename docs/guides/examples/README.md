# LaneSwap Examples

This directory contains example code demonstrating how to use various components of the LaneSwap system. These examples are designed to help you understand how to integrate with LaneSwap and build your own applications using the LaneSwap framework.

## Available Examples

### Client Basic Usage (`client_basic_usage.py`)

This example demonstrates how to initialize and use the LaneSwap client to interact with a LaneSwap network. It covers:

- Connecting to a LaneSwap network
- Registering a new service
- Getting a list of available services
- Sending messages to services
- Subscribing to events from services
- Proper cleanup and disconnection

**Usage:**
```bash
python client_basic_usage.py
```

### Custom Adapter (`custom_adapter.py`)

This example shows how to create a custom adapter for LaneSwap that can connect to an external system and translate between LaneSwap's protocol and the external system's protocol. It covers:

- Creating a custom adapter class
- Implementing message translation between systems
- Handling events from the external system
- Registering the adapter as a service in LaneSwap
- Processing messages and events

**Usage:**
```bash
python custom_adapter.py
```

### Terminal Interface (`terminal_interface.py`)

This example demonstrates how to create a custom terminal interface for interacting with a LaneSwap network. It covers:

- Creating a custom terminal application
- Defining and registering commands
- Handling command execution
- Formatting command results
- Monitoring events from services

**Usage:**
```bash
python terminal_interface.py --api-url http://localhost:8000 --api-key your-api-key
```

## Prerequisites

Before running these examples, make sure you have:

1. Installed the LaneSwap package and its dependencies
2. A running LaneSwap API server (or appropriate mock)
3. Python 3.7 or higher

## Installation

To install the required dependencies:

```bash
pip install laneswap
```

## Configuration

Most examples accept configuration parameters such as API URL and API key. You can either:

1. Modify the example code directly to use your specific configuration
2. Pass configuration parameters via command-line arguments (where supported)

## Additional Resources

For more information about LaneSwap, refer to:

- [LaneSwap Core Documentation](../../core/README.md)
- [LaneSwap API Documentation](../../api/README.md)
- [LaneSwap Client Documentation](../../client/README.md)
- [LaneSwap Terminal Documentation](../../terminal/README.md)
- [LaneSwap Adapters Documentation](../../adapters/README.md)

## Contributing

If you'd like to contribute additional examples, please follow these guidelines:

1. Create a new Python file with a descriptive name
2. Include detailed comments explaining the code
3. Add proper error handling and cleanup
4. Update this README to include your new example
5. Submit a pull request with your changes