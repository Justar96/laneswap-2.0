"""
CLI utility functions.
"""

import asyncio
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("laneswap.cli")

async def run_cli_command(
    command: List[str],
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    capture_output: bool = True
) -> Tuple[int, str, str]:
    """
    Run a CLI command asynchronously.

    Args:
        command: Command and arguments as a list
        env: Optional environment variables
        cwd: Optional working directory
        capture_output: Whether to capture stdout/stderr

    Returns:
        Tuple[int, str, str]: Return code, stdout, stderr
    """
    # Create environment with system environment as base
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            env=full_env,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None
        )

        # Wait for completion and get output
        stdout, stderr = await process.communicate()

        # Convert output to strings
        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""

        return process.returncode or 0, stdout_str, stderr_str
    except Exception as e:
        logger.error("Error running command %s: %s", ' '.join(command), str(e))
        return 1, "", str(e)

def format_command_output(stdout: str, stderr: str, return_code: int) -> str:
    """
    Format command output for display.

    Args:
        stdout: Standard output
        stderr: Standard error
        return_code: Command return code

    Returns:
        str: Formatted output
    """
    output = []

    if stdout:
        output.append("Output:")
        output.append(stdout)

    if stderr:
        output.append("Errors:")
        output.append(stderr)

    if return_code != 0:
        output.append(f"Command failed with return code {return_code}")

    return "\n".join(output)

def get_terminal_size() -> Tuple[int, int]:
    """
    Get the current terminal size.

    Returns:
        Tuple[int, int]: Width and height of the terminal
    """
    try:
        import shutil
        columns, rows = shutil.get_terminal_size()
        return columns, rows
    except Exception:
        return 80, 24  # Default fallback size
