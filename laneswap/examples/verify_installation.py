#!/usr/bin/env python
"""
LaneSwap Installation Verification Script

This script verifies that LaneSwap is installed correctly and all dependencies
are available. It checks for required modules and attempts to import key
components of the library.

Usage:
    python -m laneswap.examples.verify_installation
"""

import importlib
import platform
import sys
from pathlib import Path

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status, details=None):
    """Print a status message with color coding."""
    status_color = {
        'OK': GREEN,
        'WARNING': YELLOW,
        'ERROR': RED
    }.get(status, RESET)

    print(f"{message:<50} [{status_color}{status}{RESET}]")
    if details:
        print(f"  {details}")

def check_module(module_name):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def check_laneswap_components():
    """Check if key LaneSwap components can be imported."""
    components = [
        "laneswap.core.heartbeat",
        "laneswap.models.heartbeat",
        "laneswap.adapters.base",
        "laneswap.api.main",
        "laneswap.terminal.monitor"
    ]

    results = []
    for component in components:
        success, error = check_module(component)
        results.append((component, success, error))

    return results

def check_dependencies():
    """Check if all required dependencies are installed."""
    dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "motor",
        "aiohttp",
        "tabulate",
        "dateutil"
    ]

    results = []
    for dep in dependencies:
        success, error = check_module(dep)
        results.append((dep, success, error))

    return results

def check_terminal_monitor_files():
    """Check if terminal monitor files exist."""
    try:
        import laneswap
        base_dir = Path(laneswap.__file__).parent

        terminal_dir = base_dir / "terminal"

        required_files = [
            "__init__.py",
            "colors.py",
            "ascii_art.py",
            "monitor.py"
        ]

        results = []
        for file in required_files:
            file_path = terminal_dir / file
            exists = file_path.exists()
            results.append((file, exists, str(file_path) if exists else None))

        return True, results
    except Exception as e:
        return False, str(e)

def main():
    """Run the verification checks."""
    print(f"\n{BOLD}LaneSwap Installation Verification{RESET}\n")

    # Print system information
    print(f"{BOLD}System Information:{RESET}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Python executable: {sys.executable}")
    print()

    # Check LaneSwap version
    try:
        import laneswap
        print(f"{BOLD}LaneSwap Version:{RESET} {laneswap.__version__}")
    except (ImportError, AttributeError):
        print(f"{BOLD}LaneSwap Version:{RESET} {RED}Unable to determine{RESET}")
    print()

    # Check dependencies
    print(f"{BOLD}Checking Dependencies:{RESET}")
    dep_results = check_dependencies()
    all_deps_ok = True

    for dep, success, error in dep_results:
        if success:
            print_status(f"Dependency: {dep}", "OK")
        else:
            all_deps_ok = False
            print_status(f"Dependency: {dep}", "ERROR", f"Error: {error}")

    if not all_deps_ok:
        print(f"\n{YELLOW}Some dependencies are missing. Install them with:{RESET}")
        print("pip install pydantic fastapi uvicorn motor aiohttp tabulate dateutil")
    print()

    # Check LaneSwap components
    print(f"{BOLD}Checking LaneSwap Components:{RESET}")
    component_results = check_laneswap_components()
    all_components_ok = True

    for component, success, error in component_results:
        if success:
            print_status(f"Component: {component}", "OK")
        else:
            all_components_ok = False
            print_status(f"Component: {component}", "ERROR", f"Error: {error}")
    print()

    # Check terminal monitor files
    print(f"{BOLD}Checking Terminal Monitor Files:{RESET}")
    monitor_success, monitor_results = check_terminal_monitor_files()

    if monitor_success:
        all_files_ok = True
        for file, exists, path in monitor_results:
            if exists:
                print_status(f"File: {file}", "OK", f"Path: {path}")
            else:
                all_files_ok = False
                print_status(f"File: {file}", "ERROR", "File not found")

        if not all_files_ok:
            print(f"\n{YELLOW}Some terminal monitor files are missing. Try reinstalling LaneSwap.{RESET}")
    else:
        print_status("Terminal Monitor", "ERROR", f"Error: {monitor_results}")
    print()

    # Overall status
    print(f"{BOLD}Overall Status:{RESET}")
    if all_deps_ok and all_components_ok and monitor_success:
        print(f"{GREEN}LaneSwap is installed correctly and ready to use!{RESET}")
        print("\nYou can start the terminal monitor with:")
        print("  laneswap-term --api-url http://localhost:8000")
    else:
        print(f"{RED}There are issues with your LaneSwap installation.{RESET}")
        print("Please fix the errors above and try again.")
    print()

if __name__ == "__main__":
    main()
