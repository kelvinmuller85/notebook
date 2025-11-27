#!/usr/bin/env python3
import os
import sys
import unittest
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, GtkSource, GLib

# Add the Files directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Files')))

class TestCodeEditorHighlighting(unittest.TestCase):
    def setUp(self):
        # Initialize Gtk
        if not Gtk.init_check()[0]:
            self.skipTest("Couldn't initialize Gtk")
        
        # Create a window for testing
        self.window = Gtk.Window()
        self.window.connect('delete-event', Gtk.main_quit)
        
        # Create source view with Python highlighting
        self.buffer = GtkSource.Buffer()
        self.view = GtkSource.View(buffer=self.buffer)
        self.window.add(self.view)
        
        # Set up language
        lang_mgr = GtkSource.LanguageManager()
        python_lang = lang_mgr.get_language('python')
        self.buffer.set_language(python_lang)
        self.buffer.set_highlight_syntax(True)
        
        # Add style scheme
        style_mgr = GtkSource.StyleSchemeManager()
        style = style_mgr.get_scheme('classic')
        if style:
            self.buffer.set_style_scheme(style)
        
        self.window.show_all()
    
    def test_syntax_highlighting(self):
        """Test that syntax highlighting is working"""
        # Sample Python code
        test_code = '''def example():
    """Docstring"""
    x = 42  # Number
    return "Hello"  # String
'''
        # Set the text
        self.buffer.set_text(test_code)
        
        # Force a refresh
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        # Get the first line
        start = self.buffer.get_start_iter()
        end = start.copy()
        end.forward_line()
        
        # Check that 'def' has a different tag than the function name
        text = self.buffer.get_text(start, end, False)
        self.assertEqual(text.strip(), 'def example():')
        
        # Verify tags exist (syntax highlighting is active)
        has_tags = False
        def_iter = start.copy()
        def_iter.forward_chars(3)  # Length of 'def'
        tags = def_iter.get_tags()
        has_tags = len(tags) > 0
        
        self.assertTrue(has_tags, "No syntax highlighting tags found")
    
    def test_multiple_languages(self):
        """Test switching between different languages"""
        lang_mgr = GtkSource.LanguageManager()
        
        # Test a few different languages
        for lang_id in ['python', 'c', 'javascript', 'html']:
            language = lang_mgr.get_language(lang_id)
            if language:
                self.buffer.set_language(language)
                self.assertTrue(self.buffer.get_highlight_syntax())
                # Force refresh
                while Gtk.events_pending():
                    Gtk.main_iteration()
    
    def tearDown(self):
        self.window.destroy()

if __name__ == '__main__':
    unittest.main()