"""
Terminal-based monitor for LaneSwap services.

This module provides a terminal UI for monitoring LaneSwap services in real-time.
It can also run in a non-terminal mode for headless environments.
"""

import asyncio
import datetime
import logging
import os
import select
import shutil
import signal
import sys
import time
from typing import Any, Dict, List, Optional, TextIO, Tuple

import aiohttp
import keyboard

from ..client.async_client import LaneswapAsyncClient
from ..models.heartbeat import ServiceStatus
from .ascii_art import (
    FOOTER,
    HEADER,
    LOADING_FRAMES,
    LOGO,
    STATUS_ERROR,
    STATUS_OK,
    STATUS_UNKNOWN,
    STATUS_WARNING,
)
from .colors import Color, colored_text

# Configure logging
logger = logging.getLogger("laneswap.terminal.monitor")

# Default terminal width if we can't detect it
DEFAULT_TERMINAL_WIDTH = 100
DEFAULT_TERMINAL_HEIGHT = 30


class TerminalMonitor:
    """
    Terminal-based UI for monitoring LaneSwap services.

    This class provides a real-time terminal interface for monitoring
    the status of registered services.
    """

    def __init__(self, client: LaneswapAsyncClient, refresh_interval: float =
        2.0, use_terminal: Optional[bool] = None):
        """
        Initialize the terminal monitor.

        Args:
            client: LaneswapAsyncClient instance for API communication
            refresh_interval: How often to refresh the display (in seconds)
            use_terminal: Whether to use terminal UI (auto-detect if None)
        """
        self.client = client
        self.refresh_interval = refresh_interval
        self.services: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.paused = False
        self.loading_frame = 0
        self.last_resize_check = time.time()

        # Auto-detect terminal if not specified
        if use_terminal is None:
            self.use_terminal = self._detect_terminal()
        else:
            self.use_terminal = use_terminal

        # Get initial terminal size
        self.terminal_width, self.terminal_height = self._get_terminal_size()

        # Register signal handlers for clean exit
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

        # Register window resize handler if supported
        try:
            signal.signal(signal.SIGWINCH, self._handle_resize)
            logger.debug("Registered window resize handler")
        except (AttributeError, ValueError):
            logger.debug("Window resize handler not supported on this platform")

        logger.debug("Terminal monitor initialized (width: %s, height: %s)", self.terminal_width, self.terminal_height)

    def _detect_terminal(self) -> bool:
        """
        Detect if a terminal is available.

        Returns:
            True if a terminal is available, False otherwise
        """
        # Check if stdout is a TTY
        if not sys.stdout.isatty():
            logger.debug("stdout is not a TTY, using non-terminal mode")
            return False

        # Check if we can get terminal size
        try:
            shutil.get_terminal_size()
            return True
        except Exception:
            logger.debug("Failed to get terminal size, using non-terminal mode")
            return False

    def _get_terminal_size(self) -> Tuple[int, int]:
        """Get the current terminal size."""
        try:
            columns, lines = shutil.get_terminal_size()
            return max(columns, DEFAULT_TERMINAL_WIDTH), max(lines, DEFAULT_TERMINAL_HEIGHT)
        except Exception:
            return DEFAULT_TERMINAL_WIDTH, DEFAULT_TERMINAL_HEIGHT

    def _handle_exit(self, signum: int, frame: Any) -> None:
        """Handle exit signals to clean up resources."""
        self.running = False
        if self.use_terminal:
            print("\n" + colored_text("Shutting down LaneSwap monitor...", Color.YELLOW))
        sys.exit(0)

    def _clear_screen(self) -> None:
        """Clear the terminal screen completely."""
        if self.use_terminal:
            # Use a more reliable approach to clear the screen
            if sys.platform == 'win32':
                os.system('cls')
            else:
                os.system('clear')

            # Update terminal size
            self.terminal_width, self.terminal_height = self._get_terminal_size()

    def _get_status_indicator(self, status: str) -> str:
        """
        Get a colored status indicator based on service status.

        Args:
            status: The service status

        Returns:
            Colored status indicator string
        """
        if status == "healthy":
            return colored_text(STATUS_OK, Color.GREEN, bold=True)
        elif status == "warning":
            return colored_text(STATUS_WARNING, Color.YELLOW, bold=True)
        elif status == "error" or status == "critical":
            return
        # Removed unnecessary else:
            return colored_text(STATUS_UNKNOWN, Color.BRIGHT_BLACK)

    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """
        Format a timestamp into a human-readable string.

        Args:
            timestamp: ISO format timestamp or None

        Returns:
            Formatted timestamp string
        """
        if timestamp is None:
            return colored_text("Never", Color.BRIGHT_BLACK)

        try:
            if isinstance(timestamp, str):
                dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif isinstance(timestamp, datetime.datetime):
                dt = timestamp
            else:
                return colored_text("Invalid", Color.BRIGHT_BLACK)

            now = datetime.datetime.now()
            delta = now - dt

            if delta.total_seconds() < 60:
                return colored_text(f"{int(delta.total_seconds())}s ago", Color.GREEN)
            elif delta.total_seconds() < 3600:
                return colored_text(f"{int(delta.total_seconds() / 60)}m ago", Color.GREEN)
            elif delta.total_seconds() < 86400:
                return
            # Removed unnecessary else:
                return colored_text(f"{int(delta.total_seconds() / 86400)}d ago", Color.RED)
        except Exception:
            return colored_text("Unknown", Color.BRIGHT_BLACK)

    def _format_latency(self, latency: Optional[float]) -> str:
        """
        Format latency with color coding based on performance.

        Args:
            latency: Latency in milliseconds or None

        Returns:
            Formatted latency string
        """
        if latency is None:
            return colored_text("Unknown", Color.BRIGHT_BLACK)

        if latency < 100:
            return colored_text(f"{latency:.1f}", Color.GREEN)
        elif latency < 500:
            return
        # Removed unnecessary else:
            return colored_text(f"{latency:.1f}", Color.RED)

    def _render_services_table(self) -> None:
        """Render the service status table."""
        # Calculate column widths based on terminal width
        name_width = min(30, max(10, int(self.terminal_width * 0.25)))
        status_width = 15
        last_seen_width = 20
        message_width = min(30, max(10, int(self.terminal_width * 0.25)))
        id_width = min(20, max(10, int(self.terminal_width * 0.15)))

        # Ensure total width doesn't exceed terminal width
        total_width = name_width + status_width + last_seen_width + message_width + id_width + 4  # 4 for spaces
        if total_width > self.terminal_width:
            # Reduce message width first, then ID width
            excess = total_width - self.terminal_width
            if excess <= message_width - 10:
                message_width -= excess
            else:
                message_width = 10
                id_width = max(10, id_width - (excess - (message_width - 10)))

        headers = [
            colored_text("SERVICE NAME", Color.CYAN, bold=True),
            colored_text("STATUS", Color.CYAN, bold=True),
            colored_text("LAST HEARTBEAT", Color.CYAN, bold=True),
            colored_text("MESSAGE", Color.CYAN, bold=True),
            colored_text("ID", Color.CYAN, bold=True)
        ]

        # Print table header
        print(f"{headers[0]:<{name_width}} {headers[1]:<{status_width}} {headers[2]:<{last_seen_width}} {headers[3]:<{message_width}} {headers[4]:<{id_width}}")
        print("-" * min(self.terminal_width, name_width + status_width + last_seen_width + message_width + id_width + 4))

        # Print table rows
        if not self.services:
            print(colored_text("No services registered. Waiting for services...", Color.BRIGHT_BLACK, italic=
                True))
            return

        # Calculate available space for services
        # Reserve lines for:
        # - Logo (8 lines)
        # - Header (3 lines)
        # - Table header (2 lines)
        # - Summary (3 lines)
        # - Footer (3 lines)
        # - Loading indicator (1 line)
        # - Paused indicator (1 line if paused)
        # - Safety margin (2 lines)
        reserved_lines = 22
        max_services = max(1, self.terminal_height - reserved_lines)

        # Sort services by status (critical first, then warning, then healthy, then unknown)
        # and then by name
        def sort_key(item):
            service_id, info = item
            status = info.get('status', 'unknown')
            name = info.get('name', '')

            # Define status priority (lower number = higher priority)
            status_priority = {
                'error': 0,
                'critical': 0,
                'warning': 1,
                'healthy': 2,
                'unknown': 3
            }

            return (status_priority.get(status, 4), name.lower())

        sorted_services = sorted(self.services.items(), key=sort_key)

        # Show truncation message if needed
        if len(sorted_services) > max_services:
            display_services = sorted_services[:max_services-1]
            truncation_msg = f"Showing {len(display_services)} of {len(sorted_services)} services (sorted by status and name)"
            print(colored_text(truncation_msg, Color.YELLOW))
        else:
            display_services = sorted_services

        for service_id, info in display_services:
            status = info.get('status', 'unknown')
            status_indicator = self._get_status_indicator(status)

            # Handle different field names for last heartbeat
            last_heartbeat = None
            for field in ['last_heartbeat', 'lastHeartbeat', 'last_seen']:
                if field in info:
                    last_heartbeat = info[field]
                    break

            last_seen = self._format_timestamp(last_heartbeat)

            # Handle different field names for status message
            message = None
            for field in ['status_message', 'statusMessage', 'message', 'last_message']:
                if field in info:
                    message = info[field]
                    break

            if not message:
                message = ""

            # Truncate strings to fit column widths
            service_name = info.get('name', 'Unknown')
            if len(service_name) > name_width:
                service_name = service_name[:name_width-3] + "..."

            if len(message) > message_width:
                message = message[:message_width-3] + "..."

            if len(service_id) > id_width:
                service_id = service_id[:id_width-3] + "..."

            # Color the service name based on status
            if status == 'healthy':
                name_color = Color.GREEN
            elif status == 'warning':
                name_color = Color.YELLOW
            elif status in ['error', 'critical']:
                name_color = Color.RED
            else:
                name_color = Color.WHITE

            print(
                f"{colored_text(service_name, name_color):<{name_width}} "
                f"{status_indicator:<{status_width}} "
                f"{last_seen:<{last_seen_width}} "
                f"{colored_text(message, Color.BRIGHT_WHITE):<{message_width}} "
                f"{colored_text(service_id, Color.BRIGHT_BLACK):<{id_width}}"
            )

    def _render_summary(self) -> None:
        """Render the summary statistics."""
        if not self.services:
            return

        healthy = sum(1 for info in self.services.values() if info.get('status') == 'healthy')
        warning = sum(1 for info in self.services.values() if info.get('status') == 'warning')
        critical = sum(1 for info in self.services.values() if info.get('status') in ['error', 'critical'])
        unknown = sum(1 for info in self.services.values() if info.get('status') not in ['healthy', 'warning', 'error', 'critical'])

        # Use terminal width for the separator line
        print("\n" + "-" * min(self.terminal_width, 115))

        summary_text = (
            "Summary: "
            f"{colored_text(f'{healthy} healthy', Color.GREEN)} | "
            f"{colored_text(f'{warning} warning', Color.YELLOW)} | "
            f"{colored_text(f'{critical} critical', Color.RED)} | "
            f"{colored_text(f'{unknown} unknown', Color.BRIGHT_BLACK)}"
        )
        print(summary_text)

    def _print_non_terminal_summary(self) -> None:
        """Print a summary of services in non-terminal mode."""
        if not self.services:
            logger.info("No services registered")
            return

        healthy = sum(1 for info in self.services.values() if info.get('status') == 'healthy')
        warning = sum(1 for info in self.services.values() if info.get('status') == 'warning')
        critical = sum(1 for info in self.services.values() if info.get('status') in ['error', 'critical'])
        unknown = sum(1 for info in self.services.values() if info.get('status') not in ['healthy', 'warning', 'error', 'critical'])

        logger.info("Services summary: %s healthy, %s warning, %s critical, %s unknown", healthy, warning, critical, unknown)

        # Log details of non-healthy services
        if warning + critical > 0:
            for service_id, info in self.services.items():
                status = info.get('status', 'unknown')
                if status not in ['healthy', 'unknown']:
                    name = info.get('name', 'Unknown')
                    message = None
                    for field in ['status_message', 'statusMessage', 'message', 'last_message']:
                        if field in info and info[field]:
                            message = info[field]
                            break

                    last_heartbeat = None
                    for field in ['last_heartbeat', 'lastHeartbeat', 'last_seen']:
                        if field in info:
                            last_heartbeat = info[field]
                            break

                    logger.warning("Service '%s' (%s) is %s: %s", name, service_id, status, message or 'No message')

    async def _update_services(self) -> None:
        """Update the services data from the API."""
        try:
            logger.debug("Fetching services from %s", self.client.api_url)

            # Get all services from the API
            response = await self.client.get_all_services()
            logger.debug("API response: %s", type(response))

            # Check if the response has a 'services' key (API format)
            if isinstance(response, dict) and 'services' in response:
                logger.debug("Found services key with %s services", len(response['services']))
                self.services = response['services']
            # Or if it's already a dictionary of services
            elif isinstance(response, dict):
                # Check if it looks like a services dictionary (has id, name, status keys)
                if all(isinstance(v, dict) and 'id' in v for v in response.values()):
                    logger.debug("Response appears to be a services dictionary with %s services", len(response))
                    self.services = response
                else:
                    logger.warning("Response is a dictionary but doesn't look like services: %s", list(response.keys()))
                    if self.use_terminal:
                        print(colored_text(f"Unexpected response format: {list(response.keys())}", Color.RED))
            else:
                logger.warning("Unexpected response type: %s", type(response))
                if self.use_terminal:
                    print(colored_text(f"Unexpected response format: {type(response)}", Color.RED))
        except aiohttp.ClientConnectorError as e:
            logger.error("Cannot connect to API server: %s", e)
            if self.use_terminal:
                print(colored_text(f"Cannot connect to API server at {self.client.api_url}", Color.RED))
                print(colored_text("Make sure the LaneSwap API server is running.", Color.YELLOW))
        except Exception as e:
            logger.error("Error fetching services: %s", e, exc_info=True)
            if self.use_terminal:
                print(colored_text(f"Error fetching services: {e}", Color.RED))

    async def start(self) -> None:
        """Start the terminal monitor."""
        self.running = True
        logger.debug("Starting monitor")

        try:
            if self.use_terminal:
                await self._start_terminal_mode(self.refresh_interval)
            else:
                await self._start_non_terminal_mode(self.refresh_interval)
        except KeyboardInterrupt:
            logger.debug("Monitor stopped by keyboard interrupt")
            self.running = False
        except Exception as e:
            logger.error("Error in monitor: %s", e, exc_info=True)
            self.running = False
        finally:
            # Ensure terminal is left in a clean state if using terminal
            if self.use_terminal:
                sys.stdout.write("\n")
                sys.stdout.flush()
            logger.debug("Monitor stopped")

    def _handle_resize(self, signum: int, frame: Any) -> None:
        """Handle window resize events."""
        if self.use_terminal:
            old_width, old_height = self.terminal_width, self.terminal_height
            self.terminal_width, self.terminal_height = self._get_terminal_size()
            logger.debug("Terminal resized from %sx%s to %sx%s", old_width, old_height, self.terminal_width, self.terminal_height)

            # Force a redraw on next iteration
            # We don't clear the screen here to avoid flickering

    def _on_key_press(self, key) -> None:
        """Handle keyboard events."""
        try:
            # Toggle pause on space key
            if hasattr(key, 'char') and key.char == ' ':
                self.paused = not self.paused
                logger.debug("Monitor %s", 'paused' if self.paused else 'resumed')
        except Exception as e:
            logger.error("Error handling key press: %s", e)

    def _check_for_resize(self) -> bool:
        """
        Check if the terminal has been resized.

        Returns:
            True if the terminal was resized, False otherwise
        """
        # Only check every second to avoid performance issues
        current_time = time.time()
        if current_time - self.last_resize_check < 1.0:
            return False

        self.last_resize_check = current_time

        # Get current terminal size
        current_width, current_height = self._get_terminal_size()

        # Check if size has changed
        if current_width != self.terminal_width or current_height != self.terminal_height:
            logger.debug("Terminal resized from %sx%s to %sx%s", self.terminal_width, self.terminal_height, current_width, current_height)
            self.terminal_width, self.terminal_height = current_width, current_height
            return True

        return False

    async def _start_terminal_mode(self, refresh_interval: float) -> None:
        """Start the monitor in terminal mode."""
        if not self.use_terminal:
            return

        try:
            while True:
                # Clear the screen for each refresh
                self._clear_screen()

                # Update services data if not paused
                if not self.paused:
                    await self._update_services()

                # Render ASCII art header
                print(get_ascii_header(self.terminal_width))

                # Render services table
                self._render_services_table()

                # Render summary statistics
                self._render_summary()

                # Render footer with instructions
                status_text = "PAUSED" if self.paused else "Refreshing"
                frames = LOADING_FRAMES
                if not self.paused:
                    self.loading_frame = (self.loading_frame + 1) % len(frames)
                frame = frames[self.loading_frame]
                footer_message = f"{frame} {status_text} services data... Press SPACE to {'resume' if self.paused else 'pause'} | CTRL+C to exit"
                print("\n" + colored_text(footer_message, Color.BRIGHT_BLUE))

                # Wait for refresh interval
                await asyncio.sleep(refresh_interval)
        except asyncio.CancelledError:
            logger.info("Terminal monitor cancelled")
            raise
        except Exception as e:
            logger.error("Error in terminal monitor: %s", e)
            raise

    async def _start_non_terminal_mode(self, refresh_interval: float) -> None:
        """Start the monitor in non-terminal mode."""
        logger.info("Starting LaneSwap monitor in non-terminal mode (API URL: %s)", self.client.api_url)

        while self.running:
            # Update services
            await self._update_services()

            # Print summary to logs
            self._print_non_terminal_summary()

            # Wait for next refresh
            logger.debug("Waiting %s seconds until next refresh", refresh_interval)
            await asyncio.sleep(refresh_interval)


async def start_monitor(api_url: str, refresh_interval: float =
    2.0, use_terminal: Optional[bool] = None, start_paused: bool = False) -> None:
    """
    Start the terminal monitor with the specified API URL.

    Args:
        api_url: URL of the LaneSwap API server
        refresh_interval: How often to refresh the display (in seconds)
        use_terminal: Whether to use terminal UI (auto-detect if None)
        start_paused: Whether to start the monitor in paused mode
    """
    from ..client.async_client import LaneswapAsyncClient

    # Create client
    client = LaneswapAsyncClient(
        api_url=api_url,
        service_name="terminal-monitor"
    )

    # Create and start monitor
    monitor = TerminalMonitor(
        client=client,
        refresh_interval=refresh_interval,
        use_terminal=use_terminal
    )

    # Set initial paused state if requested
    if start_paused:
        monitor.paused = True

    # Start the monitor
    await monitor.start()
