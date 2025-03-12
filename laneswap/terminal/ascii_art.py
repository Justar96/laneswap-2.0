"""
ASCII art for LaneSwap terminal UI.

This module contains ASCII art elements for enhancing the terminal user interface.
"""

# ASCII logo for LaneSwap
LOGO = r"""
 _                      _____                       
| |                    / ____|                      
| |     __ _ _ __  ___| (___ __      ____ _ _ __   
| |    / _` | '_ \/ _ \\___ \\ \ /\ / / _` | '_ \  
| |___| (_| | | |  __/____) |\ V  V / (_| | |_) | 
|______\__,_|_| |\___|_____/  \_/\_/ \__,_| .__/  
                                          | |     
                                          |_|     
"""

# Header for terminal display
HEADER = r"""
+--------------------------------------------------------------+
|                    LANESWAP TERMINAL MONITOR                 |
+--------------------------------------------------------------+
"""

# Footer for terminal display
FOOTER = r"""
+--------------------------------------------------------------+
|           Press Ctrl+C to exit | v0.1.2 | LaneSwap           |
+--------------------------------------------------------------+
"""

# Status indicators
STATUS_OK = "[✓]"
STATUS_WARNING = "[!]"
STATUS_ERROR = "[✗]"
STATUS_UNKNOWN = "[?]"

# Loading animation frames
LOADING_FRAMES = ["|", "/", "-", "\\"]

# Service status box template
SERVICE_BOX = r"""
+------------------------+
| {service_name}         |
| Status: {status}       |
| Last seen: {last_seen} |
| Latency: {latency}ms   |
+------------------------+
""" 