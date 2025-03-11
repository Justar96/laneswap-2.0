# LaneSwap Test Suite

This directory contains test modules for the LaneSwap package, including tests for the Discord webhook and CLI functionality.

## Running All Tests

To run all tests, use the `test_all.py` script:

```bash
python -m laneswap.examples.test_all
```

### Command-line Options

- `--skip-imports`: Skip import tests
- `--skip-web-monitor`: Skip web monitor tests
- `--skip-api`: Skip API tests
- `--skip-system-flow`: Skip system flow tests
- `--skip-discord`: Skip Discord webhook tests
- `--skip-cli`: Skip CLI tests
- `--webhook-url`: Discord webhook URL for testing notifications
- `--web-monitor-port`: Port for web monitor tests (default: 8080)
- `--api-port`: Port for API server (default: 8000)

Example:

```bash
python -m laneswap.examples.test_all --webhook-url "https://discord.com/api/webhooks/your-webhook-url" --api-port 8001 --web-monitor-port 8081
```

## Individual Test Modules

### Discord Webhook Tests

To test the Discord webhook functionality specifically:

```bash
python -m laneswap.examples.test_discord --webhook-url "https://discord.com/api/webhooks/your-webhook-url"
```

This test:
1. Tests the Discord webhook adapter directly
2. Tests service-specific webhook configuration
3. Tests sending notifications with different levels
4. Tests status change notifications

### CLI Tests

To test the CLI functionality specifically:

```bash
python -m laneswap.examples.test_cli [--webhook-url "https://discord.com/api/webhooks/your-webhook-url"] [--skip-daemon]
```

This test:
1. Tests service registration via CLI
2. Tests sending heartbeats via CLI
3. Tests service listing via CLI
4. Tests Discord webhook configuration via CLI (if webhook URL is provided)
5. Tests service daemon functionality (can be skipped with `--skip-daemon`)

### Web Monitor Tests

To test the web monitor specifically:

```bash
python -m laneswap.examples.test_web_monitor [--port 8080] [--api-url "http://localhost:8000"]
```

### Import Tests

To test imports specifically:

```bash
python -m laneswap.examples.test_imports
```

## Continuous Integration

These tests can be integrated into a CI/CD pipeline. Here's an example GitHub Actions workflow:

```yaml
name: LaneSwap Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    - name: Run tests
      run: |
        python -m laneswap.examples.test_all --skip-discord
```

## Troubleshooting

If you encounter issues with the tests:

1. Make sure the API server is not already running on port 8000 (or the port specified with `--api-port`)
2. Check that the Discord webhook URL is valid (if testing Discord functionality)
3. Ensure all dependencies are installed
4. Check the logs for detailed error messages
5. If you get argument parsing errors, make sure you're using the correct command-line options for each test module

For more information, refer to the main LaneSwap documentation. 