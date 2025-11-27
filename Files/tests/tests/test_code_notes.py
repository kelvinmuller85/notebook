#!/usr/bin/python3
"""
Comprehensive tests for code note functionality
Tests:
1. Code mode toggle in GUI
2. Code note creation
3. Code icon on note titlebar
4. Color picker on code notes
5. Delete button auto-refresh
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Files'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MockApp:
    class MockSettings:
        def get_uint(self, key):
            return 300
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
        self.note_files = {'test_file': []}
        self.current_file_name = 'test_file'
        self.refresh_called = False
    
    def new_note(self, *args):
        pass
    
    def save_data(self):
        pass
    
    def refresh_current_file_view(self):
        self.refresh_called = True

def test_code_mode_toggle():
    """Test 1: Code mode toggle exists and works"""
    print("\n=== Test 1: Code Mode Toggle ===")
    try:
        from notebook_wrapper import NoteFileManager
        manager = NoteFileManager()
        
        assert hasattr(manager, 'code_mode'), "Manager missing code_mode attribute"
        assert hasattr(manager, 'code_toggle'), "Manager missing code_toggle button"
        assert manager.code_mode == False, "code_mode should start False"
        
        # Simulate toggle
        manager.code_toggle.set_active(True)
        manager.on_code_mode_toggled(manager.code_toggle)
        
        assert manager.code_mode == True, "code_mode should be True after toggle"
        print("✓ Code mode toggle works")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_note_creation():
    """Test 2: Code note can be created"""
    print("\n=== Test 2: Code Note Creation ===")
    try:
        from note_code import NoteCode
        
        app = MockApp()
        info = {'x': 100, 'y': 100, 'color': 'blue', 'language': 'python'}
        
        note = NoteCode(app, None, info)
        
        assert hasattr(note, 'is_code_note'), "Note missing is_code_note attribute"
        assert note.is_code_note == True, "is_code_note should be True"
        assert hasattr(note, 'source_view'), "Note missing source_view"
        assert hasattr(note, 'source_buffer'), "Note missing source_buffer"
        
        print("✓ Code note creates successfully")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_icon_visibility():
    """Test 3: Code icon appears on titlebar"""
    print("\n=== Test 3: Code Icon on Titlebar ===")
    try:
        from note_code import NoteCode
        
        app = MockApp()
        info = {'x': 100, 'y': 100, 'color': 'blue'}
        
        note = NoteCode(app, None, info)
        
        # Count MenuButtons in titlebar
        menu_buttons = [child for child in note.title_bar.get_children() 
                       if isinstance(child, Gtk.MenuButton)]
        
        assert len(menu_buttons) >= 2, f"Expected at least 2 MenuButtons, found {len(menu_buttons)}"
        
        # First MenuButton should be code color picker
        first_btn = menu_buttons[0]
        tooltip = first_btn.get_tooltip_text()
        
        assert tooltip is not None, "Code button has no tooltip"
        assert 'Code' in tooltip or 'python' in tooltip, f"Unexpected tooltip: {tooltip}"
        
        print(f"✓ Code icon present (tooltip: {tooltip})")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_color_picker():
    """Test 4: Code note has color picker menu"""
    print("\n=== Test 4: Code Note Color Picker ===")
    try:
        from note_code import NoteCode
        
        app = MockApp()
        info = {'x': 100, 'y': 100, 'color': 'yellow'}
        
        note = NoteCode(app, None, info)
        
        # Find code color button
        menu_buttons = [child for child in note.title_bar.get_children() 
                       if isinstance(child, Gtk.MenuButton)]
        code_btn = menu_buttons[0]
        
        # Check it has a popup menu
        menu = code_btn.get_popup()
        assert menu is not None, "Code button has no menu"
        
        # Check menu has color items
        menu_items = menu.get_children()
        assert len(menu_items) >= 11, f"Expected 11+ color items, found {len(menu_items)}"
        
        print(f"✓ Color picker has {len(menu_items)} color options")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_note_features():
    """Test 5: Code note has syntax highlighting features"""
    print("\n=== Test 5: Code Editor Features ===")
    try:
        from note_code import NoteCode
        
        app = MockApp()
        info = {'x': 100, 'y': 100, 'language': 'python'}
        
        note = NoteCode(app, None, info)
        
        # Check GtkSourceView features
        assert note.source_view.get_show_line_numbers() == True, "Line numbers not enabled"
        assert note.source_view.get_auto_indent() == True, "Auto-indent not enabled"
        assert note.source_buffer.get_highlight_syntax() == True, "Syntax highlighting not enabled"
        assert note.language_id == 'python', f"Wrong language: {note.language_id}"
        
        print("✓ All code editor features enabled")
        print(f"  - Line numbers: ✓")
        print(f"  - Auto-indent: ✓")
        print(f"  - Syntax highlighting: ✓")
        print(f"  - Language: {note.language_id}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_delete_refresh():
    """Test 6: Delete button triggers refresh"""
    print("\n=== Test 6: Delete Auto-Refresh ===")
    try:
        from note_extended import NoteExtended
        import uuid
        
        app = MockApp()
        note_id = str(uuid.uuid4())
        info = {
            'x': 100, 
            'y': 100,
            'id': note_id,
            'note_file': 'test_file'
        }
        
        note = NoteExtended(app, None, info)
        note.is_saved = True
        note.note_id = note_id
        note.note_file = 'test_file'
        
        # Add to app's note files
        app.note_files['test_file'].append(note_id)
        
        # Simulate close (without actually destroying)
        original_destroy = note.destroy
        note.destroy = lambda: None  # Mock destroy
        
        # Call close_note
        note.close_note(None)
        
        # Check refresh was called
        assert app.refresh_called == True, "refresh_current_file_view was not called"
        assert note_id not in app.note_files['test_file'], "Note ID not removed from list"
        
        print("✓ Delete triggers auto-refresh")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_creates_code_notes():
    """Test 7: Manager creates code notes when toggle is on"""
    print("\n=== Test 7: Manager Creates Code Notes ===")
    try:
        from notebook_wrapper import NoteFileManager
        from note_code import NoteCode
        
        manager = NoteFileManager()
        manager.code_mode = True
        
        # Call create_new_note
        original_notes_count = len(manager.notes)
        manager.create_new_note(None)
        
        # Check a note was created
        assert len(manager.notes) > original_notes_count, "No note created"
        
        # Check it's a code note
        new_note = manager.notes[-1]
        assert isinstance(new_note, NoteCode), f"Wrong note type: {type(new_note)}"
        assert new_note.is_code_note == True, "Note is not marked as code note"
        
        print("✓ Manager creates code notes when toggle is ON")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CODE NOTE FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_code_mode_toggle,
        test_code_note_creation,
        test_code_icon_visibility,
        test_code_color_picker,
        test_code_note_features,
        test_delete_refresh,
        test_manager_creates_code_notes
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
