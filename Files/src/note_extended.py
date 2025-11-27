#!/usr/bin/python3
"""
Extended Note class with Save/Minimize/Delete dropdown
Inherits from Sticky's Note but replaces delete button with MenuButton dropdown
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Pango

from sticky_unmodified import Note as StickyNote, FONT_SCALES, COLORS
from utils.common import confirm
import subprocess
import gettext
import os

# Initialize gettext for translations
_ = gettext.gettext
gettext.install("sticky", "/usr/share/locale", names="ngettext")


class NoteExtended(StickyNote):
    """
    Extended Note with Save/Minimize/Delete dropdown menu
    Replaces the trash button with a MenuButton offering three options
    """
    
    def __init__(self, app, parent, info={}):
        # Store note_file before calling super().__init__
        self.note_file = info.get('note_file', None)
        self.note_id = info.get('id', None)
        
        # Call parent constructor (creates the full note UI)
        super().__init__(app, parent, info)
        
        # Now replace the delete button with our dropdown
        # The delete button was added at line 200 in sticky_unmodified.py
        # It's the last button added to title_bar before the format/add buttons
        # We need to remove it and replace it with a MenuButton
        
        # Find and remove the old delete button
        for child in self.title_bar.get_children():
            if isinstance(child, Gtk.Button):
                # Check if it's the delete button by tooltip
                tooltip = child.get_tooltip_text()
                if tooltip and "Delete" in tooltip:
                    self.title_bar.remove(child)
                    break
        
        # Create new file MenuButton with dropdown
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Icons')
        close_icon_path = os.path.join(icon_dir, 'Save-Close Note.png')
        close_icon = Gtk.Image.new_from_file(close_icon_path) if os.path.exists(close_icon_path) else Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.BUTTON)
        self.close_menu_button = Gtk.MenuButton(
            image=close_icon,
            relief=Gtk.ReliefStyle.NONE,
            name='window-button',
            valign=Gtk.Align.CENTER
        )
        self.close_menu_button.set_size_request(24, 24)
        self.close_menu_button.set_tooltip_text(_("Note Options"))
        
        # Track if note is saved
        self.is_saved = bool(self.note_file and self.note_id)
        
        # Create the dropdown menu
        menu = Gtk.Menu()
        
        # Save to Note File
        save_item = Gtk.MenuItem(label=_("Save to Note File"), visible=True)
        save_item.connect('activate', self.save_to_file)
        menu.append(save_item)
        
        # Save as Subset
        subset_item = Gtk.MenuItem(label=_("Save as Subset"), visible=True)
        subset_item.connect('activate', self.save_as_subset)
        menu.append(subset_item)
        
        # Print (placeholder for future)
        print_item = Gtk.MenuItem(label=_("Print Note"), visible=True)
        print_item.connect('activate', self.print_note)
        menu.append(print_item)
        
        menu.append(Gtk.SeparatorMenuItem(visible=True))
        
        # Close Note
        close_item = Gtk.MenuItem(label=_("Close Note"), visible=True)
        close_item.connect('activate', self.close_note)
        menu.append(close_item)
        
        self.close_menu_button.set_popup(menu)
        
        # Add the new button to the title bar (at the end, same position as old delete button)
        self.title_bar.pack_end(self.close_menu_button, False, False, 0)
        self.title_bar.reorder_child(self.close_menu_button, 0)  # Make it the rightmost button
        
        self.close_menu_button.show_all()

        # Add Convert-to-Code menu button on the title bar (only for Text notes, NOT for Picture notes)
        if not getattr(self, 'is_code_note', False) and not getattr(self, 'is_picture_note', False):
            self._add_convert_to_code_button()
    
    def _add_convert_to_code_button(self):
        """Add a menu button for code editor colors (LEFT icon)
        NOTE: This icon is EXCLUSIVELY for CODE EDITOR notes.
        It shows a color menu, and selecting a color converts to/creates a code editor note.
        The RIGHT icon (inherited color droplet) is EXCLUSIVELY for TEXT notes.
        """
        try:
            # LEFT ICON: Code/text icon for CODE EDITOR color selection
            icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Icons')
            code_icon_path = os.path.join(icon_dir, 'Code Template.png')
            code_icon = Gtk.Image.new_from_file(code_icon_path) if os.path.exists(code_icon_path) else Gtk.Image.new_from_icon_name('text-x-script', Gtk.IconSize.BUTTON)
            self.convert_to_code_btn = Gtk.MenuButton(
                image=code_icon,
                relief=Gtk.ReliefStyle.NONE,
                name='window-button',
                valign=Gtk.Align.CENTER
            )
            self.convert_to_code_btn.set_size_request(24, 24)
            self.convert_to_code_btn.get_style_context().add_class('mode-switch')
            self.convert_to_code_btn.set_tooltip_text(_("Code Editor Colors (converts to code)"))
            
            # Store button reference
            setattr(self, '_mode_button', self.convert_to_code_btn)
            
            # Build CODE EDITOR colors menu
            menu = Gtk.Menu()
            for color_name, display_name in COLORS.items():
                item = Gtk.MenuItem(label=display_name, visible=True)
                def on_activate(_w, c=color_name):
                    # Prevent multiple conversions
                    if getattr(self, '_converting', False):
                        return
                    setattr(self, '_converting', True)
                    # Import here to avoid circular imports
                    from src.note_converter import NoteConverter
                    self.convert_to_code_btn.set_sensitive(False)
                    if not NoteConverter.text_to_code(self, c):
                        self.convert_to_code_btn.set_sensitive(True)
                        setattr(self, '_converting', False)
                item.connect('activate', on_activate)
                menu.append(item)
            self.convert_to_code_btn.set_popup(menu)
            
            # Place at position 0 (LEFT)
            self.title_bar.pack_start(self.convert_to_code_btn, False, False, 0)
            self.title_bar.reorder_child(self.convert_to_code_btn, 0)
            self.convert_to_code_btn.show_all()
            
            # Replace the inherited color button (RIGHT icon) with TEXT note color menu
            # RIGHT ICON (droplet) is EXCLUSIVELY for TEXT notes
            for child in self.title_bar.get_children():
                if isinstance(child, Gtk.MenuButton) and child != self.convert_to_code_btn:
                    tooltip = child.get_tooltip_text()
                    if tooltip and "Note Color" in tooltip:
                        # Remove the old color button
                        self.title_bar.remove(child)
                        break
            
            # Create new RIGHT icon: TEXT note color menu
            icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Icons')
            text_color_icon_path = os.path.join(icon_dir, 'Text Template.png')
            text_color_icon = Gtk.Image.new_from_file(text_color_icon_path) if os.path.exists(text_color_icon_path) else Gtk.Image.new_from_icon_name('sticky-color', Gtk.IconSize.BUTTON)
            text_color_button = Gtk.MenuButton(
                image=text_color_icon,
                relief=Gtk.ReliefStyle.NONE,
                name='window-button',
                valign=Gtk.Align.CENTER
            )
            text_color_button.set_size_request(24, 24)
            text_color_button.set_tooltip_text(_("Text Note Colors (exclusive to text)"))
            
            # Build TEXT note colors menu
            text_menu = Gtk.Menu()
            for color_name, display_name in COLORS.items():
                item = Gtk.MenuItem(label=display_name, visible=True)
                def on_text_color(_w, c=color_name):
                    # If already a text note, just change color
                    # If code note, convert to text
                    if getattr(self, 'is_code_note', False):
                        # This shouldn't happen on text notes, but handle it
                        if getattr(self, '_converting', False):
                            return
                        setattr(self, '_converting', True)
                        from src.note_converter import NoteConverter
                        text_color_button.set_sensitive(False)
                        if not NoteConverter.code_to_text(self, c):
                            text_color_button.set_sensitive(True)
                            setattr(self, '_converting', False)
                    else:
                        # Already text note - just change color
                        self.set_color(None, c)
                item.connect('activate', on_text_color)
                text_menu.append(item)
            text_color_button.set_popup(text_menu)
            
            # Place at position 1 (RIGHT, after code button)
            self.title_bar.pack_start(text_color_button, False, False, 0)
            self.title_bar.reorder_child(text_color_button, 1)
            text_color_button.show_all()
                        
        except Exception as e:
            print(f"Failed to add code conversion button: {e}")
            pass

    def convert_to_code(self, widget, color_name):
        """Transform this Text note into a Code note preserving content, id, and file"""
        try:
            # Get complete note data including position and content
            info = self.get_note_data()
            
            # Set new properties
            info['color'] = color_name
            info['is_code_note'] = True  # Mark as code note
            info['language'] = 'python'   # Default to Python
            
            # Create new code note
            from src.note_code import NoteCode
            new_note = NoteCode(self.app, self.app, info)
            
            # Replace in app's note list if it exists
            if hasattr(self.app, 'notes'):
                if self in self.app.notes:
                    index = self.app.notes.index(self)
                    self.app.notes[index] = new_note
                else:
                    self.app.notes.append(new_note)
            
            # Connect update signal
            if hasattr(new_note, 'connect'):
                new_note.connect('update', self.app.on_note_updated)
            
            # Position the new note where the old one was
            new_note.move(*self.get_position())
            
            # Close this note
            self.destroy()
            
            # Update the UI
            if hasattr(self.app, 'on_note_updated'):
                self.app.on_note_updated(new_note)
                
        except Exception as e:
            self.show_info_dialog(_("Convert to Code"), _("Failed to convert: %s") % str(e))
    
    def save_to_file(self, widget):
        """Save note to currently selected Note File"""
        # Get currently selected file from manager
        if hasattr(self.app, 'current_file_name') and self.app.current_file_name:
            # Bind to currently selected file
            self.note_file = self.app.current_file_name
            
            # Save note data directly without confirmation
            if hasattr(self.app, 'save_note_to_file'):
                self.app.save_note_to_file(self)
                self.is_saved = True
                return
        
        # No file selected - show error
        self.show_info_dialog(_("No File Selected"), _("Please select a Note File first."))
    
    def save_as_subset(self, widget):
        """Save note as a subset of currently selected or spawning note"""
        # Get currently selected file from manager
        if not hasattr(self.app, 'current_file_name') or not self.app.current_file_name:
            self.show_info_dialog(_("No File Selected"), _("Please select a Note File first."))
            return
        
        file_name = self.app.current_file_name
        
        # Determine default parent: either selected note or the note this was spawned from
        default_parent_id = None
        if hasattr(self.app, 'selected_note_id') and self.app.selected_note_id:
            # Use highlighted note as default parent
            default_parent_id = self.app.selected_note_id
        elif hasattr(self, 'parent') and hasattr(self.parent, 'note_id'):
            # Use spawning note as default parent
            default_parent_id = self.parent.note_id
        
        # If we have a clear parent, save directly without dialog
        if default_parent_id:
            self._save_with_parent(file_name, default_parent_id)
            return
        
        note_ids = self.app.note_files.get(file_name, [])
        
        if not note_ids:
            self.show_info_dialog(_("No Notes Available"), _("There are no notes to create a subset from."))
            return
        
        # Create dialog to select parent note
        dialog = Gtk.Dialog(
            title="Save as Subset",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(400, 300)
        
        box = dialog.get_content_area()
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_spacing(10)
        
        label = Gtk.Label(label="Select parent note for this subset:")
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        # Scrolled window for note list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scroll, True, True, 0)
        
        # List box for notes
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll.add(listbox)
        
        # Populate with notes from current file
        default_row = None
        for note_id in note_ids:
            note_data = self.app.load_note_by_id(note_id)
            if note_data and note_id != self.note_id:  # Don't show self
                row = Gtk.ListBoxRow()
                row.note_id = note_id
                
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_margin_start(5)
                hbox.set_margin_end(5)
                hbox.set_margin_top(3)
                hbox.set_margin_bottom(3)
                
                # Show ID tag if available
                id_tag = note_data.get('id_tag', '')
                if id_tag:
                    tag_label = Gtk.Label(label=f"[{id_tag}]")
                    hbox.pack_start(tag_label, False, False, 0)
                
                # Show title or preview
                title = note_data.get('title', '')
                text = note_data.get('text', '')
                preview = title if title else (text[:30] + "..." if len(text) > 30 else text)
                label = Gtk.Label(label=preview or "(Empty note)")
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                
                row.add(hbox)
                listbox.add(row)
                
                # Track default parent row
                if note_id == default_parent_id:
                    default_row = row
        
        dialog.show_all()
        
        # Auto-select default parent if found
        if default_row:
            listbox.select_row(default_row)
        
        response = dialog.run()
        
        parent_id = None
        if response == Gtk.ResponseType.OK:
            selected_row = listbox.get_selected_row()
            if selected_row:
                parent_id = selected_row.note_id
            elif default_parent_id:  # Use default if nothing else selected
                parent_id = default_parent_id
        
        dialog.destroy()
        
        if parent_id:
            self._save_with_parent(file_name, parent_id)
    
    def _save_with_parent(self, file_name, parent_id):
        """Internal method to save note with parent_id"""
        # Save this note with parent_id
        self.note_file = file_name
        
        # Get note data and add parent_id
        note_data = self.get_note_data()
        note_data['parent_id'] = parent_id
        
        # Save to file
        if hasattr(self.app, 'save_note_to_file'):
            # Need to manually add parent_id field
            import uuid
            if not note_data.get('id'):
                note_data['id'] = str(uuid.uuid4())
                self.note_id = note_data['id']
            
            # Write note JSON with parent_id
            import os
            import json
            from src.notebook_wrapper import DATA_DIR
            note_path = os.path.join(DATA_DIR, f"note_{note_data['id']}.json")
            with open(note_path, 'w') as f:
                json.dump(note_data, f, indent=2)
            
            # Index under Note File
            if note_data['id'] not in self.app.note_files[file_name]:
                self.app.note_files[file_name].append(note_data['id'])
                self.app.save_data()
                self.app.populate_file_list()
                # Force refresh by calling on_file_selected directly
                for row in self.app.file_listbox.get_children():
                    if hasattr(row, 'file_name') and row.file_name == file_name:
                        self.app.on_file_selected(self.app.file_listbox, row)
                        break
            
            self.is_saved = True
    
    def close_note(self, widget):
        """Close note window. If unsaved, warn. Do NOT delete saved note."""
        if not self.is_saved:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Note Not Saved"
            )
            dialog.format_secondary_text("This note has not been saved. Are you sure you want to close it?")
            response = dialog.run()
            dialog.destroy()
            if response != Gtk.ResponseType.YES:
                return
        # For saved notes: just close the window
        self.destroy()
    
    def print_note(self, widget):
        """Print note - placeholder for future implementation"""
        self.show_info_dialog(_("Print"), _("Print functionality will be implemented soon."))
    
    def get_note_data(self):
        """Get note data for saving"""
        info = self.get_info()
        info['note_file'] = self.note_file
        if self.note_id:
            info['id'] = self.note_id
        return info
    
    # Black note icon fix removed - now handled by CSS with reversed contrast
    # Black notes now have light grey titlebar (#bbbbbb) with default black icons
    
    def create_format_menu(self, color_button, text_button):
        """Override to add spell check and custom font size"""
        # Call parent to create base menu
        super().create_format_menu(color_button, text_button)
        
        # Get the existing format menu
        menu = text_button.get_popup()
        
        # Add separator
        menu.append(Gtk.SeparatorMenuItem(visible=True))
        
        # Add custom font size
        custom_size_item = Gtk.MenuItem(label=_("Custom Font Size..."), visible=True)
        custom_size_item.connect('activate', self.show_custom_font_dialog)
        menu.append(custom_size_item)
        
        # Add separator
        menu.append(Gtk.SeparatorMenuItem(visible=True))
        
        # Add spell check
        spell_check_item = Gtk.MenuItem(label=_("Spell Check"), visible=True)
        spell_check_item.connect('activate', self.run_spell_check)
        menu.append(spell_check_item)
        
        menu.show_all()
    
    def show_custom_font_dialog(self, widget):
        """Show dialog for custom font size"""
        dialog = Gtk.Dialog(
            title=_("Custom Font Size"),
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
        
        label = Gtk.Label(label=_("Font Size (6-72 pt):"))
        box.pack_start(label, False, False, 5)
        
        adjustment = Gtk.Adjustment(value=12, lower=6, upper=72, step_increment=1, page_increment=5)
        spinbutton = Gtk.SpinButton(adjustment=adjustment, digits=0)
        spinbutton.set_numeric(True)
        box.pack_start(spinbutton, False, False, 5)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            size = spinbutton.get_value_as_int()
            
            # Create tag with absolute font size
            # Use Pango.SCALE for proper unit conversion
            tag = self.buffer.create_tag(None)
            tag.set_property('size', size * Pango.SCALE)
            
            bounds = self.buffer.get_selection_bounds()
            if bounds:
                # Has selection - apply to selected text
                start, end = bounds
                self.buffer.apply_tag(tag, start, end)
            else:
                # No selection - apply to cursor position for future typing
                # Store the tag so new text uses it
                insert_mark = self.buffer.get_insert()
                cursor_iter = self.buffer.get_iter_at_mark(insert_mark)
                
                # Insert a zero-width space with the tag, then remove it
                # This sets the tag as active for future typing
                self.buffer.insert_with_tags(cursor_iter, '', tag)
                
                # Also set it as the active tag for typing
                # GTK will apply this tag to newly typed text
                self.buffer.handler_block(self.changed_id)
                self.current_font_size_tag = tag
                self.buffer.handler_unblock(self.changed_id)
        
        dialog.destroy()
    
    def run_spell_check(self, widget):
        """Run interactive spell check like LibreOffice Writer"""
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        text = self.buffer.get_text(start, end, True)
        
        if not text.strip():
            self.show_info_dialog(_("Spell Check"), _("No text to check."))
            return
        
        try:
            # Get list of misspelled words and their positions
            misspelled_words = self._get_misspelled_words(text)
            
            if not misspelled_words:
                self.show_info_dialog(_("Spell Check"), _("No spelling errors found!"))
                return
            
            # Interactive checking for each word
            self._interactive_spell_check(misspelled_words, text)
            
        except FileNotFoundError:
            self.show_info_dialog(
                _("Spell Check"),
                _("Spell checker not available.\nInstall 'aspell' for spell checking:\n\nsudo apt install aspell")
            )
        except subprocess.TimeoutExpired:
            self.show_info_dialog(_("Spell Check"), _("Spell check timed out."))
        except Exception as e:
            self.show_info_dialog(_("Spell Check"), _(f"Error: {str(e)}"))
    
    def _get_misspelled_words(self, text):
        """Get list of misspelled words with positions"""
        # Run aspell list to get misspelled words
        result = subprocess.run(
            ['aspell', 'list'],
            input=text,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        misspelled = result.stdout.strip().split('\n')
        misspelled = [word for word in misspelled if word]
        
        # Find positions of each misspelled word in text
        word_list = []
        for word in misspelled:
            pos = text.find(word)
            if pos >= 0:
                word_list.append({'word': word, 'pos': pos})
        
        # Sort by position
        word_list.sort(key=lambda x: x['pos'])
        return word_list
    
    def _get_suggestions(self, word):
        """Get spelling suggestions for a word using aspell"""
        try:
            result = subprocess.run(
                ['aspell', '-a'],
                input=word + '\n',
                capture_output=True,
                text=True,
                timeout=2
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('&'):  # Misspelled with suggestions
                    # Format: & word count offset: suggestion1, suggestion2, ...
                    parts = line.split(': ', 1)
                    if len(parts) > 1:
                        suggestions = parts[1].split(', ')
                        return suggestions[:10]  # Limit to 10 suggestions
            return []
        except Exception:
            return []
    
    def _interactive_spell_check(self, word_list, original_text):
        """Show interactive spell check dialog for each word"""
        ignore_all = set()
        
        for i, word_info in enumerate(word_list):
            word = word_info['word']
            
            # Skip if in ignore_all list
            if word in ignore_all:
                continue
            
            # Get suggestions
            suggestions = self._get_suggestions(word)
            
            # Get context (surrounding text)
            pos = word_info['pos']
            context_start = max(0, pos - 30)
            context_end = min(len(original_text), pos + len(word) + 30)
            context = original_text[context_start:context_end]
            
            # Show spell check dialog
            action, replacement = self._show_spell_dialog(
                word, suggestions, context, i + 1, len(word_list)
            )
            
            if action == 'cancel':
                break
            elif action == 'ignore':
                continue
            elif action == 'ignore_all':
                ignore_all.add(word)
            elif action == 'replace' and replacement:
                self._replace_word_in_buffer(word, replacement)
            elif action == 'replace_all' and replacement:
                self._replace_all_in_buffer(word, replacement)
    
    def _show_spell_dialog(self, word, suggestions, context, current, total):
        """Show LibreOffice-style spell check dialog"""
        dialog = Gtk.Dialog(
            title=_("Spell Check"),
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.set_default_size(500, 400)
        
        box = dialog.get_content_area()
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_spacing(10)
        
        # Progress
        progress_label = Gtk.Label(label=_(f"Word {current} of {total}"))
        progress_label.set_xalign(0)
        box.pack_start(progress_label, False, False, 0)
        
        # Not in dictionary
        not_in_dict = Gtk.Label(label=_(f"Not in dictionary: {word}"))
        not_in_dict.set_xalign(0)
        not_in_dict.set_markup(f"<b>{_('Not in dictionary:')}</b> {word}")
        box.pack_start(not_in_dict, False, False, 0)
        
        # Context
        context_frame = Gtk.Frame(label=_("Context"))
        context_label = Gtk.Label(label=context)
        context_label.set_line_wrap(True)
        context_label.set_xalign(0)
        context_label.set_margin_start(5)
        context_label.set_margin_end(5)
        context_label.set_margin_top(5)
        context_label.set_margin_bottom(5)
        context_frame.add(context_label)
        box.pack_start(context_frame, False, False, 0)
        
        # Suggestions
        suggestions_label = Gtk.Label(label=_("Suggestions:"))
        suggestions_label.set_xalign(0)
        box.pack_start(suggestions_label, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(-1, 150)
        
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        for suggestion in suggestions:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=suggestion)
            label.set_xalign(0)
            label.set_margin_start(5)
            label.set_margin_end(5)
            label.set_margin_top(2)
            label.set_margin_bottom(2)
            row.add(label)
            listbox.add(row)
        
        if suggestions:
            listbox.select_row(listbox.get_row_at_index(0))
        
        scroll.add(listbox)
        box.pack_start(scroll, True, True, 0)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)
        
        ignore_btn = Gtk.Button(label=_("Ignore"))
        button_box.pack_start(ignore_btn, False, False, 0)
        
        ignore_all_btn = Gtk.Button(label=_("Ignore All"))
        button_box.pack_start(ignore_all_btn, False, False, 0)
        
        replace_btn = Gtk.Button(label=_("Replace"))
        button_box.pack_start(replace_btn, False, False, 0)
        
        replace_all_btn = Gtk.Button(label=_("Replace All"))
        button_box.pack_start(replace_all_btn, False, False, 0)
        
        cancel_btn = Gtk.Button(label=_("Cancel"))
        button_box.pack_start(cancel_btn, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        dialog.show_all()
        
        # Handle button clicks
        result = {'action': 'ignore', 'replacement': None}
        
        def on_ignore(*args):
            result['action'] = 'ignore'
            dialog.destroy()
        
        def on_ignore_all(*args):
            result['action'] = 'ignore_all'
            dialog.destroy()
        
        def on_replace(*args):
            selected = listbox.get_selected_row()
            if selected:
                result['action'] = 'replace'
                result['replacement'] = selected.get_child().get_text()
            dialog.destroy()
        
        def on_replace_all(*args):
            selected = listbox.get_selected_row()
            if selected:
                result['action'] = 'replace_all'
                result['replacement'] = selected.get_child().get_text()
            dialog.destroy()
        
        def on_cancel(*args):
            result['action'] = 'cancel'
            dialog.destroy()
        
        ignore_btn.connect('clicked', on_ignore)
        ignore_all_btn.connect('clicked', on_ignore_all)
        replace_btn.connect('clicked', on_replace)
        replace_all_btn.connect('clicked', on_replace_all)
        cancel_btn.connect('clicked', on_cancel)
        
        dialog.run()
        return result['action'], result['replacement']
    
    def _replace_word_in_buffer(self, old_word, new_word):
        """Replace first occurrence of word in buffer"""
        start = self.buffer.get_start_iter()
        result = start.forward_search(old_word, Gtk.TextSearchFlags.TEXT_ONLY, None)
        
        if result:
            match_start, match_end = result
            self.buffer.delete(match_start, match_end)
            self.buffer.insert(match_start, new_word)
    
    def _replace_all_in_buffer(self, old_word, new_word):
        """Replace all occurrences of word in buffer"""
        while True:
            start = self.buffer.get_start_iter()
            result = start.forward_search(old_word, Gtk.TextSearchFlags.TEXT_ONLY, None)
            
            if not result:
                break
            
            match_start, match_end = result
            self.buffer.delete(match_start, match_end)
            self.buffer.insert(match_start, new_word)
    
    def show_info_dialog(self, title, message):
        """Show an info dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
