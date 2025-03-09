#!/usr/bin/env python
"""
Test script to verify that all required modules can be imported correctly.
This helps identify any missing dependencies or import issues.
"""

import sys
import importlib
import traceback

def test_import(module_name, skip_errors=False):
    """Test importing a module and print the result."""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {str(e)}")
        if not skip_errors:
            traceback.print_exc()
        return False

def main():
    """Test importing all required modules."""
    modules_to_test = [
        # Core modules
        "laneswap.core.heartbeat",
        "laneswap.core.config",
        "laneswap.core.exceptions",
        
        # Adapters
        "laneswap.adapters.mongodb",
        "laneswap.adapters.base",
        
        # API
        "laneswap.api.main",
        
        # Client
        "laneswap.client.async_client",
        
        # CLI
        "laneswap.cli.commands",
        
        # Examples
        "laneswap.examples.simple_service",
        "laneswap.examples.progress_service",
        "laneswap.examples.web_monitor.launch",
        "laneswap.examples.start_monitor",
    ]
    
    # Modules with known issues that we can skip detailed error reporting for
    known_issue_modules = []  # Empty now that we've fixed the config module
    
    success_count = 0
    for module in modules_to_test:
        skip_errors = module in known_issue_modules
        if test_import(module, skip_errors):
            success_count += 1
    
    print(f"\nImport test results: {success_count}/{len(modules_to_test)} modules imported successfully")
    
    # Don't fail the test if only known issue modules failed
    failed_modules = len(modules_to_test) - success_count
    if failed_modules > len(known_issue_modules):
        print("\n❌ Some imports failed.")
        return 1
    else:
        print("\n✅ All imports successful!")
        return 0

if __name__ == "__main__":
    main() 