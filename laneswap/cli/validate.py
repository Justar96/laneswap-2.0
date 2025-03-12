#!/usr/bin/env python
"""
LaneSwap Validation CLI

This module provides a command-line interface for validating the LaneSwap installation.
"""

import argparse
import logging
import sys
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("laneswap.cli.validate")

def validate_command(args: argparse.Namespace) -> int:
    """
    Run the validation command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        from ..core.validator import run_validation
        
        # Run validation
        results = run_validation(
            check_terminal_monitor=not args.no_terminal_monitor,
            print_results=not args.quiet
        )
        
        # Return exit code based on validation results
        if results["overall_status"] == "error":
            return 1
        elif results["overall_status"] == "warning" and args.strict:
            return 2
        else:
            return 0
    except ImportError:
        logger.error("Validator module not found. Make sure LaneSwap is installed correctly.")
        return 1
    except Exception as e:
        logger.error(f"Error running validation: {str(e)}")
        return 1

def setup_parser(parser: argparse.ArgumentParser) -> None:
    """
    Set up the argument parser for the validate command.
    
    Args:
        parser: Argument parser to set up
    """
    parser.add_argument(
        "--no-terminal-monitor",
        action="store_true",
        help="Skip terminal monitor validation"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Don't print validation results"
    )
    parser.set_defaults(func=validate_command)

def main() -> int:
    """
    Main entry point for the validate command.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Validate LaneSwap installation")
    setup_parser(parser)
    args = parser.parse_args()
    
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main()) 