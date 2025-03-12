#!/usr/bin/env python
"""
Test module for LaneSwap CLI functionality.

This module tests:
1. Service registration via CLI
2. Sending heartbeats via CLI
3. Service listing via CLI
4. Discord webhook configuration via CLI
5. Service daemon functionality
"""

import asyncio
import argparse
import logging
import sys
import time
import subprocess
import json
import os
import signal
import tempfile
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cli_test")


def run_cli_command(command, check=True):
    """
    Run a LaneSwap CLI command.
    
    Args:
        command: List of command arguments
        check: Whether to check the return code
        
    Returns:
        tuple: (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "laneswap.cli.main"] + command,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def test_service_registration():
    """Test service registration via CLI."""
    print("\n=== Testing Service Registration ===\n")
    
    # Register a service
    service_name = f"CLI Test Service {int(time.time())}"
    metadata = json.dumps({"test": True, "type": "cli_test", "timestamp": time.time()})
    
    print(f"Registering service: {service_name}")
    success, stdout, stderr = run_cli_command([
        "service", "register",
        "--name", service_name,
        "--metadata", metadata
    ])
    
    if not success:
        print(f"❌ Service registration failed: {stderr}")
        return None
    
    print(f"✅ Service registration output:\n{stdout}")
    
    # Extract service ID from output
    service_id = None
    for line in stdout.splitlines():
        if "Service ID:" in line:
            service_id = line.split("Service ID:")[1].strip()
            break
    
    if not service_id:
        print("❌ Failed to extract service ID from output")
        return None
    
    print(f"✅ Extracted service ID: {service_id}")
    return service_id


def test_heartbeat(service_id):
    """Test sending heartbeats via CLI."""
    print("\n=== Testing Heartbeat Sending ===\n")
    
    if not service_id:
        print("❌ Cannot test heartbeat without service ID")
        return False
    
    # Send heartbeats with different statuses
    statuses = [
        ("healthy", "Service is running normally"),
        ("warning", "High resource usage detected"),
        ("error", "Service encountered an error"),
        ("warning", "Service recovering from error"),
        ("healthy", "Service has recovered")
    ]
    
    for status, message in statuses:
        print(f"Sending {status} heartbeat: {message}")
        success, stdout, stderr = run_cli_command([
            "service", "heartbeat",
            "--id", service_id,
            "--status", status,
            "--message", message,
            "--metadata", json.dumps({"timestamp": time.time(), "test": True})
        ])
        
        if not success:
            print(f"❌ Failed to send {status} heartbeat: {stderr}")
            return False
        
        print(f"✅ Heartbeat sent successfully:\n{stdout}")
        time.sleep(1)  # Brief pause between heartbeats
    
    print("✅ All heartbeat tests passed")
    return True


def test_service_listing(service_id):
    """Test service listing via CLI."""
    print("\n=== Testing Service Listing ===\n")
    
    if not service_id:
        print("❌ Cannot test service listing without service ID")
        return False
    
    # List all services
    print("Listing all services")
    success, stdout, stderr = run_cli_command(["service", "list"])
    
    if not success:
        print(f"❌ Failed to list services: {stderr}")
        return False
    
    print(f"✅ Service list output:\n{stdout}")
    
    # Get specific service details
    print(f"Getting details for service {service_id}")
    success, stdout, stderr = run_cli_command(["service", "list", "--id", service_id])
    
    if not success:
        print(f"❌ Failed to get service details: {stderr}")
        return False
    
    print(f"✅ Service details output:\n{stdout}")
    
    # Get service details in JSON format
    print(f"Getting service details in JSON format")
    success, stdout, stderr = run_cli_command(["service", "list", "--id", service_id, "--format", "json"])
    
    if not success:
        print(f"❌ Failed to get service details in JSON format: {stderr}")
        return False
    
    try:
        service_data = json.loads(stdout)
        print(f"✅ Service JSON data parsed successfully")
    except json.JSONDecodeError:
        print(f"❌ Failed to parse service JSON data")
        return False
    
    print("✅ All service listing tests passed")
    return True


def test_webhook_configuration(service_id, webhook_url):
    """Test Discord webhook configuration via CLI."""
    print("\n=== Testing Discord Webhook Configuration ===\n")
    
    if not service_id:
        print("❌ Cannot test webhook configuration without service ID")
        return False
    
    if not webhook_url:
        print("⚠️ Skipping webhook configuration test (no webhook URL provided)")
        return True
    
    # Configure webhook for the service
    print(f"Configuring webhook for service {service_id}")
    success, stdout, stderr = run_cli_command([
        "service", "webhook",
        "--id", service_id,
        "--webhook-url", webhook_url,
        "--levels", "info,warning,error"
    ])
    
    if not success:
        print(f"❌ Failed to configure webhook: {stderr}")
        return False
    
    print(f"✅ Webhook configuration output:\n{stdout}")
    
    # List Discord webhooks
    print("Listing Discord webhooks")
    success, stdout, stderr = run_cli_command(["discord", "list"])
    
    if not success:
        print(f"❌ Failed to list webhooks: {stderr}")
        return False
    
    print(f"✅ Webhook list output:\n{stdout}")
    
    # Test the webhook
    print("Testing webhook notification")
    success, stdout, stderr = run_cli_command([
        "discord", "test",
        "--service-id", service_id,
        "--level", "info",
        "--message", "This is a test notification from CLI test"
    ])
    
    if not success:
        print(f"❌ Failed to test webhook: {stderr}")
        return False
    
    print(f"✅ Webhook test output:\n{stdout}")
    
    print("✅ All webhook configuration tests passed")
    return True


def test_daemon_functionality(service_id):
    """Test service daemon functionality."""
    print("\n=== Testing Service Daemon Functionality ===\n")
    
    if not service_id:
        print("❌ Cannot test daemon functionality without service ID")
        return False
    
    # Start the daemon process
    print("Starting service daemon (will run for 10 seconds)")
    daemon_process = subprocess.Popen(
        ["python", "-m", "laneswap.cli.main", "service", "daemon",
         "--id", service_id,
         "--interval", "2",
         "--status", "healthy",
         "--message", "Daemon test heartbeat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Let the daemon run for a few seconds
    try:
        time.sleep(10)
    finally:
        # Terminate the daemon
        print("Terminating daemon process")
        daemon_process.send_signal(signal.SIGINT)
        try:
            daemon_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            daemon_process.kill()
    
    stdout, stderr = daemon_process.communicate()
    
    if daemon_process.returncode != 0 and daemon_process.returncode != -2:  # -2 is for SIGINT
        print(f"❌ Daemon process exited with error: {stderr}")
        return False
    
    print(f"✅ Daemon process output:\n{stdout}")
    
    # Check that heartbeats were sent
    print("Checking service status after daemon run")
    success, stdout, stderr = run_cli_command(["service", "list", "--id", service_id])
    
    if not success:
        print(f"❌ Failed to get service status: {stderr}")
        return False
    
    print(f"✅ Service status after daemon run:\n{stdout}")
    
    print("✅ Daemon functionality test passed")
    return True


def main():
    """Main entry point for the CLI tests."""
    parser = argparse.ArgumentParser(description="Test LaneSwap CLI functionality")
    parser.add_argument("--webhook-url", help="Discord webhook URL for testing notifications")
    parser.add_argument("--skip-daemon", action="store_true", help="Skip daemon functionality test")
    
    try:
        args = parser.parse_args()
        
        print("Testing LaneSwap CLI functionality...")
        
        # Test service registration
        service_id = test_service_registration()
        if not service_id:
            print("\n❌ CLI tests failed at service registration")
            return 1
        
        # Test heartbeat sending
        if not test_heartbeat(service_id):
            print("\n❌ CLI tests failed at heartbeat sending")
            return 1
        
        # Test service listing
        if not test_service_listing(service_id):
            print("\n❌ CLI tests failed at service listing")
            return 1
        
        # Test webhook configuration if URL is provided
        if args.webhook_url:
            if not test_webhook_configuration(service_id, args.webhook_url):
                print("\n❌ CLI tests failed at webhook configuration")
                return 1
        
        # Test daemon functionality
        if not args.skip_daemon:
            if not test_daemon_functionality(service_id):
                print("\n❌ CLI tests failed at daemon functionality")
                return 1
        
        print("\n✅ All CLI tests passed!")
        return 0
    except SystemExit as e:
        # Handle the case where argparse exits due to --help or error
        if e.code == 0:  # --help was called
            return 0
        print("\n❌ Error parsing arguments")
        return 1
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 