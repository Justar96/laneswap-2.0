"""
LaneSwap Validator Module

This module provides validation functions to ensure that LaneSwap is properly configured
and all required dependencies are available before starting services.
"""

import importlib
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laneswap.validator")

class ValidationWarning(Warning):
    """Warning raised for non-critical validation issues."""
    pass

class ValidationError(Exception):
    """Exception raised for critical validation issues."""
    pass

def check_dependency(module_name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a dependency is installed and can be imported.

    Args:
        module_name: Name of the module to check

    Returns:
        Tuple of (success, error_message)
    """
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error importing {module_name}: {str(e)}"

def check_core_dependencies() -> List[Tuple[str, bool, Optional[str]]]:
    """
    Check if all core dependencies are installed.

    Returns:
        List of tuples (module_name, success, error_message)
    """
    core_dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "motor",
        "aiohttp",
    ]

    results = []
    for dep in core_dependencies:
        success, error = check_dependency(dep)
        results.append((dep, success, error))

    return results

def check_terminal_monitor_dependencies() -> List[Tuple[str, bool, Optional[str]]]:
    """
    Check if all terminal monitor dependencies are installed.

    Returns:
        List of tuples (module_name, success, error_message)
    """
    terminal_monitor_dependencies = [
        "dateutil",
    ]

    results = []
    for dep in terminal_monitor_dependencies:
        success, error = check_dependency(dep)
        results.append((dep, success, error))

    return results

def check_terminal_monitor_files() -> Tuple[bool, Any]:
    """
    Check if terminal monitor files exist.

    Returns:
        Tuple of (success, results)
        where results is either a list of (file, exists, path) tuples or an error message
    """
    try:
        # Get the base directory of the laneswap package
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

def validate_system(check_terminal_monitor: bool =
    True, raise_on_error: bool = False) -> Dict[str, Any]:
    """
    Validate the LaneSwap system configuration.

    Args:
        check_terminal_monitor: Whether to check terminal monitor dependencies and files
        raise_on_error: Whether to raise an exception on critical validation errors

    Returns:
        Dictionary with validation results

    Raises:
        ValidationError: If raise_on_error is True and critical validation errors are found
    """
    validation_results = {
        "core_dependencies": {
            "status": "ok",
            "details": [],
            "missing": []
        },
        "terminal_monitor_dependencies": {
            "status": "ok",
            "details": [],
            "missing": []
        },
        "terminal_monitor_files": {
            "status": "ok",
            "details": [],
            "missing": []
        },
        "overall_status": "ok"
    }

    # Check core dependencies
    core_results = check_core_dependencies()
    validation_results["core_dependencies"]["details"] = core_results

    missing_core = [dep for dep, success, _ in core_results if not success]
    if missing_core:
        validation_results["core_dependencies"]["status"] = "error"
        validation_results["core_dependencies"]["missing"] = missing_core
        validation_results["overall_status"] = "error"

        error_msg = f"Missing core dependencies: {', '.join(missing_core)}"
        logger.error(error_msg)
        if raise_on_error:
            raise ValidationError(error_msg)

    # Check terminal monitor dependencies if requested
    if check_terminal_monitor:
        terminal_monitor_results = check_terminal_monitor_dependencies()
        validation_results["terminal_monitor_dependencies"]["details"] = terminal_monitor_results

        missing_terminal = [dep for dep, success, _ in terminal_monitor_results if not success]
        if missing_terminal:
            validation_results["terminal_monitor_dependencies"]["status"] = "warning"
            validation_results["terminal_monitor_dependencies"]["missing"] = missing_terminal

            if validation_results["overall_status"] != "error":
                validation_results["overall_status"] = "warning"

            warning_msg = f"Missing terminal monitor dependencies: {', '.join(missing_terminal)}"
            logger.warning(warning_msg)
            warnings.warn(warning_msg, ValidationWarning)

        # Check terminal monitor files
        files_success, files_results = check_terminal_monitor_files()

        if files_success:
            validation_results["terminal_monitor_files"]["details"] = files_results
            missing_files = [file for file, exists, _ in files_results if not exists]

            if missing_files:
                validation_results["terminal_monitor_files"]["status"] = "warning"
                validation_results["terminal_monitor_files"]["missing"] = missing_files

                if validation_results["overall_status"] != "error":
                    validation_results["overall_status"] = "warning"

                warning_msg = f"Missing terminal monitor files: {', '.join(missing_files)}"
                logger.warning(warning_msg)
                warnings.warn(warning_msg, ValidationWarning)
        else:
            validation_results["terminal_monitor_files"]["status"] = "warning"
            validation_results["terminal_monitor_files"]["error"] = str(files_results)

            if validation_results["overall_status"] != "error":
                validation_results["overall_status"] = "warning"

            warning_msg = f"Could not check terminal monitor files: {files_results}"
            logger.warning(warning_msg)
            warnings.warn(warning_msg, ValidationWarning)

    # Log overall status
    if validation_results["overall_status"] == "ok":
        logger.info("LaneSwap validation successful: All dependencies and files are available.")
    elif validation_results["overall_status"] == "warning":
        logger.warning("LaneSwap validation completed with warnings. Some features may not work correctly.")
    else:
        logger.error("LaneSwap validation failed. The system may not function correctly.")

    return validation_results

def print_validation_results(results: Dict[str, Any]) -> None:
    """
    Print validation results in a human-readable format.

    Args:
        results: Validation results from validate_system()
    """
    # Define ANSI color codes for terminal output
    GREEN = '\033[92m' if sys.platform != 'win32' else ''
    YELLOW = '\033[93m' if sys.platform != 'win32' else ''
    RED = '\033[91m' if sys.platform != 'win32' else ''
    RESET = '\033[0m' if sys.platform != 'win32' else ''
    BOLD = '\033[1m' if sys.platform != 'win32' else ''

    status_colors = {
        "ok": GREEN,
        "warning": YELLOW,
        "error": RED
    }

    print(f"\n{BOLD}LaneSwap System Validation{RESET}\n")

    # Print overall status
    overall_color = status_colors.get(results["overall_status"], "")
    print(f"Overall Status: {overall_color}{results['overall_status'].upper()}{RESET}")

    # Print core dependencies
    core_color = status_colors.get(results["core_dependencies"]["status"], "")
    print(f"\n{BOLD}Core Dependencies:{RESET} {core_color}{results['core_dependencies']['status'].upper()}{RESET}")

    if results["core_dependencies"]["missing"]:
        print(f"  Missing: {', '.join(results['core_dependencies']['missing'])}")
        print(f"  {YELLOW}Install with: pip install {' '.join(results['core_dependencies']['missing'])}{RESET}")

    # Print terminal monitor dependencies if checked
    if "terminal_monitor_dependencies" in results and results["terminal_monitor_dependencies"]["details"]:
        terminal_color = status_colors.get(results["terminal_monitor_dependencies"]["status"], "")
        print(f"\n{BOLD}Terminal Monitor Dependencies:{RESET} {terminal_color}{results['terminal_monitor_dependencies']['status'].upper()}{RESET}")

        if results["terminal_monitor_dependencies"]["missing"]:
            print(f"  Missing: {', '.join(results['terminal_monitor_dependencies']['missing'])}")
            print(f"  {YELLOW}Install with: pip install {' '.join(results['terminal_monitor_dependencies']['missing'])}{RESET}")

    # Print terminal monitor files if checked
    if "terminal_monitor_files" in results and results["terminal_monitor_files"].get("details"):
        files_color = status_colors.get(results["terminal_monitor_files"]["status"], "")
        print(f"\n{BOLD}Terminal Monitor Files:{RESET} {files_color}{results['terminal_monitor_files']['status'].upper()}{RESET}")

        if results["terminal_monitor_files"].get("missing"):
            print(f"  Missing: {', '.join(results['terminal_monitor_files']['missing'])}")
            print(f"  {YELLOW}Try reinstalling LaneSwap to restore missing files.{RESET}")

        if results["terminal_monitor_files"].get("error"):
            print(f"  Error: {results['terminal_monitor_files']['error']}")

    # Print recommendation
    if results["overall_status"] != "ok":
        print(f"\n{YELLOW}Recommendation:{RESET}")
        if results["overall_status"] == "error":
            print(f"  {RED}Critical issues found. LaneSwap may not function correctly.{RESET}")
            print(f"  Run: {BOLD}pip install -U laneswap[all]{RESET} to install all dependencies.")
        else:
            print(f"  {YELLOW}Non-critical issues found. Some features may not work correctly.{RESET}")
            print(f"  Run: {BOLD}pip install -U laneswap[all]{RESET} to install all dependencies.")
    else:
        print(f"\n{GREEN}All checks passed. LaneSwap is properly configured.{RESET}")

    print()  # Add a blank line at the end

def run_validation(check_terminal_monitor: bool =
    True, print_results: bool = True) -> Dict[str, Any]:
    """
    Run system validation and optionally print results.

    Args:
        check_terminal_monitor: Whether to check terminal monitor dependencies and files
        print_results: Whether to print validation results to stdout

    Returns:
        Dictionary with validation results
    """
    results = validate_system(check_terminal_monitor=check_terminal_monitor, raise_on_error=False)

    if print_results:
        print_validation_results(results)

    return results

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run validation when module is executed directly
    run_validation(check_terminal_monitor=True, print_results=True)
