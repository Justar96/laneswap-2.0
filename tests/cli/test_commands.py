"""
Tests for the CLI commands.
"""

import pytest
import subprocess
import sys
import json
import time
import os
from pathlib import Path
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import socket
import logging

from laneswap.cli.commands import main
from laneswap.cli.utils import run_cli_command
from laneswap.core.heartbeat import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Ensure required environment variables are set
MONGODB_URI = os.environ.get('LANESWAP_MONGODB_URI')
DISCORD_WEBHOOK = os.environ.get('LANESWAP_DISCORD_WEBHOOK')

if not MONGODB_URI:
    pytest.skip("MongoDB URI not provided", allow_module_level=True)

async def run_cli_command(command):
    """Run a CLI command and return its output."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ  # Pass current environment variables
    )
    stdout, stderr = await process.communicate()
    return process.returncode == 0, stdout.decode(), stderr.decode()


def find_free_port():
    """Find a free port to use for the API server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

async def start_api_server():
    """Start the API server and wait for it to be ready."""
    print("\nStarting API server...")
    
    # Find a free port
    port = find_free_port()
    os.environ['PORT'] = str(port)
    
    # Ensure MongoDB URI is set
    if not os.environ.get('LANESWAP_MONGODB_URI'):
        print("MongoDB URI not set in environment variables")
        return None
        
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "laneswap.api.main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ  # Pass current environment variables
    )
    
    # Wait for server to start
    await asyncio.sleep(10)
    
    # Check if process is still running
    if process.returncode is not None:
        stdout, stderr = await process.communicate()
        print(f"\nAPI server failed to start!")
        print(f"Exit code: {process.returncode}")
        print(f"stdout: {stdout.decode()}")
        print(f"stderr: {stderr.decode()}")
        return None
        
    print(f"API server started successfully on port {port}!")
    return process, port


async def stop_api_server(process):
    """Stop the API server gracefully."""
    if process:
        try:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        except ProcessLookupError:
            pass  # Process already terminated


@pytest.fixture
async def api_server():
    """Fixture to start and stop the API server."""
    result = await start_api_server()
    if result is None:
        pytest.fail("API server failed to start")
    process, port = result
    yield process, port
    await stop_api_server(process)


async def test_cli_help():
    """Test the CLI help command."""
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "--help"
    ])
    assert success
    assert "Usage:" in stdout
    assert "LaneSwap CLI commands" in stdout


async def test_service_command_help():
    """Test the service command help."""
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "--help"
    ])
    assert success
    assert "Usage:" in stdout
    assert "Manage LaneSwap services" in stdout


async def test_service_registration(api_server):
    """Test service registration via CLI."""
    process, port = api_server
    
    # Register a service
    service_name = f"CLI Test Service {int(time.time())}"
    metadata = json.dumps({"test": True, "type": "cli_test", "timestamp": time.time()})

    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "register",
        "--name", service_name,
        "--metadata", metadata,
        "--api-url", f"http://localhost:{port}/api"
    ])
    
    assert success, f"Failed to register service: {stderr}"
    assert "Service registered successfully!" in stdout


async def test_heartbeat(api_server):
    """Test sending a heartbeat via CLI."""
    process, port = api_server
    
    # First register a new service for this test
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "register",
        "--name", "Test Heartbeat Service",
        "--metadata", json.dumps({"test": True}),
        "--api-url", f"http://localhost:{port}/api"
    ])
    assert success, f"Failed to register service: {stderr}"

    # Extract the service ID
    service_id = stdout.split("Service ID:")[1].split("\n")[0].strip()

    # Verify service exists
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "list",
        "--id", service_id,
        "--api-url", f"http://localhost:{port}/api"
    ])
    assert success, f"Service not found: {stderr}"
    assert "Service Details for" in stdout, "Service details not found in output"

    # Send the heartbeat
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "heartbeat",
        "--id", service_id,
        "--status", "healthy",
        "--message", "Test heartbeat",
        "--api-url", f"http://localhost:{port}/api"
    ])

    assert success, f"Failed to send heartbeat: {stderr}"
    assert "Heartbeat sent successfully" in stdout


async def test_service_listing(api_server):
    """Test listing services via CLI."""
    process, port = api_server
    
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "list",
        "--api-url", f"http://localhost:{port}/api"
    ])
    
    assert success, f"Failed to list services: {stderr}"
    assert "Total services:" in stdout


@pytest.mark.skipif(
    not DISCORD_WEBHOOK,
    reason="Discord webhook URL not provided"
)
async def test_webhook_configuration(api_server):
    """Test configuring webhooks via CLI."""
    process, port = api_server
    webhook_url = DISCORD_WEBHOOK

    # First register a service
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "register",
        "--name", "Test Service",
        "--metadata", json.dumps({"test": True}),
        "--api-url", f"http://localhost:{port}/api"
    ])
    assert success, f"Failed to register service: {stderr}"

    # Extract the service ID
    service_id = stdout.split("Service ID:")[1].split("\n")[0].strip()

    # Verify service exists
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "list",
        "--id", service_id,
        "--api-url", f"http://localhost:{port}/api"
    ])
    assert success, f"Service not found: {stderr}"
    assert "Service Details for" in stdout, "Service details not found in output"

    # Now configure the webhook
    success, stdout, stderr = await run_cli_command([
        "python", "-m", "laneswap.cli.main",
        "service", "webhook",
        "--id", service_id,
        "--webhook-url", webhook_url,
        "--username", "Test Bot",
        "--levels", "info,warning,error",
        "--api-url", f"http://localhost:{port}/api"
    ])

    assert success, f"Failed to configure webhook: {stderr}"
    assert "Discord webhook configured for service" in stdout
    assert "Test notification sent successfully" in stdout 