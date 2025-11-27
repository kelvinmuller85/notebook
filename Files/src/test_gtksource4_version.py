#!/usr/bin/python3
"""Test GtkSource 4 version and features"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, GtkSource

def get_version_info():
    # GtkSource 4 doesn't expose version directly like 3.0 did
    # Instead, we can check capabilities
    buf = GtkSource.Buffer()
    view = GtkSource.View(buffer=buf)
    
    print("GtkSource 4 Capabilities:")
    print("- Has syntax highlighting:", buf.get_highlight_syntax() is not None)
    print("- Has style schemes:", bool(GtkSource.StyleSchemeManager.get_default().get_scheme_ids()))
    print("- Has language manager:", bool(GtkSource.LanguageManager.get_default().get_language_ids()))
    
    # Test basic features
    lang_mgr = GtkSource.LanguageManager.get_default()
    python_lang = lang_mgr.get_language('python')
    if python_lang:
        print("- Python language support: Available")
        buf.set_language(python_lang)
    else:
        print("- Python language support: Not available")
    
    style_mgr = GtkSource.StyleSchemeManager.get_default()
    classic = style_mgr.get_scheme('classic')
    if classic:
        print("- Classic style scheme: Available")
        buf.set_style_scheme(classic)
    else:
        print("- Classic style scheme: Not available")
    
    return True

if __name__ == '__main__':
    get_version_info()