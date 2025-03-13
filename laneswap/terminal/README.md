# LaneSwap Terminal Module

The terminal module provides a colorful, interactive terminal-based dashboard for monitoring service health in real-time.

## Components

### Terminal Monitor (`monitor.py`)

The main terminal monitor implementation, providing a real-time dashboard for service health.

#### Key Features

- **Real-time Updates**: See service status changes as they happen
- **Color-coded Status**: Quickly identify service health with color indicators
- **Automatic Refresh**: Configurable refresh interval
- **Summary Statistics**: Overview of service health status
- **Detailed Service Information**: View complete service information including latency and last heartbeat
- **Keyboard Shortcuts**: Easy navigation with keyboard shortcuts
- **Auto-detection**: Automatically detects if a terminal is available
- **Headless Mode**: Can run in non-terminal mode for headless environments
- **Scroll Preservation**: Preserves terminal scroll history for better navigation
- **Pause/Resume**: Press SPACE to pause/resume auto-refresh for uninterrupted viewing
- **Stable UI**: Consistent and stable terminal UI that handles window resizing
- **Priority Sorting**: Services are sorted by status (critical first) and then by name
- **Adaptive Display**: Automatically adjusts to terminal size and shows the most important services

#### Usage Example

```python
from laneswap.terminal import start_monitor
import asyncio

# Start the monitor with default settings
asyncio.run(start_monitor(api_url="http://localhost:8000"))

# Start with custom settings
asyncio.run(start_monitor(
    api_url="http://localhost:8000",
    refresh_interval=5.0,
    use_terminal=True,
    start_paused=False
))

# Run in non-terminal mode (logging only)
asyncio.run(start_monitor(
    api_url="http://localhost:8000",
    use_terminal=False
))
```

### ASCII Art (`ascii_art.py`)

Provides ASCII art for the terminal monitor header.

#### Key Features

- **Logo Display**: ASCII art logo for the terminal monitor
- **Header Formatting**: Consistent header formatting
- **Color Support**: Colorized ASCII art

### Colors (`colors.py`)

Provides color utilities for the terminal monitor.

#### Key Features

- **ANSI Color Codes**: Constants for ANSI color codes
- **Color Functions**: Functions for colorizing text
- **Status Colors**: Mapping of status values to colors
- **Terminal Detection**: Functions for detecting terminal capabilities

## Terminal Monitor Interface

The terminal monitor provides a comprehensive interface for monitoring service health:

### Header Section

- **Logo**: ASCII art logo
- **Version**: LaneSwap version
- **Status**: Monitor status (running/paused)
- **Refresh Rate**: Current refresh interval
- **API URL**: Connected API server URL

### Summary Section

- **Total Services**: Count of all registered services
- **Healthy Services**: Count of services with "healthy" status
- **Warning Services**: Count of services with "warning" status
- **Error Services**: Count of services with "error" or "critical" status
- **Unknown Services**: Count of services with "unknown" status
- **Stale Services**: Count of services that have not sent heartbeats recently

### Services Table

- **ID**: Service ID (truncated)
- **Name**: Service name
- **Status**: Current service status (color-coded)
- **Last Heartbeat**: Time since last heartbeat
- **Message**: Latest heartbeat message
- **Metadata**: Additional service information

### Footer Section

- **Controls**: Available keyboard shortcuts
- **Status**: Current monitor status
- **Time**: Current time

## Keyboard Controls

While the terminal monitor is running, you can use these keyboard controls:

- **SPACE**: Pause/resume auto-refresh (useful for scrolling through service data)
- **CTRL+C**: Exit the monitor

## Integration with Other Modules

The terminal module integrates with other LaneSwap modules:

- **API Module**: Communicates with the API server to retrieve service data
- **Models Module**: Uses data models for parsing API responses
- **Core Module**: Uses core types and utilities

## Advanced Usage

### Custom Terminal Monitor

You can create a custom terminal monitor by extending the `TerminalMonitor` class:

```python
from laneswap.terminal.monitor import TerminalMonitor
import asyncio

class CustomTerminalMonitor(TerminalMonitor):
    def __init__(self, api_url, refresh_interval=2.0, use_terminal=True, start_paused=False):
        super().__init__(api_url, refresh_interval, use_terminal, start_paused)
        # Custom initialization
    
    async def fetch_data(self):
        # Custom data fetching
        data = await super().fetch_data()
        # Process data
        return data
    
    def render_header(self):
        # Custom header rendering
        print("=== CUSTOM TERMINAL MONITOR ===")
    
    def render_services(self, services):
        # Custom service rendering
        for service in services:
            print(f"{service.name}: {service.status}")

# Use the custom monitor
async def main():
    monitor = CustomTerminalMonitor(api_url="http://localhost:8000")
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Color Scheme

You can customize the color scheme by modifying the color mappings:

```python
from laneswap.terminal.colors import STATUS_COLORS
from laneswap.terminal.monitor import TerminalMonitor
import asyncio

# Customize status colors
STATUS_COLORS["healthy"] = "\033[38;5;46m"  # Bright green
STATUS_COLORS["warning"] = "\033[38;5;220m"  # Yellow
STATUS_COLORS["error"] = "\033[38;5;196m"  # Bright red
STATUS_COLORS["critical"] = "\033[38;5;201m"  # Magenta
STATUS_COLORS["unknown"] = "\033[38;5;250m"  # Light gray

# Start the monitor with custom colors
async def main():
    monitor = TerminalMonitor(api_url="http://localhost:8000")
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Non-Terminal Mode

You can run the terminal monitor in non-terminal mode for headless environments:

```python
from laneswap.terminal import start_monitor
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="monitor.log"
)

# Run in non-terminal mode
asyncio.run(start_monitor(
    api_url="http://localhost:8000",
    use_terminal=False,
    refresh_interval=30.0
))
```

## Best Practices

1. **Terminal Size**: Ensure your terminal is large enough for the monitor display
2. **Refresh Interval**: Use a reasonable refresh interval (2-5 seconds) to avoid API overload
3. **Pause When Needed**: Use the SPACE key to pause auto-refresh when examining service details
4. **Color Support**: Ensure your terminal supports ANSI colors for the best experience
5. **Headless Mode**: Use non-terminal mode for automated monitoring or headless environments
6. **Error Handling**: Handle API connection errors gracefully
7. **Resource Usage**: Be mindful of resource usage with very frequent refreshes
8. **Secure Connections**: Use HTTPS in production
9. **Monitoring Duration**: For long-term monitoring, consider using a service like systemd
10. **Log Output**: Redirect log output to a file for non-terminal mode 