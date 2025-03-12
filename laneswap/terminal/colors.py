"""
Terminal color utilities for LaneSwap.

This module provides color constants and functions for terminal text styling.
"""

from enum import Enum
from typing import Optional


class Color(Enum):
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Text styles
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ITALIC = "\033[3m"


def colored_text(text: str, color: Optional[Color] = None, 
                 bg_color: Optional[Color] = None, 
                 bold: bool = False, 
                 underline: bool = False,
                 italic: bool = False) -> str:
    """
    Format text with ANSI color codes for terminal display.
    
    Args:
        text: The text to color
        color: Foreground color from Color enum
        bg_color: Background color from Color enum
        bold: Whether to make the text bold
        underline: Whether to underline the text
        italic: Whether to italicize the text
        
    Returns:
        Formatted text string with ANSI color codes
    """
    result = ""
    
    if color:
        result += color.value
    
    if bg_color:
        result += bg_color.value
    
    if bold:
        result += Color.BOLD.value
    
    if underline:
        result += Color.UNDERLINE.value
    
    if italic:
        result += Color.ITALIC.value
    
    result += text
    result += Color.RESET.value
    
    return result 