#!/usr/bin/python3
"""Quick test to verify NoteCode works"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import sys

# Mock app with minimal requirements
class MockApp:
    class MockSettings:
        def get_uint(self, key):
            return 300 if 'height' in key or 'width' in key else 0
        def get_string(self, key):
            return 'yellow'
        def get_boolean(self, key):
            return False
        def bind(self, *args):
            pass
        def connect(self, *args):
            pass
    
    def __init__(self):
        self.settings = self.MockSettings()
        self.notes = []
        self.note_files = {}
        self.current_file_name = None
    
    def new_note(self, *args):
        print("New note requested")

try:
    from note_code import NoteCode
    
    app = MockApp()
    
    # Create a code note
    info = {
        'x': 100,
        'y': 100,
        'width': 400,
        'height': 300,
        'title': 'Test Code Note',
        'text': 'def hello():\n    print("Hello, world!")',
        'color': 'blue',
        'language': 'python'
    }
    
    print("Creating code note...")
    note = NoteCode(app, None, info)
    print("✓ Code note created successfully!")
    print(f"  - Has line numbers: {note.source_view.get_show_line_numbers()}")
    print(f"  - Has syntax highlighting: {note.source_buffer.get_highlight_syntax()}")
    print(f"  - Language: {note.language_id}")
    print(f"  - Auto-indent enabled: {note.source_view.get_auto_indent()}")
    print(f"  - Is code note: {note.is_code_note}")
    
    # Verify it saved the right metadata
    note_data = note.get_note_data()
    assert note_data['is_code_note'] == True
    assert note_data['language'] == 'python'
    print("✓ Metadata correct!")
    
    print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
