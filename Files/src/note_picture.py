#!/usr/bin/python3
"""
Picture Note - for displaying and managing screenshot/icon images.
Similar to NoteExtended but with image viewing capabilities and picture editor tools.
"""

import gi
import os
import uuid
import sys
import json
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, cairo

from .note_extended import NoteExtended
from .picture_editor import TextBox, TextBoxType, flood_fill
from sticky_unmodified import COLORS
import gettext

# Initialize gettext for translations
_ = gettext.gettext
gettext.install("sticky", "/usr/share/locale", names="ngettext")


class NotePicture(NoteExtended):
    """
    Picture note for viewing and managing images/screenshots.
    Enhanced with text box annotation and paint bucket fill tools.
    """
    
    def __init__(self, app, parent, info={}):
        self.image_path = info.get('image_path', '')
        self.is_picture_note = True
        self.text_boxes = []
        self.current_pixbuf = None
        self.original_pixbuf = None
        self.edit_mode = False
        self.selected_text_box = None
        self.active_tool = None  # 'text', 'bucket', or None
        self.current_fill_color = (255, 0, 0)
        self.current_font_size = 14
        self.current_text_box_type = TextBoxType.DESCRIPTION
        self.dragging_handle = -1
        self.drag_start = (0, 0)
        
        # Load text boxes from metadata
        if 'text_boxes' in info:
            for box_data in info['text_boxes']:
                self.text_boxes.append(TextBox.from_dict(box_data))
        
        # Prevent the parent class from adding text editor
        info['is_picture_note'] = True
        
        # Call parent constructor
        super().__init__(app, parent, info)
        
        # Replace the TextView with image viewer
        self._replace_textview_with_imageview()
        
        # Add picture editor toolbar
        self._add_picture_editor_toolbar()
        
        # Add picture indicator to title bar
        self._add_picture_indicator()
    
    def _add_picture_editor_toolbar(self):
        """Add toolbar with text box and paint bucket tools"""
        try:
            # Create toolbar box
            toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            toolbar.set_margin_start(5)
            toolbar.set_margin_end(5)
            toolbar.set_margin_top(3)
            toolbar.set_margin_bottom(3)
            
            # Get icons path
            icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Icons')
            
            # Add Text Box Button
            text_icon_path = os.path.join(icons_path, 'Text Box.png')
            text_icon = Gtk.Image.new_from_file(text_icon_path) if os.path.exists(text_icon_path) else Gtk.Image.new_from_icon_name('text-editor', Gtk.IconSize.BUTTON)
            text_btn = Gtk.ToggleButton(image=text_icon, label="Text")
            text_btn.set_tooltip_text(_("Add Text Box - Click image to place"))
            text_btn.connect('toggled', self._on_text_tool_toggled)
            toolbar.pack_start(text_btn, False, False, 0)
            self.text_tool_btn = text_btn
            
            # Add Paint Bucket Button
            bucket_icon_path = os.path.join(icons_path, 'Paint Bucket.png')
            bucket_icon = Gtk.Image.new_from_file(bucket_icon_path) if os.path.exists(bucket_icon_path) else Gtk.Image.new_from_icon_name('paint-bucket', Gtk.IconSize.BUTTON)
            bucket_btn = Gtk.ToggleButton(image=bucket_icon, label="Fill")
            bucket_btn.set_tooltip_text(_("Paint Bucket - Select color and click to fill"))
            bucket_btn.connect('toggled', self._on_bucket_tool_toggled)
            toolbar.pack_start(bucket_btn, False, False, 0)
            self.bucket_tool_btn = bucket_btn
            
            # Add separator
            sep1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            toolbar.pack_start(sep1, False, False, 0)
            
            # Font Size Spinner
            font_label = Gtk.Label(label="Font:")
            toolbar.pack_start(font_label, False, False, 0)
            
            font_spin = Gtk.SpinButton()
            font_spin.set_range(8, 72)
            font_spin.set_value(14)
            font_spin.set_increments(1, 5)
            font_spin.set_width_chars(3)
            font_spin.connect('value-changed', self._on_font_size_changed)
            toolbar.pack_start(font_spin, False, False, 0)
            self.font_size_spin = font_spin
            
            # Color Picker for fill/text
            color_label = Gtk.Label(label="Color:")
            toolbar.pack_start(color_label, False, False, 0)
            
            color_btn = Gtk.ColorButton()
            color_btn.set_rgba(Gdk.RGBA(1.0, 0.0, 0.0, 1.0))
            color_btn.connect('color-set', self._on_color_changed)
            toolbar.pack_start(color_btn, False, False, 0)
            self.color_picker = color_btn
            
            # Add separator
            sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            toolbar.pack_start(sep2, False, False, 0)
            
            # Text Box Type Combo (Description vs Instruction)
            type_label = Gtk.Label(label="Type:")
            toolbar.pack_start(type_label, False, False, 0)
            
            type_combo = Gtk.ComboBoxText()
            type_combo.append("description", "Description")
            type_combo.append("instruction", "Instruction")
            type_combo.set_active(0)
            type_combo.connect('changed', self._on_text_box_type_changed)
            toolbar.pack_start(type_combo, False, False, 0)
            self.text_box_type_combo = type_combo
            
            # Add spacer
            spacer = Gtk.Box()
            toolbar.pack_start(spacer, True, True, 0)
            
            # Exit Edit Mode Button
            exit_icon = Gtk.Image.new_from_icon_name('window-close', Gtk.IconSize.BUTTON)
            exit_btn = Gtk.Button(image=exit_icon, label="Done")
            exit_btn.set_tooltip_text(_("Exit Edit Mode"))
            exit_btn.connect('clicked', self._on_exit_edit_mode)
            toolbar.pack_end(exit_btn, False, False, 0)
            
            # Add toolbar to main box (between title bar and image)
            # Find the right place to insert
            main_box = self.get_children()[0] if self.get_children() else None
            if main_box and isinstance(main_box, Gtk.Box):
                # Insert toolbar after the title bar
                for i, child in enumerate(main_box.get_children()):
                    if isinstance(child, Gtk.ScrolledWindow):
                        main_box.reorder_child(toolbar, i)
                        break
                main_box.pack_start(toolbar, False, False, 0)
                main_box.reorder_child(toolbar, 1)  # Put it after title bar
            
            toolbar.show_all()
            self.editor_toolbar = toolbar
            
        except Exception as e:
            print(f"Failed to add picture editor toolbar: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_text_tool_toggled(self, widget):
        """Toggle text tool"""
        if widget.get_active():
            self.active_tool = 'text'
            self.bucket_tool_btn.set_active(False)
        else:
            self.active_tool = None
    
    def _on_bucket_tool_toggled(self, widget):
        """Toggle paint bucket tool"""
        if widget.get_active():
            self.active_tool = 'bucket'
            self.text_tool_btn.set_active(False)
        else:
            self.active_tool = None
    
    def _on_font_size_changed(self, widget):
        """Update font size"""
        self.current_font_size = int(widget.get_value())
        if self.selected_text_box:
            self.selected_text_box.font_size = self.current_font_size
            self._redraw_image()
    
    def _on_color_changed(self, widget):
        """Update color"""
        rgba = widget.get_rgba()
        self.current_fill_color = (
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255)
        )
        if self.selected_text_box:
            # Update text color
            hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            self.selected_text_box.font_color = hex_color
            self._redraw_image()
    
    def _on_text_box_type_changed(self, widget):
        """Change text box type (description vs instruction)"""
        active_id = widget.get_active_id()
        self.current_text_box_type = TextBoxType(active_id)
    
    def _on_exit_edit_mode(self, widget):
        """Exit edit mode and return to view"""
        self.active_tool = None
        self.selected_text_box = None
        self.text_tool_btn.set_active(False)
        self.bucket_tool_btn.set_active(False)
    
    def _replace_textview_with_imageview(self):
        """Replace the TextView widget with an image viewer"""
        # Find the scrolled window containing the view
        scroll = None
        for child in self.get_children():
            if isinstance(child, Gtk.ScrolledWindow):
                scroll = child
                break
        
        if not scroll:
            return
        
        # Remove old view
        scroll.remove(self.view)
        
        # Create new scrolled window with image viewer
        image_scroll = Gtk.ScrolledWindow()
        image_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create drawing area for image and annotations
        self.draw_area = Gtk.DrawingArea()
        self.draw_area.connect('draw', self._on_draw)
        self.draw_area.connect('button-press-event', self._on_image_press)
        self.draw_area.connect('button-release-event', self._on_image_release)
        self.draw_area.connect('motion-notify-event', self._on_image_motion)
        self.draw_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                                   Gdk.EventMask.BUTTON_RELEASE_MASK | 
                                   Gdk.EventMask.POINTER_MOTION_MASK)
        
        image_scroll.add(self.draw_area)
        
        # Load image if path provided
        if self.image_path and os.path.exists(self.image_path):
            self._load_image(self.image_path)
        else:
            # Show placeholder
            pass
        
        # Replace the scroll content
        for child in scroll.get_children():
            scroll.remove(child)
        scroll.add(image_scroll)
        
        self.image_scroll = image_scroll
        
        scroll.show_all()
    
    def _load_image(self, image_path):
        """Load and display an image"""
        try:
            # Load the pixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            
            # Store original
            self.original_pixbuf = pixbuf
            self.current_pixbuf = pixbuf.copy()
            
            # Scale to reasonable size if needed
            width = pixbuf.get_width()
            height = pixbuf.get_height()
            
            # Set drawing area size
            self.draw_area.set_size_request(width, height)
            
            self.image_path = image_path
            self._redraw_image()
            
        except Exception as e:
            print(f"Error loading image: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_draw(self, widget, context):
        """Draw image and text boxes"""
        if not self.current_pixbuf:
            return
        
        # Draw image
        Gdk.cairo_set_source_pixbuf(context, self.current_pixbuf, 0, 0)
        context.paint()
        
        # Draw text boxes
        for box in self.text_boxes:
            box.render(context, self.current_pixbuf)
    
    def _redraw_image(self):
        """Redraw the drawing area"""
        if self.draw_area:
            self.draw_area.queue_draw()
    
    def _on_image_press(self, widget, event):
        """Handle mouse button press on image"""
        if not self.active_tool and not self.selected_text_box:
            return
        
        if self.active_tool == 'text':
            # Create new text box
            new_box = TextBox(
                x=int(event.x),
                y=int(event.y),
                box_type=self.current_text_box_type
            )
            self.text_boxes.append(new_box)
            self.selected_text_box = new_box
            self._show_text_box_dialog(new_box)
            self._redraw_image()
        
        elif self.active_tool == 'bucket':
            # Fill color at point
            if self.current_pixbuf:
                pixbuf = self.current_pixbuf.copy()
                flood_fill(pixbuf, int(event.x), int(event.y), self.current_fill_color)
                self.current_pixbuf = pixbuf
                self._redraw_image()
        
        elif self.selected_text_box:
            # Check if clicked on a text box handle
            handle = self.selected_text_box.get_handle_at(int(event.x), int(event.y))
            if handle >= 0:
                self.dragging_handle = handle
                self.drag_start = (event.x, event.y)
            elif self.selected_text_box.contains_point(int(event.x), int(event.y)):
                # Start dragging text box
                self.dragging_handle = -2  # Special flag for body drag
                self.drag_start = (event.x, event.y)
            else:
                # Click outside, deselect
                self.selected_text_box = None
                self._redraw_image()
    
    def _on_image_release(self, widget, event):
        """Handle mouse button release"""
        self.dragging_handle = -1
    
    def _on_image_motion(self, widget, event):
        """Handle mouse motion"""
        if self.dragging_handle >= -1:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            
            if self.dragging_handle == -2:
                # Moving text box
                self.selected_text_box.move(dx, dy)
            elif self.dragging_handle >= 0:
                # Resizing text box
                self.selected_text_box.resize_from_handle(self.dragging_handle, event.x, event.y)
            
            self.drag_start = (event.x, event.y)
            self._redraw_image()
    
    def _show_text_box_dialog(self, text_box):
        """Show dialog to edit text box content"""
        dialog = Gtk.Dialog(
            title="Edit Text Box",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        box = dialog.get_content_area()
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_spacing(10)
        
        # Text entry
        text_label = Gtk.Label(label="Text:")
        box.pack_start(text_label, False, False, 0)
        
        text_entry = Gtk.Entry()
        text_entry.set_text(text_box.text)
        box.pack_start(text_entry, False, False, 0)
        
        # Font size
        size_label = Gtk.Label(label="Font Size:")
        box.pack_start(size_label, False, False, 0)
        
        size_spin = Gtk.SpinButton()
        size_spin.set_range(8, 72)
        size_spin.set_value(text_box.font_size)
        size_spin.set_increments(1, 5)
        box.pack_start(size_spin, False, False, 0)
        
        # Delete button
        delete_btn = Gtk.Button(label="Delete")
        delete_btn.connect('clicked', lambda w: dialog.response(Gtk.ResponseType.REJECT))
        box.pack_start(delete_btn, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            text_box.text = text_entry.get_text()
            text_box.font_size = int(size_spin.get_value())
            self._redraw_image()
        elif response == Gtk.ResponseType.REJECT:
            # Delete text box
            if text_box in self.text_boxes:
                self.text_boxes.remove(text_box)
            self.selected_text_box = None
            self._redraw_image()
        
        dialog.destroy()
    
    def _add_picture_indicator(self):
        """Add a picture icon indicator to the title bar"""
        try:
            # Get the title label to modify
            title_label = None
            for child in self.titlebar.get_children():
                if isinstance(child, Gtk.Label):
                    title_label = child
                    break
            
            if title_label:
                current_text = title_label.get_label()
                # Add picture indicator
                if not current_text.startswith("🖼️"):
                    title_label.set_label(f"🖼️ {current_text}")
        except:
            pass
    
    def save(self):
        """Override save to handle picture note data"""
        # Get the base note data from parent
        note_data = super().save() if hasattr(super(), 'save') else {}
        
        # Add picture-specific data
        if isinstance(note_data, dict):
            note_data['is_picture_note'] = True
            note_data['image_path'] = self.image_path
            note_data['text_boxes'] = [box.to_dict() for box in self.text_boxes]
        
        return note_data
    
    def get_note_data(self):
        """Override to include picture-specific data when saving"""
        # Get base note data from parent
        info = super().get_note_data()
        
        # Add picture-specific data
        info['is_picture_note'] = True
        info['image_path'] = self.image_path
        info['text_boxes'] = [box.to_dict() for box in self.text_boxes]
        
        return info
    
    def get_buffer(self):
        """For compatibility - return empty buffer since we don't use text"""
        # This is called by parent class to get note content
        # For pictures, we return an empty buffer
        buffer = Gtk.TextBuffer()
        buffer.set_text(f"[Picture Note: {self.image_path}]")
        return buffer
