#!/usr/bin/python3
"""
Picture Editor - Text box annotation and paint bucket fill tools for picture notes
"""

import gi
import uuid
from enum import Enum

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, cairo

import gettext
_ = gettext.gettext
gettext.install("sticky", "/usr/share/locale", names="ngettext")


class TextBoxType(Enum):
    """Types of text boxes for different annotation purposes"""
    DESCRIPTION = "description"  # Explains a feature
    INSTRUCTION = "instruction"  # Requests evaluation/adjustment


class TextBox:
    """Annotation text box for pictures"""
    
    def __init__(self, x=0, y=0, text="", font_size=14, font_color="#000000", box_type=TextBoxType.DESCRIPTION):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.width = 200
        self.height = 50
        self.text = text
        self.font_size = font_size
        self.font_color = font_color
        self.box_type = box_type
        self.selected = False
        self.is_editing = False
        self.min_width = 100
        self.min_height = 30
    
    def contains_point(self, px, py):
        """Check if point is within text box"""
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def get_handle_at(self, px, py, handle_size=8):
        """Get which handle (if any) is at the point"""
        handles = self.get_handles()
        for idx, (hx, hy) in enumerate(handles):
            if (hx - handle_size <= px <= hx + handle_size and 
                hy - handle_size <= py <= hy + handle_size):
                return idx
        return -1
    
    def get_handles(self):
        """Get handle positions (corners and edges)"""
        return [
            (self.x, self.y),                                    # top-left
            (self.x + self.width, self.y),                      # top-right
            (self.x + self.width, self.y + self.height),        # bottom-right
            (self.x, self.y + self.height),                     # bottom-left
            (self.x + self.width // 2, self.y),                 # top-center
            (self.x + self.width, self.y + self.height // 2),   # right-center
            (self.x + self.width // 2, self.y + self.height),   # bottom-center
            (self.x, self.y + self.height // 2),                # left-center
        ]
    
    def move(self, dx, dy):
        """Move text box by delta"""
        self.x += dx
        self.y += dy
    
    def set_position(self, x, y):
        """Set text box position"""
        self.x = max(0, x)
        self.y = max(0, y)
    
    def resize_from_handle(self, handle_idx, px, py):
        """Resize text box from a specific handle"""
        if handle_idx == 0:  # top-left
            self.width = max(self.min_width, self.width + (self.x - px))
            self.height = max(self.min_height, self.height + (self.y - py))
            self.x = px
            self.y = py
        elif handle_idx == 1:  # top-right
            self.width = max(self.min_width, px - self.x)
            self.height = max(self.min_height, self.height + (self.y - py))
            self.y = py
        elif handle_idx == 2:  # bottom-right
            self.width = max(self.min_width, px - self.x)
            self.height = max(self.min_height, py - self.y)
        elif handle_idx == 3:  # bottom-left
            self.width = max(self.min_width, self.width + (self.x - px))
            self.height = max(self.min_height, py - self.y)
            self.x = px
        elif handle_idx == 4:  # top-center
            self.height = max(self.min_height, self.height + (self.y - py))
            self.y = py
        elif handle_idx == 5:  # right-center
            self.width = max(self.min_width, px - self.x)
        elif handle_idx == 6:  # bottom-center
            self.height = max(self.min_height, py - self.y)
        elif handle_idx == 7:  # left-center
            self.width = max(self.min_width, self.width + (self.x - px))
            self.x = px
    
    def render(self, context, pixbuf=None):
        """Draw text box on cairo context"""
        # Draw background box
        if self.box_type == TextBoxType.INSTRUCTION:
            # Orange border for instructions
            context.set_source_rgb(1.0, 0.6, 0.0)  # Orange
        else:
            # Blue border for descriptions
            context.set_source_rgb(0.2, 0.5, 1.0)  # Blue
        
        # Draw filled background with transparency
        context.set_source_rgba(1.0, 1.0, 1.0, 0.8)
        context.rectangle(self.x, self.y, self.width, self.height)
        context.fill()
        
        # Draw border
        if self.selected:
            context.set_line_width(3)
        else:
            context.set_line_width(2)
        
        if self.box_type == TextBoxType.INSTRUCTION:
            context.set_source_rgb(1.0, 0.6, 0.0)  # Orange
        else:
            context.set_source_rgb(0.2, 0.5, 1.0)  # Blue
        
        context.rectangle(self.x, self.y, self.width, self.height)
        context.stroke()
        
        # Draw text
        context.set_source_rgb(0, 0, 0)
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(self.font_size)
        
        # Parse font color hex
        try:
            if self.font_color.startswith('#'):
                r = int(self.font_color[1:3], 16) / 255.0
                g = int(self.font_color[3:5], 16) / 255.0
                b = int(self.font_color[5:7], 16) / 255.0
            else:
                r, g, b = 0, 0, 0
            context.set_source_rgb(r, g, b)
        except:
            context.set_source_rgb(0, 0, 0)
        
        # Draw text with word wrap
        text_lines = self.text.split('\n')
        y_offset = self.y + 5
        padding = 5
        
        for line in text_lines:
            context.move_to(self.x + padding, y_offset + self.font_size)
            context.show_text(line[:30])  # Limit text width
            y_offset += self.font_size + 2
        
        # Draw handles if selected
        if self.selected:
            self.render_handles(context)
    
    def render_handles(self, context):
        """Draw resize handles"""
        context.set_source_rgb(1.0, 0.2, 0.2)  # Red
        handle_size = 6
        
        for hx, hy in self.get_handles():
            context.rectangle(hx - handle_size, hy - handle_size, handle_size * 2, handle_size * 2)
            context.fill()
    
    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.text,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'box_type': self.box_type.value
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize from dictionary"""
        box = cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            text=data.get('text', ''),
            font_size=data.get('font_size', 14),
            font_color=data.get('font_color', '#000000'),
            box_type=TextBoxType(data.get('box_type', 'description'))
        )
        box.id = data.get('id', str(uuid.uuid4()))
        box.width = data.get('width', 200)
        box.height = data.get('height', 50)
        return box


def flood_fill(pixbuf, x, y, replacement_color, tolerance=20):
    """
    Flood fill algorithm - replace continuous color region
    
    Args:
        pixbuf: GdkPixbuf to modify
        x, y: Starting point
        replacement_color: Tuple (r, g, b) 0-255
        tolerance: Color match tolerance (0-255)
    
    Returns:
        Modified pixbuf
    """
    pixels = pixbuf.get_pixels()
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    n_channels = pixbuf.get_n_channels()
    rowstride = pixbuf.get_rowstride()
    
    # Boundary check
    if not (0 <= x < width and 0 <= y < height):
        return pixbuf
    
    # Get target color at starting point
    start_idx = y * rowstride + x * n_channels
    if start_idx + 2 >= len(pixels):
        return pixbuf
    
    target_color = (
        pixels[start_idx],
        pixels[start_idx + 1],
        pixels[start_idx + 2]
    )
    
    # If target is same as replacement, no need to fill
    if all(abs(target_color[i] - replacement_color[i]) < 5 for i in range(3)):
        return pixbuf
    
    # Flood fill using queue
    queue = [(x, y)]
    visited = set()
    visited.add((x, y))
    
    while queue:
        cx, cy = queue.pop(0)
        
        # Fill current pixel
        idx = cy * rowstride + cx * n_channels
        if idx + 2 < len(pixels):
            pixels[idx] = replacement_color[0]
            pixels[idx + 1] = replacement_color[1]
            pixels[idx + 2] = replacement_color[2]
        
        # Check neighbors
        for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
            if (0 <= nx < width and 0 <= ny < height and 
                (nx, ny) not in visited):
                
                n_idx = ny * rowstride + nx * n_channels
                if n_idx + 2 < len(pixels):
                    neighbor_color = (
                        pixels[n_idx],
                        pixels[n_idx + 1],
                        pixels[n_idx + 2]
                    )
                    
                    # Check if color matches target within tolerance
                    if all(abs(neighbor_color[i] - target_color[i]) <= tolerance for i in range(3)):
                        visited.add((nx, ny))
                        queue.append((nx, ny))
    
    return pixbuf
