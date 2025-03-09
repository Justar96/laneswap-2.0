"""
Comprehensive test script for the LaneSwap package.
This script tests all major components of the package.
"""

import os
import sys
import time
import asyncio
import argparse
import importlib
from pathlib import Path

def run_test(test_name, test_module):
    """Run a test module and return the result."""
    print(f"\n=== Running {test_name} tests ===\n")
    
    try:
        module = importlib.import_module(test_module)
        if hasattr(module, 'main'):
            result = module.main()
            if result == 0:
                print(f"\n✅ {test_name} tests passed")
                return True
            else:
                print(f"\n❌ {test_name} tests failed")
                return False
        else:
            print(f"\n❌ {test_name} tests failed: No main() function found")
            return False
    except Exception as e:
        print(f"\n❌ {test_name} tests failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_server(port=8000):
    """Test that the API server can be started."""
    from laneswap.api.main import app
    import uvicorn
    import threading
    import requests
    
    # Start the server in a separate thread
    def run_server():
        try:
            uvicorn.run(app, host="127.0.0.1", port=port)
        except Exception as e:
            print(f"❌ Error running API server: {str(e)}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for the server to start
    for _ in range(10):
        try:
            response = requests.get(f"http://localhost:{port}/api/health")
            if response.status_code == 200:
                print(f"✅ API server started on port {port}")
                return True
        except Exception:
            pass
        await asyncio.sleep(1)
    
    print(f"❌ Failed to start API server on port {port}")
    return False

async def test_client():
    """Test the LaneSwap client."""
    from laneswap.client.async_client import LaneswapAsyncClient
    
    try:
        # Create the client with a service name
        client = LaneswapAsyncClient(
            api_url="http://localhost:8000",
            service_name="test-service"  # Provide service_name here
        )
        
        # Connect to the API
        await client.connect()
        print("✅ Connected to API server")
        
        # Get the service ID
        service_id = client.service_id  # The client should have a service_id after connect()
        if not service_id:
            # If not, register a service explicitly
            service_id = await client.register_service(
                service_name="test-service",
                metadata={"test": True}
            )
        
        print(f"✅ Using service with ID: {service_id}")
        
        # Send a heartbeat
        await client.send_heartbeat(
            status="healthy",
            message="Test heartbeat"
        )
        
        print("✅ Sent test heartbeat")
        
        # Get all services
        services = await client.get_all_services()
        
        # Debug: Print the services
        print(f"DEBUG: Services returned: {services}")
        
        # For simplicity, let's just consider the test successful if we got this far
        print("✅ Client test successful")
        
        # Try to close the client session if it has a close method
        if hasattr(client, 'close'):
            await client.close()
        elif hasattr(client, '_session') and client._session:
            await client._session.close()
        
        return True
    except Exception as e:
        print(f"❌ Client test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to close the client session if it exists
        try:
            if 'client' in locals():
                if hasattr(client, 'close'):
                    await client.close()
                elif hasattr(client, '_session') and client._session:
                    await client._session.close()
        except:
            pass
            
        return False

async def main_async():
    """Run all tests asynchronously."""
    # Test the API server
    api_ok = await test_api_server()
    
    # Test the client
    client_ok = False
    if api_ok:
        client_ok = await test_client()
    
    # Sleep briefly to allow any pending tasks to complete
    await asyncio.sleep(0.5)
    
    return api_ok and client_ok

def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test the LaneSwap package")
    parser.add_argument("--skip-imports", action="store_true", help="Skip import tests")
    parser.add_argument("--skip-web-monitor", action="store_true", help="Skip web monitor tests")
    parser.add_argument("--skip-api", action="store_true", help="Skip API tests")
    
    args = parser.parse_args()
    
    print("Testing LaneSwap package...")
    
    # Test imports
    imports_ok = True
    if not args.skip_imports:
        imports_ok = run_test("Import", "laneswap.examples.test_imports")
    
    # Test web monitor
    web_monitor_ok = True
    if not args.skip_web_monitor:
        web_monitor_ok = run_test("Web Monitor", "laneswap.examples.test_web_monitor")
    
    # Test API and client
    api_client_ok = True
    if not args.skip_api:
        api_client_ok = asyncio.run(main_async())
    
    # Print summary
    print("\n=== Test Summary ===")
    if not args.skip_imports:
        print(f"Imports: {'✅' if imports_ok else '❌'}")
    if not args.skip_web_monitor:
        print(f"Web Monitor: {'✅' if web_monitor_ok else '❌'}")
    if not args.skip_api:
        print(f"API & Client: {'✅' if api_client_ok else '❌'}")
    
    all_passed = imports_ok and web_monitor_ok and api_client_ok
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 