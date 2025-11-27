"""
Note conversion utility to handle transitions between note types.
Centralizes all conversion logic to avoid circular dependencies and state issues.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gettext
_ = gettext.gettext

class NoteConverter:
    """Handles conversion between different note types"""
    
    @staticmethod
    def text_to_code(text_note, color_name):
        """Convert a text note to a code note"""
        try:
            # Get full note data
            info = text_note.get_note_data()
            
            # Save current position and size
            x, y = text_note.get_position()
            width, height = text_note.get_size()
            
            # Update note properties
            info['color'] = color_name
            info['is_code_note'] = True
            info['language'] = 'python'  # Default to Python
            
            # Create new code note
            from src.note_code import NoteCode
            new_note = NoteCode(text_note.app, text_note.app, info)
            
            # Restore position and size
            new_note.move(x, y)
            new_note.resize(width, height)
            
            # Update app's note list
            if hasattr(text_note.app, 'notes'):
                if text_note in text_note.app.notes:
                    index = text_note.app.notes.index(text_note)
                    text_note.app.notes[index] = new_note
                else:
                    text_note.app.notes.append(new_note)
            
            # Connect update signal
            if hasattr(new_note, 'connect'):
                new_note.connect('update', text_note.app.on_note_updated)
            
            # Destroy old note AFTER new one is fully set up
            text_note.destroy()
            
            # Update UI
            if hasattr(text_note.app, 'on_note_updated'):
                text_note.app.on_note_updated(new_note)
            
            return True
            
        except Exception as e:
            try:
                text_note.show_info_dialog(
                    _("Convert to Code"),
                    _("Failed to convert: %s") % str(e)
                )
            except:
                print(f"Failed to convert to code: {e}")
            return False
    
    @staticmethod
    def code_to_text(code_note, color_name):
        """Convert a code note to a text note"""
        try:
            # Get full note data
            info = code_note.get_note_data()
            
            # Save current position and size
            x, y = code_note.get_position()
            width, height = code_note.get_size()
            
            # Update note properties
            info['color'] = color_name
            info['is_code_note'] = False
            if 'language' in info:
                del info['language']
            
            # Create new text note
            from src.note_extended import NoteExtended
            new_note = NoteExtended(code_note.app, code_note.app, info)
            
            # Restore position and size
            new_note.move(x, y)
            new_note.resize(width, height)
            
            # Update app's note list
            if hasattr(code_note.app, 'notes'):
                if code_note in code_note.app.notes:
                    index = code_note.app.notes.index(code_note)
                    code_note.app.notes[index] = new_note
                else:
                    code_note.app.notes.append(new_note)
            
            # Connect update signal
            if hasattr(new_note, 'connect'):
                new_note.connect('update', code_note.app.on_note_updated)
            
            # Destroy old note AFTER new one is fully set up
            code_note.destroy()
            
            # Update UI
            if hasattr(code_note.app, 'on_note_updated'):
                code_note.app.on_note_updated(new_note)
            
            return True
            
        except Exception as e:
            try:
                code_note.show_info_dialog(
                    _("Convert to Text"),
                    _("Failed to convert: %s") % str(e)
                )
            except:
                print(f"Failed to convert to text: {e}")
            return False