#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import GtkSource

# Usage:
#   python3 list_sourceview_colors.py [scheme-id]
# If scheme-id is omitted, tries the default scheme or falls back to 'tango'.

scheme_id = sys.argv[1] if len(sys.argv) > 1 else None

mgr = GtkSource.StyleSchemeManager()

if scheme_id is None:
    # Try to detect default by picking a common light scheme
    for candidate in ('tango', 'classic', 'kate', 'solarized-light', 'solarized-dark'):
        if mgr.get_scheme(candidate):
            scheme_id = candidate
            break

scheme = mgr.get_scheme(scheme_id) if scheme_id else None
if not scheme:
    print("No scheme found. Provide a valid scheme ID (e.g., 'tango', 'classic', 'kate').")
    sys.exit(1)

print(f"Scheme: {scheme.get_id()} ({scheme.get_name()})")

# Common style names observed in many GtkSource schemes
styles = [
    'text', 'cursor', 'selection', 'current-line', 'line-numbers',
    'def:keyword', 'def:comment', 'def:string', 'def:number', 'def:function',
    'def:type', 'def:variable', 'def:constant', 'def:preprocessor', 'def:operator',
    'def:boolean', 'def:character', 'def:identifier', 'def:statement',
]

for name in styles:
    st = scheme.get_style(name)
    if not st:
        continue
    fg = st.get_foreground() if hasattr(st, 'get_foreground') else None
    bg = st.get_background() if hasattr(st, 'get_background') else None
    bold = st.is_bold() if hasattr(st, 'is_bold') else False
    italic = st.is_italic() if hasattr(st, 'is_italic') else False
    underline = st.is_underline() if hasattr(st, 'is_underline') else False
    print(f"{name:16} fg={fg or '-':>10} bg={bg or '-':>10} bold={bold} italic={italic} underline={underline}")
