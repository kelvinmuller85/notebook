#!/usr/bin/env python3
import gi
import sys
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Ensure module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notebook_wrapper import NoteFileManager
from src.note_code import NoteCode


def assert_true(cond, msg):
    if cond:
        print(f"OK: {msg}")
    else:
        print(f"FAIL: {msg}")
        raise SystemExit(1)


# Create the manager window (it will show; that's fine for this quick test)
mgr = NoteFileManager()

# 1) Toolbar item exists and launches a Code note
assert_true(hasattr(mgr, 'new_code_btn'), 'New Code button exists')

# Create a Text note (default New Note)
mgr.create_new_note(None)
assert_true(len(mgr.notes) > 0, 'a text note was created')
text_note = mgr.notes[-1]

# Text note should have a convert-to-code button
found_convert_to_code = False
for child in text_note.title_bar.get_children():
    if isinstance(child, Gtk.MenuButton):
        tt = child.get_tooltip_text() or ''
        if 'Convert to Code Note' in tt:
            found_convert_to_code = True
            break
assert_true(found_convert_to_code, 'text note shows Convert to Code menu')

# Convert Text -> Code with a chosen color
orig_id = getattr(text_note, 'note_id', None)
text_note.convert_to_code(None, 'blue')
code_note = mgr.notes[-1]
assert_true(isinstance(code_note, NoteCode), 'converted to NoteCode')
assert_true(code_note.color == 'blue', 'code note color set to chosen value')

# Code note should have code color menu and Convert to Text
found_code_color = False
found_convert_to_text = False
for child in code_note.title_bar.get_children():
    if isinstance(child, Gtk.MenuButton):
        tt = child.get_tooltip_text() or ''
        if 'Code Note Color' in tt:
            found_code_color = True
        if 'Convert to Text Note' in tt:
            found_convert_to_text = True
assert_true(found_code_color, 'code note has color picker menu')
assert_true(found_convert_to_text, 'code note shows Convert to Text menu')

# 2) Save code note to a test file and verify row icon
if 'Test' not in mgr.note_files:
    mgr.note_files['Test'] = []

mgr.current_file_name = 'Test'
code_note.note_file = 'Test'
mgr.save_note_to_file(code_note)

mgr.populate_file_list()
for row in mgr.file_listbox.get_children():
    if getattr(row, 'file_name', None) == 'Test':
        mgr.on_file_selected(mgr.file_listbox, row)
        break

found_row_icon = False
for row in mgr.note_listbox.get_children():
    if getattr(row, 'note_id', None) == getattr(code_note, 'note_id', None):
        hbox = row.get_child()
        for w in hbox.get_children():
            if isinstance(w, Gtk.Image):
                name_size = w.get_icon_name()
                if name_size and name_size[0] == 'applications-development':
                    found_row_icon = True
                    break
        break
assert_true(found_row_icon, 'code icon present in Note File list row')

# 3) Convert Code -> Text with a chosen color and verify row icon removed
note_id = getattr(code_note, 'note_id', None)
code_note.convert_to_text(None, 'yellow')
new_text_note = mgr.notes[-1]
assert_true(not isinstance(new_text_note, NoteCode), 'converted back to Text note')
assert_true(new_text_note.color == 'yellow', 'text note color set to chosen value')

# Re-save to ensure index remains and refresh list
new_text_note.note_file = 'Test'
mgr.save_note_to_file(new_text_note)

mgr.populate_file_list()
for row in mgr.file_listbox.get_children():
    if getattr(row, 'file_name', None) == 'Test':
        mgr.on_file_selected(mgr.file_listbox, row)
        break

found_row_code_icon_after = False
for row in mgr.note_listbox.get_children():
    if getattr(row, 'note_id', None) == note_id:
        hbox = row.get_child()
        for w in hbox.get_children():
            if isinstance(w, Gtk.Image):
                name_size = w.get_icon_name()
                if name_size and name_size[0] == 'applications-development':
                    found_row_code_icon_after = True
                    break
        break
assert_true(found_row_code_icon_after is False, 'code icon removed after converting to Text note')

# 4) Direct toolbar Code note creation also works
prev_len = len(mgr.notes)
mgr.create_new_code_note(None)
assert_true(len(mgr.notes) == prev_len + 1 and isinstance(mgr.notes[-1], NoteCode), 'toolbar Code icon launches a Code note')

print('ALL GUI CHECKS PASSED')

# Cleanup
try:
    note.destroy()
    mgr.destroy()
except Exception:
    pass
