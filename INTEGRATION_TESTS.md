# Running Integration Tests

This document provides instructions on how to run the integration tests for the LaneSwap project.

## Prerequisites

1. MongoDB instance (local or remote)
2. Python 3.8 or higher
3. All project dependencies installed

## Test Types

The integration tests are divided into three categories:

1. **MongoDB Integration Tests**: Tests the integration with MongoDB
2. **Discord Integration Tests**: Tests the integration with Discord webhooks
3. **Client Integration Tests**: Tests the integration between the LaneSwap client and API server

## Environment Variables

The following environment variables are used by the integration tests:

- `MONGODB_URI`: MongoDB connection string (required for all integration tests)
- `DISCORD_WEBHOOK_URL`: Discord webhook URL (required for Discord integration tests)

## Running the Tests

### MongoDB Integration Tests

```bash
# Set the MongoDB URI environment variable
export MONGODB_URI="mongodb://localhost:27017/laneswap_test"  # Linux/macOS
set MONGODB_URI=mongodb://localhost:27017/laneswap_test       # Windows Command Prompt
$env:MONGODB_URI="mongodb://localhost:27017/laneswap_test"    # Windows PowerShell

# Run the test
python -m pytest tests/integration/test_full_flow.py::test_full_flow_with_mongodb -v
```

### Discord Integration Tests

```bash
# Set the environment variables
export MONGODB_URI="mongodb://localhost:27017/laneswap_test"  # Linux/macOS
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

set MONGODB_URI=mongodb://localhost:27017/laneswap_test       # Windows Command Prompt
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

$env:MONGODB_URI="mongodb://localhost:27017/laneswap_test"    # Windows PowerShell
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Run the test
python -m pytest tests/integration/test_full_flow.py::test_full_flow_with_discord -v
```

### Client Integration Tests

The client integration test requires both a MongoDB instance and a running API server. We've provided a helper script to simplify this process:

#### Using the Helper Script

```bash
# Linux/macOS
./run_client_integration_test.py --mongodb-uri="mongodb://localhost:27017/laneswap_test"

# Windows
run_client_integration_test.bat mongodb://localhost:27017/laneswap_test
```

#### Manual Setup

If you prefer to run the test manually:

1. Start the API server:
   ```bash
   # In terminal 1
   export MONGODB_URI="mongodb://localhost:27017/laneswap_test"  # Linux/macOS
   set MONGODB_URI=mongodb://localhost:27017/laneswap_test       # Windows Command Prompt
   $env:MONGODB_URI="mongodb://localhost:27017/laneswap_test"    # Windows PowerShell
   
   python -m laneswap.api.main
   ```

2. Run the test:
   ```bash
   # In terminal 2
   export MONGODB_URI="mongodb://localhost:27017/laneswap_test"  # Linux/macOS
   set MONGODB_URI=mongodb://localhost:27017/laneswap_test       # Windows Command Prompt
   $env:MONGODB_URI="mongodb://localhost:27017/laneswap_test"    # Windows PowerShell
   
   python -m pytest tests/integration/test_full_flow.py::test_client_integration -v
   ```

## Troubleshooting

### MongoDB Connection Issues

- Ensure MongoDB is running and accessible
- Check that the connection string is correct
- Verify network connectivity to the MongoDB server

### API Server Issues

- Ensure the API server is running on localhost:8000
- Check the API server logs for errors
- Verify that the MongoDB URI is correctly set for the API server

### Discord Webhook Issues

- Ensure the webhook URL is valid and active
- Check Discord's rate limits
- Verify network connectivity to Discord's servers 