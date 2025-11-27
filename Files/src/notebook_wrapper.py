#!/usr/bin/python3
"""
Note Book - Wrapper around Sticky Notes adding file organization
"""

import json
import os
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Gio, Gdk, Pango, GdkPixbuf

# Import extended Note class with Save/Minimize/Delete dropdown
# Add parent directory (Files/) to path so src. imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from src.note_extended import NoteExtended as Note
from src.note_code import NoteCode

DATA_DIR = os.path.expanduser("~/.config/notebook")
os.makedirs(DATA_DIR, exist_ok=True)

class NoteFileManager(Gtk.Window):
    """Manager window for organizing notes into files/folders"""
    
    def __init__(self):
        super().__init__(title="Note Book")
        self.note_files = {}  # {file_name: [note_ids]}
        self.note_file_metadata = {}  # {file_name: {description, instructions, color_config}}
        self.minimized_notes = []
        self.notes = []
        # Mock settings for Note class compatibility
        self.settings = Gio.Settings(schema_id='org.x.sticky')
        
        # Load Sticky's CSS so notes render properly
        css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui', 'sticky_original.css')
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
        
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.load_data()
        
        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        
        # === Custom Toolbar with Buttons ===
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        toolbar_box.set_margin_start(5)
        toolbar_box.set_margin_end(5)
        toolbar_box.set_margin_top(3)
        toolbar_box.set_margin_bottom(3)
        vbox.pack_start(toolbar_box, False, False, 0)
        
        # Load CSS for darker borders and proper sizing on buttons
        css_provider = Gtk.CssProvider()
        css_data = b"""
        .toolbar-button {
            border: 2px solid #333333;
            border-radius: 4px;
            padding: 4px 8px;
            min-width: 90px;
            min-height: 32px;
        }
        .toolbar-button:hover {
            border: 2px solid #000000;
            background-color: #f0f0f0;
        }
        """
        css_provider.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Get base path for custom icons
        icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Icons')
        
        # Helper function to create toolbar button with uniform sizing
        def create_toolbar_button(label_text, icon_path_or_name, callback, is_file=False, is_picture=False, icon_size=24):
            button = Gtk.Button()
            button.get_style_context().add_class("toolbar-button")
            button.set_size_request(100, 40)  # Fixed size for all buttons
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            box.set_halign(Gtk.Align.CENTER)
            box.set_valign(Gtk.Align.CENTER)
            
            # Icon - with configurable size, using proper GdkPixbuf scaling
            img = Gtk.Image()
            if icon_path_or_name.endswith('.png'):
                if os.path.exists(icon_path_or_name):
                    # Load with proper interpolation scaling
                    try:
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path_or_name)
                        # Scale with HIGH quality interpolation
                        scaled_pixbuf = pixbuf.scale_simple(icon_size, icon_size, GdkPixbuf.InterpType.HYPER)
                        img.set_from_pixbuf(scaled_pixbuf)
                    except:
                        # Fallback to old method
                        img = Gtk.Image.new_from_file(icon_path_or_name)
                        img.set_pixel_size(icon_size)
                else:
                    if is_file:
                        img = Gtk.Image.new_from_icon_name('folder-new', Gtk.IconSize.BUTTON)
                    elif is_picture:
                        img = Gtk.Image.new_from_icon_name('image-x-generic', Gtk.IconSize.BUTTON)
                    else:
                        img = Gtk.Image.new_from_icon_name('document-new', Gtk.IconSize.BUTTON)
            else:
                img = Gtk.Image.new_from_icon_name(icon_path_or_name, Gtk.IconSize.BUTTON)
            
            # Label
            lbl = Gtk.Label(label=label_text)
            font_desc = Pango.FontDescription("Sans 9")
            lbl.override_font(font_desc)
            
            box.pack_start(img, False, False, 0)
            box.pack_start(lbl, False, False, 0)
            box.show_all()
            
            button.add(box)
            button.connect("clicked", callback)
            button.show()
            
            return button
        
        # === New Note Button ===
        new_note_btn = create_toolbar_button("New Note", os.path.join(icons_path, 'Add Note.png'), self.create_new_note)
        toolbar_box.pack_start(new_note_btn, False, False, 0)
        
        # === New Code Button ===
        new_code_btn = create_toolbar_button("New Code", os.path.join(icons_path, 'Code Template.png'), self.create_new_code_note)
        toolbar_box.pack_start(new_code_btn, False, False, 0)
        
        # === New Picture Button ===
        new_pic_btn = create_toolbar_button("New Picture", os.path.join(icons_path, 'Picture.png'), self.placeholder_new_picture, is_picture=True)
        toolbar_box.pack_start(new_pic_btn, False, False, 0)
        
        # === New File Button (larger icon) ===
        new_file_btn = create_toolbar_button("New File", os.path.join(icons_path, 'Folder Icon.png'), self.create_note_file, is_file=True, icon_size=32)
        toolbar_box.pack_start(new_file_btn, False, False, 0)
        
        # Paned layout
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(paned, True, True, 0)
        
        # Left panel: Note Files
        left_scroll = Gtk.ScrolledWindow()
        left_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        left_scroll.set_size_request(250, -1)
        paned.add1(left_scroll)
        
        self.file_listbox = Gtk.ListBox()
        self.file_listbox.connect("row-activated", self.on_file_selected)
        left_scroll.add(self.file_listbox)
        
        # Right panel container
        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        paned.add2(right_vbox)
        
        # Right panel: Notes in selected file
        right_scroll = Gtk.ScrolledWindow()
        right_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        right_vbox.pack_start(right_scroll, True, True, 0)
        
        self.note_listbox = Gtk.ListBox()
        self.note_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.note_listbox.connect('row-selected', self.on_note_row_selected)
        right_scroll.add(self.note_listbox)
        
        # Bottom action bar
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_bar.set_margin_start(10)
        action_bar.set_margin_end(10)
        action_bar.set_margin_top(5)
        action_bar.set_margin_bottom(5)
        right_vbox.pack_start(action_bar, False, False, 0)
        
        self.open_btn = Gtk.Button(label="Open")
        self.open_btn.set_sensitive(False)
        self.open_btn.connect("clicked", self.action_open_note)
        action_bar.pack_start(self.open_btn, True, True, 0)
        
        self.settings_btn = Gtk.Button(label="Settings")
        self.settings_btn.set_sensitive(False)
        self.settings_btn.connect("clicked", self.action_note_settings)
        action_bar.pack_start(self.settings_btn, True, True, 0)
        
        self.up_btn = Gtk.Button(label="Up ↑")
        self.up_btn.set_sensitive(False)
        self.up_btn.connect("clicked", self.action_move_up)
        action_bar.pack_start(self.up_btn, True, True, 0)
        
        self.down_btn = Gtk.Button(label="Down ↓")
        self.down_btn.set_sensitive(False)
        self.down_btn.connect("clicked", self.action_move_down)
        action_bar.pack_start(self.down_btn, True, True, 0)
        
        self.delete_btn = Gtk.Button(label="Delete")
        self.delete_btn.set_sensitive(False)
        self.delete_btn.connect("clicked", self.action_delete_note)
        action_bar.pack_start(self.delete_btn, True, True, 0)
        
        # Track selected note for action bar
        self.selected_note_id = None
        self.selected_note_data = None
        
        # Track current file for DND
        self.current_file_name = None
        
        self.populate_file_list()
        
        # Select first file by default if not already set
        if not self.current_file_name and self.note_files:
            first_file = sorted(self.note_files.keys())[0]
            self.current_file_name = first_file
            # Trigger selection to display notes
            for row in self.file_listbox.get_children():
                if hasattr(row, 'file_name') and row.file_name == first_file:
                    self.file_listbox.select_row(row)
                    # Actually trigger the callback to populate notes
                    self.on_file_selected(self.file_listbox, row)
                    break
        
        self.connect("delete-event", self.on_close)
        self.show_all()
    
    
    def create_new_note(self, widget):
        """Create a new note with Sticky GUI"""
        # Simple position staggering
        x = 100 + len(self.notes) * 20
        y = 100 + len(self.notes) * 20
        
        info = {'x': x, 'y': y}
        try:
            note = Note(self, self, info)
            self.notes.append(note)
            # Connect to note's update signal to refresh list when title/color changes
            note.connect('update', self.on_note_updated)
        except Exception as e:
            print(f"Error creating note: {e}")
            import traceback
            traceback.print_exc()

    def create_new_code_note(self, widget):
        """Create a new Code Note directly from toolbar"""
        x = 100 + len(self.notes) * 20
        y = 100 + len(self.notes) * 20
        info = {'x': x, 'y': y}
        try:
            note = NoteCode(self, self, info)
            self.notes.append(note)
            note.connect('update', self.on_note_updated)
        except Exception as e:
            print(f"Error creating code note: {e}")
            import traceback
            traceback.print_exc()
    
    def placeholder_new_picture(self, widget):
        """Create a new Picture entry - open file chooser to select image"""
        if not self.current_file_name:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No File Selected"
            )
            dialog.format_secondary_text("Please select or create a note file first.")
            dialog.run()
            dialog.destroy()
            return
        
        # Open file chooser for image
        file_dialog = Gtk.FileChooserDialog(
            title="Select Picture to Add",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )
        
        # Add image file filter
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Image Files")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_mime_type("image/bmp")
        image_filter.add_mime_type("image/gif")
        image_filter.add_mime_type("image/webp")
        image_filter.add_pattern("*.png")
        image_filter.add_pattern("*.jpg")
        image_filter.add_pattern("*.jpeg")
        image_filter.add_pattern("*.bmp")
        image_filter.add_pattern("*.gif")
        file_dialog.add_filter(image_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        file_dialog.add_filter(all_filter)
        
        # Set home directory as default
        file_dialog.set_current_folder(os.path.expanduser("~"))
        
        response = file_dialog.run()
        if response == Gtk.ResponseType.OK:
            image_path = file_dialog.get_filename()
            file_dialog.destroy()
            
            # Create picture note entry (without opening a window)
            self._create_picture_note_entry(image_path)
        else:
            file_dialog.destroy()
    
    def _create_picture_note_entry(self, image_path):
        """Create and save a picture note entry without opening a window"""
        try:
            # Generate unique ID for this picture
            import uuid
            note_id = str(uuid.uuid4())
            
            # Get image filename for title
            image_filename = os.path.basename(image_path)
            title_without_ext = os.path.splitext(image_filename)[0]
            
            # Create picture note data
            picture_data = {
                'id': note_id,
                'type': 'picture',
                'title': title_without_ext,
                'image_path': image_path,
                'color': 'yellow',  # Default color
                'tag': '',  # No tag initially
                'is_picture_note': True,
                'created': __import__('datetime').datetime.now().isoformat()
            }
            
            # Save the picture data
            note_path = os.path.join(DATA_DIR, f"{note_id}.json")
            with open(note_path, 'w') as f:
                __import__('json').dump(picture_data, f, indent=2)
            
            # Add to current file's note list
            if self.current_file_name not in self.note_files:
                self.note_files[self.current_file_name] = []
            self.note_files[self.current_file_name].append(note_id)
            
            # Save the file organization
            self.save_data()
            
            # Refresh the note list
            self.refresh_current_file_view()
            
            print(f"Picture note created: {image_filename}")
        except Exception as e:
            print(f"Error creating picture note: {e}")
            import traceback
            traceback.print_exc()
            
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Creating Picture Note"
            )
            error_dialog.format_secondary_text(f"Could not create picture note:\n{str(e)}")
            error_dialog.run()
            error_dialog.destroy()
    
    def new_note(self, button=None, parent=None):
        """Create a new note matching the parent's type and color but without text"""
        x = 100 + len(self.notes) * 20
        y = 100 + len(self.notes) * 20
        
        # If parent exists, match its color and type
        if parent:
            info = {
                'x': x,
                'y': y,
                'color': parent.color,
                'is_code_note': getattr(parent, 'is_code_note', False)
            }
            
            # Create matching note type
            if info.get('is_code_note'):
                from src.note_code import NoteCode
                note = NoteCode(self, self, info)
            else:
                note = Note(self, self, info)
        else:
            # No parent - create default text note
            info = {'x': x, 'y': y}
            note = Note(self, self, info)
        
        self.notes.append(note)
        note.connect('update', self.on_note_updated)
        return note
    
    def duplicate_note(self, source_note):
        """Duplicate a note with all its content, type, and color"""
        # Get complete info from source note
        if hasattr(source_note, 'get_info'):
            info = source_note.get_info()
        else:
            info = {}
        
        # Offset position
        info['x'] = info.get('x', 100) + 50
        info['y'] = info.get('y', 100) + 50
        
        # Create matching note type
        if info.get('is_code_note'):
            from src.note_code import NoteCode
            note = NoteCode(self, self, info)
        else:
            note = Note(self, self, info)
        
        self.notes.append(note)
        note.connect('update', self.on_note_updated)
        return note
    
    def save_note_to_file(self, note):
        """Save note data and index it under its Note File"""
        import uuid
        note_data = note.get_note_data()
        
        # Generate ID if missing
        if not note_data.get('id'):
            note_data['id'] = str(uuid.uuid4())
            note.note_id = note_data['id']
        
        # Write note JSON
        note_path = os.path.join(DATA_DIR, f"note_{note_data['id']}.json")
        with open(note_path, 'w') as f:
            json.dump(note_data, f, indent=2)
        
        # Index under Note File
        if note_data.get('note_file'):
            file_name = note_data['note_file']
            if file_name in self.note_files:
                if note_data['id'] not in self.note_files[file_name]:
                    self.note_files[file_name].append(note_data['id'])
                    self.save_data()
                    self.populate_file_list()
                # Always refresh to show changes
                for row in self.file_listbox.get_children():
                    if hasattr(row, 'file_name') and row.file_name == file_name:
                        self.on_file_selected(self.file_listbox, row)
                        break
    
    def prompt_save_note(self, note):
        """Prompt user to select a Note File for saving"""
        if not self.note_files:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No Note Files"
            )
            dialog.format_secondary_text("Create a Note File first before saving notes.")
            dialog.run()
            dialog.destroy()
            return
        
        dialog = Gtk.Dialog(
            title="Save to Note File",
            transient_for=self,
            flags=0
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
        
        label = Gtk.Label(label="Select Note File:")
        box.pack_start(label, False, False, 5)
        
        combo = Gtk.ComboBoxText()
        for file_name in sorted(self.note_files.keys()):
            combo.append_text(file_name)
        if self.note_files:
            combo.set_active(0)
        box.pack_start(combo, False, False, 5)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            selected_file = combo.get_active_text()
            if selected_file:
                note.note_file = selected_file
                self.save_note_to_file(note)
        
        dialog.destroy()
    
    def draw_color_indicator(self, widget, cr, color_code):
        """Draw a colored square indicator"""
        # Parse hex color
        if color_code.startswith('#'):
            r = int(color_code[1:3], 16) / 255.0
            g = int(color_code[3:5], 16) / 255.0
            b = int(color_code[5:7], 16) / 255.0
        else:
            r, g, b = 0.96, 0.97, 0.03  # yellow fallback
        
        # Draw filled rectangle
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, 16, 16)
        cr.fill()
        
        # Draw border
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.rectangle(0, 0, 16, 16)
        cr.stroke()
        
        return False
    
    def on_drag_data_get(self, widget, drag_context, data, info, time):
        """Provide data for drag operation"""
        data.set_text(widget.note_id, -1)
    
    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        """Handle drop operation - reorder notes"""
        if not self.current_file_name:
            return
        
        dragged_id = data.get_text()
        target_id = widget.note_id
        
        if dragged_id == target_id:
            return
        
        # Reorder in the note_files list
        note_ids = self.note_files[self.current_file_name]
        
        if dragged_id in note_ids and target_id in note_ids:
            # Remove dragged item
            note_ids.remove(dragged_id)
            # Insert before target
            target_index = note_ids.index(target_id)
            note_ids.insert(target_index, dragged_id)
            
            # Save and auto-refresh
            self.save_data()
            self.refresh_current_file_view()
    
    def move_note_up(self, widget, file_name, note_id):
        """Move note up in the list"""
        if file_name not in self.note_files:
            return
        
        note_ids = self.note_files[file_name]
        if note_id not in note_ids:
            return
        
        index = note_ids.index(note_id)
        if index > 0:  # Can move up
            note_ids[index], note_ids[index - 1] = note_ids[index - 1], note_ids[index]
            self.save_data()
            self.populate_file_list()
            # Force refresh by calling on_file_selected directly
            for row in self.file_listbox.get_children():
                if hasattr(row, 'file_name') and row.file_name == file_name:
                    self.on_file_selected(self.file_listbox, row)
                    break
            # Re-select the note
            self.refresh_and_select_note(note_id)
    
    def move_note_down(self, widget, file_name, note_id):
        """Move note down in the list"""
        if file_name not in self.note_files:
            return
        
        note_ids = self.note_files[file_name]
        if note_id not in note_ids:
            return
        
        index = note_ids.index(note_id)
        if index < len(note_ids) - 1:  # Can move down
            note_ids[index], note_ids[index + 1] = note_ids[index + 1], note_ids[index]
            self.save_data()
            self.populate_file_list()
            # Force refresh by calling on_file_selected directly
            for row in self.file_listbox.get_children():
                if hasattr(row, 'file_name') and row.file_name == file_name:
                    self.on_file_selected(self.file_listbox, row)
                    break
            # Re-select the note
            self.refresh_and_select_note(note_id)
    
    def delete_saved_note(self, widget, file_name, note_id):
        """Delete a saved note from a Note File"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete Note?"
        )
        dialog.format_secondary_text("Are you sure you want to delete this note?")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Remove from index
            if file_name in self.note_files and note_id in self.note_files[file_name]:
                self.note_files[file_name].remove(note_id)
                self.save_data()
                self.populate_file_list()
            
            # Delete note JSON file
            import os
            note_path = os.path.join(DATA_DIR, f"note_{note_id}.json")
            if os.path.exists(note_path):
                os.remove(note_path)
            
            # Clear selection
            self.selected_note_id = None
            self.selected_note_data = None
            self.note_listbox.unselect_all()
            
            # Force refresh by calling on_file_selected directly
            for row in self.file_listbox.get_children():
                if hasattr(row, 'file_name') and row.file_name == file_name:
                    self.on_file_selected(self.file_listbox, row)
                    break
    
    def create_note_file(self, widget):
        """Create a new note file/folder"""
        dialog = Gtk.Dialog(
            title="New Note File",
            transient_for=self,
            flags=0
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
        
        label = Gtk.Label(label="Note File Name:")
        box.pack_start(label, False, False, 5)
        
        entry = Gtk.Entry()
        box.pack_start(entry, False, False, 5)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name and name not in self.note_files:
                self.note_files[name] = []
                self.save_data()
                self.populate_file_list()
        
        dialog.destroy()
    
    def populate_file_list(self):
        """Populate the note files list"""
        for child in self.file_listbox.get_children():
            self.file_listbox.remove(child)
        
        # Create radio button group (first will be the group leader)
        radio_group = None
        
        for file_name in sorted(self.note_files.keys()):
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_margin_start(10)
            hbox.set_margin_end(10)
            hbox.set_margin_top(5)
            hbox.set_margin_bottom(5)
            
            # Radio button for selection
            if radio_group is None:
                radio_btn = Gtk.RadioButton()
                radio_group = radio_btn
            else:
                radio_btn = Gtk.RadioButton.new_from_widget(radio_group)
            
            # Set active if this is the current file
            if file_name == self.current_file_name:
                radio_btn.set_active(True)
            
            radio_btn.connect('toggled', self.on_file_radio_toggled, file_name)
            hbox.pack_start(radio_btn, False, False, 0)
            
            label = Gtk.Label(label=f"📁 {file_name}")
            label.set_xalign(0)
            hbox.pack_start(label, True, True, 0)
            
            count = len(self.note_files[file_name])
            count_label = Gtk.Label(label=f"({count})")
            hbox.pack_start(count_label, False, False, 0)
            
            # Settings button for file metadata
            settings_btn = Gtk.Button(label="⚙")
            settings_btn.set_relief(Gtk.ReliefStyle.NONE)
            settings_btn.set_tooltip_text("Edit Description & Instructions")
            settings_btn.connect("clicked", self.edit_file_metadata, file_name)
            hbox.pack_start(settings_btn, False, False, 0)
            
            delete_btn = Gtk.Button(label="✖")
            delete_btn.set_relief(Gtk.ReliefStyle.NONE)
            delete_btn.connect("clicked", self.delete_note_file, file_name)
            hbox.pack_start(delete_btn, False, False, 0)
            
            row.add(hbox)
            row.file_name = file_name
            self.file_listbox.add(row)
        
        self.file_listbox.show_all()
    
    def delete_note_file(self, widget, file_name):
        """Delete a note file"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete Note File?"
        )
        dialog.format_secondary_text(f"Delete '{file_name}'? Notes won't be deleted, just the organization.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            del self.note_files[file_name]
            self.save_data()
            self.populate_file_list()
            
            for child in self.note_listbox.get_children():
                self.note_listbox.remove(child)
    
    def on_file_radio_toggled(self, radio_btn, file_name):
        """Handle radio button toggle for file selection"""
        if radio_btn.get_active():
            self.current_file_name = file_name
            # Also select the row in listbox to show notes
            for row in self.file_listbox.get_children():
                if hasattr(row, 'file_name') and row.file_name == file_name:
                    self.file_listbox.select_row(row)
                    break
    
    def on_file_selected(self, listbox, row):
        """Show notes in selected file"""
        if row is None:
            return
        
        file_name = row.file_name
        self.current_file_name = file_name
        
        for child in self.note_listbox.get_children():
            self.note_listbox.remove(child)
        
        note_ids = self.note_files.get(file_name, [])
        
        # Build hierarchy for indentation
        note_hierarchy = self.build_note_hierarchy(note_ids)
        
        for seq_num, (note_id, depth) in enumerate(note_hierarchy, 1):
            note_data = self.load_note_by_id(note_id)
            if note_data:
                row = Gtk.ListBoxRow()
                row.note_id = note_id
                
                # Enable drag and drop for reordering
                row.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.MOVE)
                row.drag_source_add_text_targets()
                row.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
                row.drag_dest_add_text_targets()
                row.connect('drag-data-get', self.on_drag_data_get)
                row.connect('drag-data-received', self.on_drag_data_received)
                
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=13)
                # Add indentation based on depth (25px per level, 25% larger)
                indent = 13 + (depth * 25)
                hbox.set_margin_start(indent)
                hbox.set_margin_end(13)
                hbox.set_margin_top(10)
                hbox.set_margin_bottom(10)
                
                # Sequential note number (25% larger)
                seq_label = Gtk.Label(label=f"{seq_num}.")
                seq_label.set_xalign(0)
                seq_label.set_size_request(38, -1)
                font_desc = Pango.FontDescription("Sans Bold 14")
                seq_label.override_font(font_desc)
                hbox.pack_start(seq_label, False, False, 0)
                
                # Color indicator box (25% larger)
                color = note_data.get('color', 'yellow')
                from sticky_unmodified import COLOR_CODES
                color_code = COLOR_CODES.get(color, '#f6f907')
                color_box = Gtk.DrawingArea()
                color_box.set_size_request(24, 24)
                color_box.connect('draw', self.draw_color_indicator, color_code)
                hbox.pack_start(color_box, False, False, 0)

                # Note type indicator icon (25% larger)
                icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Icons')
                if note_data.get('is_picture_note', False):
                    # Picture note indicator
                    picture_icon_path = os.path.join(icons_path, 'Picture.png')
                    picture_img = Gtk.Image()
                    if os.path.exists(picture_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(picture_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            picture_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            picture_img = Gtk.Image.new_from_file(picture_icon_path)
                            picture_img.set_pixel_size(24)
                    else:
                        picture_img = Gtk.Image.new_from_icon_name('image-x-generic', Gtk.IconSize.BUTTON)
                    hbox.pack_start(picture_img, False, False, 0)
                elif note_data.get('is_code_note', False):
                    # Code note indicator
                    code_icon_path = os.path.join(icons_path, 'Code Template.png')
                    code_img = Gtk.Image()
                    if os.path.exists(code_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(code_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            code_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            code_img = Gtk.Image.new_from_file(code_icon_path)
                            code_img.set_pixel_size(24)
                    else:
                        code_img = Gtk.Image.new_from_icon_name('applications-development', Gtk.IconSize.BUTTON)
                    hbox.pack_start(code_img, False, False, 0)
                else:
                    # Text note indicator
                    text_icon_path = os.path.join(icons_path, 'Add Note.png')
                    text_img = Gtk.Image()
                    if os.path.exists(text_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(text_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            text_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            text_img = Gtk.Image.new_from_file(text_icon_path)
                            text_img.set_pixel_size(24)
                    else:
                        text_img = Gtk.Image.new_from_icon_name('document-properties', Gtk.IconSize.BUTTON)
                    hbox.pack_start(text_img, False, False, 0)
                
                # ID Tag if assigned
                id_tag = note_data.get('id_tag', '')
                if id_tag:
                    tag_label = Gtk.Label(label=f"[{id_tag}]")
                    tag_label.set_xalign(0)
                    font_desc = Pango.FontDescription("Sans Bold 12")
                    tag_label.override_font(font_desc)
                    hbox.pack_start(tag_label, False, False, 5)
                
                title = note_data.get('title', '')
                text = note_data.get('text', '')
                preview = title if title else (text[:50] + "..." if len(text) > 50 else text)
                
                label = Gtk.Label(label=preview or "(Empty note)")
                label.set_xalign(0)
                font_desc = Pango.FontDescription("Sans 12")
                label.override_font(font_desc)
                hbox.pack_start(label, True, True, 0)
                
                # Store note data in row for action bar
                row.note_data = note_data
                
                row.add(hbox)
                self.note_listbox.add(row)
        
        self.note_listbox.show_all()
    
    def refresh_current_file_view(self):
        """Refresh the currently selected file's note list"""
        if not self.current_file_name:
            return
        
        # Clear the note list
        for child in self.note_listbox.get_children():
            self.note_listbox.remove(child)
        
        # Rebuild the note list for current file
        note_ids = self.note_files.get(self.current_file_name, [])
        note_hierarchy = self.build_note_hierarchy(note_ids)
        
        for seq_num, (note_id, depth) in enumerate(note_hierarchy, 1):
            note_data = self.load_note_by_id(note_id)
            if note_data:
                row = Gtk.ListBoxRow()
                row.note_id = note_id
                
                # Enable drag and drop for reordering
                row.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.MOVE)
                row.drag_source_add_text_targets()
                row.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
                row.drag_dest_add_text_targets()
                row.connect('drag-data-get', self.on_drag_data_get)
                row.connect('drag-data-received', self.on_drag_data_received)
                
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=13)
                indent = 13 + (depth * 25)
                hbox.set_margin_start(indent)
                hbox.set_margin_end(13)
                hbox.set_margin_top(10)
                hbox.set_margin_bottom(10)
                
                seq_label = Gtk.Label(label=f"{seq_num}.")
                seq_label.set_xalign(0)
                seq_label.set_size_request(38, -1)
                font_desc = Pango.FontDescription("Sans Bold 14")
                seq_label.override_font(font_desc)
                hbox.pack_start(seq_label, False, False, 0)
                
                color = note_data.get('color', 'yellow')
                from sticky_unmodified import COLOR_CODES
                color_code = COLOR_CODES.get(color, '#f6f907')
                color_box = Gtk.DrawingArea()
                color_box.set_size_request(24, 24)
                color_box.connect('draw', self.draw_color_indicator, color_code)
                hbox.pack_start(color_box, False, False, 0)
                
                # Note type indicator icon
                icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Icons')
                if note_data.get('is_picture_note', False):
                    # Picture note indicator
                    picture_icon_path = os.path.join(icons_path, 'Picture.png')
                    picture_img = Gtk.Image()
                    if os.path.exists(picture_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(picture_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            picture_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            picture_img = Gtk.Image.new_from_file(picture_icon_path)
                            picture_img.set_pixel_size(24)
                    else:
                        picture_img = Gtk.Image.new_from_icon_name('image-x-generic', Gtk.IconSize.BUTTON)
                    hbox.pack_start(picture_img, False, False, 0)
                elif note_data.get('is_code_note', False):
                    # Code note indicator
                    code_icon_path = os.path.join(icons_path, 'Code Template.png')
                    code_img = Gtk.Image()
                    if os.path.exists(code_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(code_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            code_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            code_img = Gtk.Image.new_from_file(code_icon_path)
                            code_img.set_pixel_size(24)
                    else:
                        code_img = Gtk.Image.new_from_icon_name('applications-development', Gtk.IconSize.BUTTON)
                    hbox.pack_start(code_img, False, False, 0)
                else:
                    # Text note indicator
                    text_icon_path = os.path.join(icons_path, 'Add Note.png')
                    text_img = Gtk.Image()
                    if os.path.exists(text_icon_path):
                        try:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(text_icon_path)
                            scaled_pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
                            text_img.set_from_pixbuf(scaled_pixbuf)
                        except:
                            text_img = Gtk.Image.new_from_file(text_icon_path)
                            text_img.set_pixel_size(24)
                    else:
                        text_img = Gtk.Image.new_from_icon_name('document-properties', Gtk.IconSize.BUTTON)
                    hbox.pack_start(text_img, False, False, 0)
                
                id_tag = note_data.get('id_tag', '')
                if id_tag:
                    tag_label = Gtk.Label(label=f"[{id_tag}]")
                    tag_label.set_xalign(0)
                    font_desc = Pango.FontDescription("Sans Bold 12")
                    tag_label.override_font(font_desc)
                    hbox.pack_start(tag_label, False, False, 5)
                
                title = note_data.get('title', '')
                text = note_data.get('text', '')
                preview = title if title else (text[:50] + "..." if len(text) > 50 else text)
                
                label = Gtk.Label(label=preview or "(Empty note)")
                label.set_xalign(0)
                font_desc = Pango.FontDescription("Sans 12")
                label.override_font(font_desc)
                hbox.pack_start(label, True, True, 0)
                
                row.note_data = note_data
                row.add(hbox)
                self.note_listbox.add(row)
        
        self.note_listbox.show_all()
    
    def refresh_and_select_note(self, note_id):
        """Refresh note list and re-select specific note"""
        # Refresh the list
        self.refresh_current_file_view()
        
        # Find and select the note with matching ID
        for row in self.note_listbox.get_children():
            if hasattr(row, 'note_id') and row.note_id == note_id:
                self.note_listbox.select_row(row)
                break
    
    def build_note_hierarchy(self, note_ids):
        """Build hierarchical list of (note_id, depth) tuples"""
        # Load all note data
        notes = {}
        for note_id in note_ids:
            note_data = self.load_note_by_id(note_id)
            if note_data:
                notes[note_id] = note_data
        
        # Build parent-child relationships
        children = {}  # parent_id -> [child_ids]
        for note_id, data in notes.items():
            parent_id = data.get('parent_id')
            if parent_id:
                if parent_id not in children:
                    children[parent_id] = []
                children[parent_id].append(note_id)
        
        # Build hierarchical list
        hierarchy = []
        visited = set()
        
        def add_note_and_children(note_id, depth):
            if note_id in visited:
                return
            visited.add(note_id)
            hierarchy.append((note_id, depth))
            
            # Add children recursively
            if note_id in children:
                for child_id in children[note_id]:
                    add_note_and_children(child_id, depth + 1)
        
        # Add all notes, starting with top-level (no parent)
        for note_id in note_ids:
            if note_id in notes:
                parent_id = notes[note_id].get('parent_id')
                # Only add top-level notes here, children will be added recursively
                if not parent_id or parent_id not in notes:
                    add_note_and_children(note_id, 0)
        
        return hierarchy
    
    def on_note_row_selected(self, listbox, row):
        """Handle note selection - enable/disable action bar buttons"""
        if row is None:
            # No selection - disable all buttons
            self.open_btn.set_sensitive(False)
            self.settings_btn.set_sensitive(False)
            self.up_btn.set_sensitive(False)
            self.down_btn.set_sensitive(False)
            self.delete_btn.set_sensitive(False)
            self.selected_note_id = None
            self.selected_note_data = None
        else:
            # Note selected - enable buttons
            self.selected_note_id = row.note_id
            self.selected_note_data = row.note_data
            
            self.open_btn.set_sensitive(True)
            self.settings_btn.set_sensitive(True)
            self.delete_btn.set_sensitive(True)
            
            # Enable/disable up/down based on position
            if self.current_file_name:
                note_ids = self.note_files.get(self.current_file_name, [])
                if self.selected_note_id in note_ids:
                    index = note_ids.index(self.selected_note_id)
                    self.up_btn.set_sensitive(index > 0)
                    self.down_btn.set_sensitive(index < len(note_ids) - 1)
    
    def action_open_note(self, widget):
        """Open the selected note"""
        if self.selected_note_data:
            self.open_saved_note(widget, self.selected_note_data)
    
    def action_note_settings(self, widget):
        """Open settings for selected note"""
        if self.selected_note_id:
            self.edit_note_metadata(widget, self.selected_note_id)
    
    def action_move_up(self, widget):
        """Move selected note up"""
        if self.selected_note_id and self.current_file_name:
            self.move_note_up(widget, self.current_file_name, self.selected_note_id)
    
    def action_move_down(self, widget):
        """Move selected note down"""
        if self.selected_note_id and self.current_file_name:
            self.move_note_down(widget, self.current_file_name, self.selected_note_id)
    
    def action_delete_note(self, widget):
        """Delete selected note"""
        if self.selected_note_id and self.current_file_name:
            self.delete_saved_note(widget, self.current_file_name, self.selected_note_id)
    
    def on_note_updated(self, note):
        """Called when a note is updated (title/color change)"""
        # If note is saved to a file, refresh that file's view
        if hasattr(note, 'note_file') and note.note_file:
            # Also save the updated note data
            if hasattr(note, 'note_id') and note.note_id:
                note_data = note.get_note_data()
                note_path = os.path.join(DATA_DIR, f"note_{note.note_id}.json")
                with open(note_path, 'w') as f:
                    json.dump(note_data, f, indent=2)
            
            # Refresh if viewing the note's file
            if note.note_file == self.current_file_name:
                self.refresh_current_file_view()
    
    def open_saved_note(self, widget, note_data):
        """Open a saved note"""
        try:
            # Check if this is a picture note
            if note_data.get('is_picture_note', False):
                from src.note_picture import NotePicture
                note = NotePicture(self, self, note_data)
            # Check if this is a code note
            elif note_data.get('is_code_note', False):
                note = NoteCode(self, self, note_data)
            else:
                note = Note(self, self, note_data)
            self.notes.append(note)
            # Connect to note's update signal to refresh list when title/color changes
            note.connect('update', self.on_note_updated)
        except Exception as e:
            print(f"Error opening note: {e}")
            import traceback
            traceback.print_exc()
    
    def load_note_by_id(self, note_id):
        """Load note data by ID - handles both regular notes and picture notes"""
        # Try regular note format first
        file_path = os.path.join(DATA_DIR, f"note_{note_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        # Try picture note format
        file_path = os.path.join(DATA_DIR, f"{note_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def save_data(self):
        """Save note files organization and metadata"""
        data = {
            'note_files': self.note_files,
            'note_file_metadata': self.note_file_metadata
        }
        file_path = os.path.join(DATA_DIR, "notebook.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        """Load note files organization"""
        file_path = os.path.join(DATA_DIR, "notebook.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                note_files_raw = data.get('note_files', {})
                
                # Handle both old and new formats
                # New format: {"file": {"notes": [ids], "description": "...", "instructions": "..."}}
                # Old format: {"file": [ids]}
                self.note_files = {}
                self.note_file_metadata = {}
                for file_name, file_data in note_files_raw.items():
                    if isinstance(file_data, dict) and 'notes' in file_data:
                        # New format with nested "notes"
                        self.note_files[file_name] = file_data['notes']
                    elif isinstance(file_data, list):
                        # Old format, direct list
                        self.note_files[file_name] = file_data
                    else:
                        # Unknown format, initialize empty
                        self.note_files[file_name] = []
                
                # Load separate metadata structures
                raw_file_metadata = data.get('note_file_metadata', {})
                for file_name in self.note_files.keys():
                    if file_name in raw_file_metadata:
                        metadata = raw_file_metadata[file_name]
                        # Ensure color_config and number_config exist
                        if 'color_config' not in metadata:
                            metadata['color_config'] = {}
                        if 'number_config' not in metadata:
                            metadata['number_config'] = {}
                        self.note_file_metadata[file_name] = metadata
                    else:
                        self.note_file_metadata[file_name] = {
                            'description': '',
                            'instructions': '',
                            'color_config': {},
                            'number_config': {}
                        }
    
    def edit_file_metadata(self, widget, file_name):
        """Edit Description, Instructions, and Color Configuration for a Note File"""
        if file_name not in self.note_file_metadata:
            self.note_file_metadata[file_name] = {'description': '', 'instructions': '', 'color_config': {}}
        
        metadata = self.note_file_metadata[file_name]
        if 'color_config' not in metadata:
            metadata['color_config'] = {}
        
        dialog = Gtk.Dialog(
            title="Note File Settings",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(700, 600)
        
        box = dialog.get_content_area()
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_spacing(10)
        
        # Notebook for tabs
        notebook = Gtk.Notebook()
        box.pack_start(notebook, True, True, 0)
        
        # === Tab 1: File Settings ===
        file_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        file_tab.set_margin_start(10)
        file_tab.set_margin_end(10)
        file_tab.set_margin_top(10)
        file_tab.set_margin_bottom(10)
        
        # Description
        desc_label = Gtk.Label(label="<b>Description:</b>", use_markup=True)
        desc_label.set_xalign(0)
        file_tab.pack_start(desc_label, False, False, 0)
        
        desc_frame = Gtk.Frame()
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_size_request(-1, 100)
        file_desc_text = Gtk.TextView()
        file_desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
        file_desc_buffer = file_desc_text.get_buffer()
        file_desc_buffer.set_text(metadata.get('description', ''))
        desc_scroll.add(file_desc_text)
        desc_frame.add(desc_scroll)
        file_tab.pack_start(desc_frame, True, True, 0)
        
        # Instructions
        inst_label = Gtk.Label(label="<b>Instructions:</b>", use_markup=True)
        inst_label.set_xalign(0)
        file_tab.pack_start(inst_label, False, False, 0)
        
        inst_frame = Gtk.Frame()
        inst_scroll = Gtk.ScrolledWindow()
        inst_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        inst_scroll.set_size_request(-1, 100)
        file_inst_text = Gtk.TextView()
        file_inst_text.set_wrap_mode(Gtk.WrapMode.WORD)
        file_inst_buffer = file_inst_text.get_buffer()
        file_inst_buffer.set_text(metadata.get('instructions', ''))
        inst_scroll.add(file_inst_text)
        inst_frame.add(inst_scroll)
        file_tab.pack_start(inst_frame, True, True, 0)
        
        notebook.append_page(file_tab, Gtk.Label(label="File Settings"))
        
        # === Tab 2: Color Configuration ===
        color_tab_scroll = Gtk.ScrolledWindow()
        color_tab_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        color_grid = Gtk.Grid()
        color_grid.set_column_spacing(10)
        color_grid.set_row_spacing(10)
        color_grid.set_margin_start(10)
        color_grid.set_margin_end(10)
        color_grid.set_margin_top(10)
        color_grid.set_margin_bottom(10)
        color_tab_scroll.add(color_grid)
        
        from sticky_unmodified import COLORS
        color_entries = {}
        
        row = 0
        for color_name in sorted(COLORS.keys()):
            # Color name label
            color_label = Gtk.Label(label=f"<b>{color_name.capitalize()}:</b>", use_markup=True)
            color_label.set_xalign(0)
            color_grid.attach(color_label, 0, row, 1, 1)
            
            # Get existing color config
            color_config = metadata['color_config'].get(color_name, {'description': '', 'instructions': ''})
            
            # Description entry
            desc_frame = Gtk.Frame(label="Description")
            desc_text = Gtk.TextView()
            desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
            desc_text.set_size_request(250, 60)
            desc_buffer = desc_text.get_buffer()
            desc_buffer.set_text(color_config.get('description', ''))
            desc_frame.add(desc_text)
            color_grid.attach(desc_frame, 1, row, 1, 1)
            
            # Instructions entry
            inst_frame = Gtk.Frame(label="Instructions")
            inst_text = Gtk.TextView()
            inst_text.set_wrap_mode(Gtk.WrapMode.WORD)
            inst_text.set_size_request(250, 60)
            inst_buffer = inst_text.get_buffer()
            inst_buffer.set_text(color_config.get('instructions', ''))
            inst_frame.add(inst_text)
            color_grid.attach(inst_frame, 2, row, 1, 1)
            
            color_entries[color_name] = (desc_buffer, inst_buffer)
            row += 1
        
        notebook.append_page(color_tab_scroll, Gtk.Label(label="Color Configuration"))
        
        # === Tab 3: ID Tag Configuration ===
        number_tab_scroll = Gtk.ScrolledWindow()
        number_tab_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        number_grid = Gtk.Grid()
        number_grid.set_column_spacing(10)
        number_grid.set_row_spacing(10)
        number_grid.set_margin_start(10)
        number_grid.set_margin_end(10)
        number_grid.set_margin_top(10)
        number_grid.set_margin_bottom(10)
        number_tab_scroll.add(number_grid)
        
        # Get existing number config or initialize
        if 'number_config' not in metadata:
            metadata['number_config'] = {}
        
        # Find all unique ID tags used in this file's notes
        used_tags = set()
        tag_note_data = {}  # Map tag to note data for auto-population
        for note_id in self.note_files.get(file_name, []):
            note_data = self.load_note_by_id(note_id)
            if note_data and 'id_tag' in note_data and note_data['id_tag']:
                tag = str(note_data['id_tag'])
                used_tags.add(tag)
                # Store first occurrence of each tag's note data for propagation
                if tag not in tag_note_data:
                    tag_note_data[tag] = note_data
        
        # Auto-populate folder's tag config from notes if not already set
        for tag, note_data in tag_note_data.items():
            if tag not in metadata['number_config'] or \
               (metadata['number_config'][tag].get('description') == '' and 
                metadata['number_config'][tag].get('instructions') == ''):
                # Inherit description and instructions from the note
                metadata['number_config'][tag] = {
                    'description': note_data.get('description', ''),
                    'instructions': note_data.get('instructions', '')
                }
        
        # Sort tags (numeric if possible, otherwise alphabetic)
        sorted_tags = sorted(used_tags, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))
        
        tag_entries = {}
        
        if sorted_tags:
            row = 0
            for tag in sorted_tags:
                # Tag label
                tag_label = Gtk.Label(label=f"<b>ID Tag {tag}:</b>", use_markup=True)
                tag_label.set_xalign(0)
                number_grid.attach(tag_label, 0, row, 1, 1)
                
                # Get existing config
                tag_config = metadata['number_config'].get(tag, {'description': '', 'instructions': ''})
                
                # Description entry
                desc_frame = Gtk.Frame(label="Description")
                desc_text = Gtk.TextView()
                desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
                desc_text.set_size_request(250, 60)
                desc_buffer = desc_text.get_buffer()
                desc_buffer.set_text(tag_config.get('description', ''))
                desc_frame.add(desc_text)
                number_grid.attach(desc_frame, 1, row, 1, 1)
                
                # Instructions entry
                inst_frame = Gtk.Frame(label="Instructions")
                inst_text = Gtk.TextView()
                inst_text.set_wrap_mode(Gtk.WrapMode.WORD)
                inst_text.set_size_request(250, 60)
                inst_buffer = inst_text.get_buffer()
                inst_buffer.set_text(tag_config.get('instructions', ''))
                inst_frame.add(inst_text)
                number_grid.attach(inst_frame, 2, row, 1, 1)
                
                tag_entries[tag] = (desc_buffer, inst_buffer)
                row += 1
        else:
            # No ID tags assigned yet
            info_label = Gtk.Label(label="No ID Tags assigned to notes yet.\nAssign ID Tags in Note Settings first.")
            info_label.set_margin_top(20)
            number_grid.attach(info_label, 0, 0, 3, 1)
        
        notebook.append_page(number_tab_scroll, Gtk.Label(label="ID Tag Configuration"))
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Save file metadata
            color_config = {}
            for color_name, (desc_buf, inst_buf) in color_entries.items():
                color_config[color_name] = {
                    'description': desc_buf.get_text(desc_buf.get_start_iter(), desc_buf.get_end_iter(), True),
                    'instructions': inst_buf.get_text(inst_buf.get_start_iter(), inst_buf.get_end_iter(), True)
                }
            
            # Save ID tag config
            tag_config = {}
            for tag, (desc_buf, inst_buf) in tag_entries.items():
                tag_config[tag] = {
                    'description': desc_buf.get_text(desc_buf.get_start_iter(), desc_buf.get_end_iter(), True),
                    'instructions': inst_buf.get_text(inst_buf.get_start_iter(), inst_buf.get_end_iter(), True)
                }
            
            self.note_file_metadata[file_name] = {
                'description': file_desc_buffer.get_text(file_desc_buffer.get_start_iter(), file_desc_buffer.get_end_iter(), True),
                'instructions': file_inst_buffer.get_text(file_inst_buffer.get_start_iter(), file_inst_buffer.get_end_iter(), True),
                'color_config': color_config,
                'number_config': tag_config
            }
            self.save_data()
        
        dialog.destroy()
    
    def edit_note_metadata(self, widget, note_id):
        """Edit Description and Instructions for an individual note"""
        note_data = self.load_note_by_id(note_id)
        if not note_data:
            return
        
        dialog = Gtk.Dialog(
            title="Note Settings",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 400)
        
        box = dialog.get_content_area()
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_spacing(10)
        
        # Color Selector
        color_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        color_label = Gtk.Label(label="<b>Color:</b>", use_markup=True)
        color_label.set_xalign(0)
        color_hbox.pack_start(color_label, False, False, 0)
        
        # Import color names and codes
        from sticky_unmodified import COLORS, COLOR_CODES
        color_combo = Gtk.ComboBoxText()
        current_color = note_data.get('color', 'yellow')
        color_index = 0
        for idx, (color_name, display_name) in enumerate(COLORS.items()):
            color_combo.append(color_name, display_name)
            if color_name == current_color:
                color_index = idx
        color_combo.set_active(color_index)
        color_hbox.pack_start(color_combo, True, True, 0)
        
        # Color preview box
        color_code = COLOR_CODES.get(current_color, '#f6f907')
        color_preview = Gtk.DrawingArea()
        color_preview.set_size_request(40, 30)
        color_preview.connect('draw', self.draw_color_indicator, color_code)
        color_hbox.pack_start(color_preview, False, False, 0)
        
        # Update preview when color selection changes
        def on_color_changed(combo, preview_widget):
            selected_color = combo.get_active_id()
            new_code = COLOR_CODES.get(selected_color, '#f6f907')
            preview_widget.queue_draw()
            # Redraw with new color
            preview_widget.disconnect_by_func(self.draw_color_indicator)
            preview_widget.connect('draw', self.draw_color_indicator, new_code)
            preview_widget.queue_draw()
        
        color_combo.connect('changed', on_color_changed, color_preview)
        
        box.pack_start(color_hbox, False, False, 0)
        
        # ID Tag field
        idtag_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        idtag_label = Gtk.Label(label="<b>ID Tag:</b>", use_markup=True)
        idtag_label.set_xalign(0)
        idtag_hbox.pack_start(idtag_label, False, False, 0)
        
        idtag_entry = Gtk.Entry()
        idtag_entry.set_placeholder_text("Enter ID Tag (e.g., A1, Bug, Feature, v2)")
        idtag_entry.set_text(str(note_data.get('id_tag', '')))
        idtag_entry.set_max_length(20)
        idtag_hbox.pack_start(idtag_entry, True, True, 0)
        
        box.pack_start(idtag_hbox, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label="<b>Description:</b>", use_markup=True)
        desc_label.set_xalign(0)
        box.pack_start(desc_label, False, False, 0)
        
        desc_frame = Gtk.Frame()
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_size_request(-1, 100)
        desc_text = Gtk.TextView()
        desc_text.set_wrap_mode(Gtk.WrapMode.WORD)
        desc_buffer = desc_text.get_buffer()
        desc_buffer.set_text(note_data.get('description', ''))
        desc_scroll.add(desc_text)
        desc_frame.add(desc_scroll)
        box.pack_start(desc_frame, True, True, 0)
        
        # Instructions
        inst_label = Gtk.Label(label="<b>Instructions:</b>", use_markup=True)
        inst_label.set_xalign(0)
        box.pack_start(inst_label, False, False, 0)
        
        inst_frame = Gtk.Frame()
        inst_scroll = Gtk.ScrolledWindow()
        inst_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        inst_scroll.set_size_request(-1, 100)
        inst_text = Gtk.TextView()
        inst_text.set_wrap_mode(Gtk.WrapMode.WORD)
        inst_buffer = inst_text.get_buffer()
        inst_buffer.set_text(note_data.get('instructions', ''))
        inst_scroll.add(inst_text)
        inst_frame.add(inst_scroll)
        box.pack_start(inst_frame, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Get the new color value
            new_color = color_combo.get_active_id()
            
            # Save metadata to note file
            note_data['id_tag'] = idtag_entry.get_text().strip()
            note_data['color'] = new_color
            note_data['description'] = desc_buffer.get_text(desc_buffer.get_start_iter(), desc_buffer.get_end_iter(), True)
            note_data['instructions'] = inst_buffer.get_text(inst_buffer.get_start_iter(), inst_buffer.get_end_iter(), True)
            note_path = os.path.join(DATA_DIR, f"note_{note_id}.json")
            with open(note_path, 'w') as f:
                json.dump(note_data, f, indent=2)
            
            # Update any open notes with this ID and apply color change immediately
            for note in self.notes:
                if hasattr(note, 'note_id') and note.note_id == note_id:
                    # Call set_color method which handles the color change properly
                    if hasattr(note, 'set_color') and note.color != new_color:
                        note.set_color(None, new_color)
            
            # Trigger immediate refresh and re-select this note
            self.refresh_and_select_note(note_id)
        
        dialog.destroy()
    
    def on_close(self, widget, event):
        """Handle window close: save data and hide the manager."""
        self.save_data()
        # Don't quit, just hide
        self.hide()
        return True

def main():
    # Create and show only our manager window (Note Files UI)
    manager = NoteFileManager()

    # Run the main loop
    Gtk.main()

if __name__ == "__main__":
    main()
