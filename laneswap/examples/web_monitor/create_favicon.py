"""
Script to generate a favicon for the LaneSwap web monitor.
This creates a simple heart pulse icon as a favicon.
"""

from PIL import Image, ImageDraw
import os

def create_favicon():
    """Create a simple heart pulse favicon."""
    # Create a 32x32 transparent image
    img = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a heart pulse line
    # Background color
    primary_color = (13, 110, 253)  # Bootstrap primary blue
    
    # Draw the heart pulse
    points = [
        (2, 16),    # Start
        (8, 16),    # Flat
        (10, 8),    # Up
        (14, 24),   # Down
        (18, 12),   # Up
        (22, 16),   # Back to middle
        (30, 16)    # End
    ]
    
    # Draw a thicker line
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=primary_color, width=3)
    
    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
    img.save(output_path)
    print(f"Favicon created at {output_path}")

if __name__ == "__main__":
    create_favicon() 