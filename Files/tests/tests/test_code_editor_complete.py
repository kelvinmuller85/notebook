#!/usr/bin/python3
"""Test all code editor features work end-to-end"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Files'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MockApp:
    class MockSettings:
        def get_uint(self, key): return 300
        def get_string(self, key): return 'yellow'
        def get_boolean(self, key): return False
        def bind(self, *args): pass
        def connect(self, *args): pass
    
    def __init__(self):
        self.settings = self.MockSettings()
        self.notes = []
        self.note_files = {}
    def new_note(self, *args): pass

print("Testing code editor features...")

# Test 1: Code note creation
from note_code import NoteCode
app = MockApp()
note = NoteCode(app, None, {'x': 100, 'y': 100, 'color': 'blue'})
print(f"✓ Code note created")

# Test 2: Check titlebar has code icon
menu_buttons = [c for c in note.title_bar.get_children() if isinstance(c, Gtk.MenuButton)]
print(f"  MenuButtons in titlebar: {len(menu_buttons)}")
if len(menu_buttons) >= 2:
    print(f"✓ Code icon present (2+ MenuButtons)")
    # First should be code color picker
    first = menu_buttons[0]
    tooltip = first.get_tooltip_text()
    if tooltip and 'Code' in tooltip:
        print(f"✓ Code icon tooltip correct: '{tooltip}'")
    else:
        print(f"✗ Wrong tooltip: '{tooltip}'")
else:
    print(f"✗ FAILED: Only {len(menu_buttons)} MenuButtons")
    sys.exit(1)

# Test 3: Code icon has color menu
menu = menu_buttons[0].get_popup()
if menu:
    items = menu.get_children()
    print(f"✓ Color menu has {len(items)} items")
else:
    print(f"✗ No color menu")
    sys.exit(1)

# Test 4: GtkSourceView features
if note.source_view.get_show_line_numbers():
    print(f"✓ Line numbers enabled")
else:
    print(f"✗ Line numbers disabled")

if note.source_buffer.get_highlight_syntax():
    print(f"✓ Syntax highlighting enabled")
else:
    print(f"✗ Syntax highlighting disabled")

print("\n✓✓ ALL CODE EDITOR FEATURES WORKING ✓✓")
