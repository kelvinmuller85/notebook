#!/usr/bin/python3
"""
Code-enabled Note using GtkSourceView for syntax highlighting.
Identical to NoteExtended but with code editor capabilities.
"""

import gi
import os
import uuid
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, GtkSource, Gdk, GObject

# Constants for GtkSource 4 compatibility
GTKSOURCE_GUTTER_RENDERER_STATE_NORMAL = 0
GTKSOURCE_GUTTER_RENDERER_STATE_CURSOR = 1
GTKSOURCE_GUTTER_RENDERER_STATE_PRELIT = 2
GTKSOURCE_GUTTER_RENDERER_STATE_SELECTED = 4

from .note_extended import NoteExtended
import gettext

# Initialize gettext for translations
_ = gettext.gettext
gettext.install("sticky", "/usr/share/locale", names="ngettext")


class NoteCode(NoteExtended):
    """
    Code-enabled note with syntax highlighting using GtkSourceView.
    Inherits all features from NoteExtended (save, minimize, delete, spell check, etc.)
    but replaces TextView with SourceView for code editing.
    """
    
    def __init__(self, app, parent, info={}):
        # Store language before parent init
        self.language_id = info.get('language', 'python')
        self.is_code_note = True
        
        # Prevent the parent class from adding its mode button
        info['is_code_note'] = True
        
        # Call parent constructor
        # This will create the note with TextView, which we'll replace
        super().__init__(app, parent, info)
        
        # Now replace the TextView with SourceView
        self._replace_textview_with_sourceview()
        
        # Add code editor icon to title bar
        self._add_code_indicator()
    
    def _replace_textview_with_sourceview(self):
        """Replace the TextView widget with GtkSourceView"""
        # Find the scrolled window containing the view
        scroll = None
        for child in self.get_children():
            if isinstance(child, Gtk.ScrolledWindow):
                scroll = child
                break
        
        if not scroll:
            return
        
        # Store old buffer content
        old_buffer = self.view.get_buffer()
        start = old_buffer.get_start_iter()
        end = old_buffer.get_end_iter()
        text_content = old_buffer.get_text(start, end, True)
        
        # Remove old view
        scroll.remove(self.view)
        
        # Initialize style manager and load styles
        style_manager = GtkSource.StyleSchemeManager.get_default()
        style_scheme = style_manager.get_scheme('classic')  # Use classic as fallback
        
        # Create SourceView buffer with language
        language_manager = GtkSource.LanguageManager.get_default()
        language = language_manager.get_language(self.language_id)
        
        # Create and configure source buffer
        self.source_buffer = GtkSource.Buffer()
        if language:
            self.source_buffer.set_language(language)
        if style_scheme:
            self.source_buffer.set_style_scheme(style_scheme)
        
        # Enable syntax highlighting explicitly
        self.source_buffer.set_highlight_syntax(True)
        self.source_buffer.set_highlight_matching_brackets(True)
        
        # Create and configure SourceView
        self.source_view = GtkSource.View.new_with_buffer(self.source_buffer)
        self.source_view.set_show_line_numbers(True)  # Enable line numbers
        self.source_view.set_auto_indent(True)
        self.source_view.set_indent_on_tab(True)
        self.source_view.set_insert_spaces_instead_of_tabs(True)
        self.source_view.set_tab_width(4)
        self.source_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        
        # Set margins
        self.source_view.set_left_margin(10)
        self.source_view.set_right_margin(10)
        self.source_view.set_top_margin(10)
        self.source_view.set_bottom_margin(10)
        
        # Give this editor a unique CSS id to style its gutter/content background
        self._css_id = f"code-editor-{uuid.uuid4().hex[:8]}"
        self.source_view.set_name(self._css_id)
        
        # Try to tag the left gutter with a unique name/class for CSS targeting
        try:
            gutter = self.source_view.get_gutter(Gtk.TextWindowType.LEFT)
            if gutter:
                gutter.set_name(self._css_id + "-gutter")
                gutter.get_style_context().add_class('code-gutter')
        except Exception:
            pass
        
        # Enable code editor features
        # Paint gutter background to match note color
        self._install_gutter_background_renderer()
        # Avoid white row highlight; the note color will be consistent
        self.source_view.set_highlight_current_line(False)
        self.source_view.set_auto_indent(True)
        self.source_view.set_indent_on_tab(True)
        self.source_view.set_tab_width(4)
        self.source_view.set_insert_spaces_instead_of_tabs(True)
        
        # Set background window to prevent white L artifact
        self.source_view.set_background_pattern(GtkSource.BackgroundPatternType.NONE)
        
        # Enable bracket matching
        self.source_buffer.set_highlight_matching_brackets(True)
        
        # Do NOT force a style scheme with a hardcoded white background
        # (CSS will handle background so it matches note color)
        # style_manager = GtkSource.StyleSchemeManager()
        # scheme = style_manager.get_scheme('classic')
        # if scheme:
        #     self.source_buffer.set_style_scheme(scheme)
        
        # Set content
        self.source_buffer.set_text(text_content)
        
        # Add to scroll window
        scroll.add(self.source_view)
        
        # Update references
        self.view = self.source_view
        self.buffer = self.source_buffer
        
        # Connect change handler
        self.changed_id = self.source_buffer.connect('changed', self.queue_update, True)
        
        # Show the new view
        self.source_view.show()
        
        # Add CSS class to help with styling
        self.source_view.get_style_context().add_class('code-editor')

        # Apply dynamic CSS so gutter and content match the note color
        self._apply_dynamic_css()
        # Apply a dynamic GtkSource style scheme so line numbers and text obey the note color
        self._apply_dynamic_scheme()
    
    def _add_code_indicator(self):
        """Add code editor control icons"""
        try:
            from sticky_unmodified import COLORS
            
            # Remove the inherited color button from base Note class
            for child in self.title_bar.get_children():
                if isinstance(child, Gtk.MenuButton):
                    tooltip = child.get_tooltip_text()
                    if tooltip and "Note Color" in tooltip:
                        self.title_bar.remove(child)
                        break
            
            # LEFT ICON: Code/text icon - EXCLUSIVE to CODE EDITOR
            # Shows color menu, converts to code if needed, or just changes color if already code
            icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Icons')
            code_icon_path = os.path.join(icon_dir, 'Code Template.png')
            code_icon = Gtk.Image.new_from_file(code_icon_path) if os.path.exists(code_icon_path) else Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.BUTTON)
            code_color_button = Gtk.MenuButton(
                image=code_icon,
                relief=Gtk.ReliefStyle.NONE,
                name='window-button',
                valign=Gtk.Align.CENTER
            )
            code_color_button.set_size_request(24, 24)
            code_color_button.set_tooltip_text(_("Code Editor Colors (exclusive to code)"))
            
            # Create CODE EDITOR color menu
            code_color_menu = Gtk.Menu()
            for color_name, display_name in COLORS.items():
                item = Gtk.MenuItem(label=display_name, visible=True)
                def on_code_color(_w, c=color_name):
                    # Already a code note - just change color
                    self.change_color(None, c)
                item.connect('activate', on_code_color)
                code_color_menu.append(item)
            code_color_button.set_popup(code_color_menu)
            
            # Insert code button at position 0 (LEFT)
            self.title_bar.pack_start(code_color_button, False, False, 0)
            self.title_bar.reorder_child(code_color_button, 0)
            code_color_button.show_all()
            
            # RIGHT ICON: Droplet icon - EXCLUSIVE TO TEXT NOTES
            # Shows color menu, converts to text if needed, or just changes color if already text
            text_color_icon_path = os.path.join(icon_dir, 'Text Template.png')
            text_color_icon = Gtk.Image.new_from_file(text_color_icon_path) if os.path.exists(text_color_icon_path) else Gtk.Image.new_from_icon_name('sticky-color', Gtk.IconSize.BUTTON)
            convert_button = Gtk.MenuButton(
                image=text_color_icon,
                relief=Gtk.ReliefStyle.NONE,
                name='window-button',
                valign=Gtk.Align.CENTER
            )
            convert_button.set_size_request(24, 24)
            convert_button.get_style_context().add_class('mode-switch')
            convert_button.set_tooltip_text(_("Text Note Colors (exclusive to text)"))
            
            # Store button reference
            self.mode_button = convert_button
            setattr(self, '_mode_button', convert_button)
            
            # Create TEXT note color menu (converts to text)
            convert_menu = Gtk.Menu()
            for color_name, display_name in COLORS.items():
                item = Gtk.MenuItem(label=display_name, visible=True)
                def on_text_color(_w, c=color_name):
                    if getattr(self, '_converting', False):
                        return
                    setattr(self, '_converting', True)
                    from src.note_converter import NoteConverter
                    convert_button.set_sensitive(False)
                    if not NoteConverter.code_to_text(self, c):
                        convert_button.set_sensitive(True)
                        setattr(self, '_converting', False)
                item.connect('activate', on_text_color)
                convert_menu.append(item)
            convert_button.set_popup(convert_menu)
            
            # Insert convert button at position 1 (RIGHT)
            self.title_bar.pack_start(convert_button, False, False, 0)
            self.title_bar.reorder_child(convert_button, 1)
            convert_button.show_all()
        except Exception as e:
            print(f"Failed to add code editor buttons: {e}")
            pass
    
    def change_color(self, widget, color_name):
        """Change code note color (internal helper, not bound to UI)."""
        # Remove old color class
        context = self.get_style_context()
        context.remove_class(self.color)
        
        # Add new color class
        self.color = color_name
        context.add_class(self.color)
        
        # Update saved data
        self.queue_update()
        # Update gutter renderer color
        self._update_gutter_color()
        # Re-apply CSS to update gutter/content colors for the new note color
        self._apply_dynamic_css()
        # Update dynamic scheme too
        self._apply_dynamic_scheme()

    def set_color(self, menu, color):
        """Override base set_color so droplet color updates gutter/scheme too."""
        try:
            super().set_color(menu, color)
        finally:
            self._update_gutter_color()
            self._apply_dynamic_css()
            self._apply_dynamic_scheme()

    def convert_to_text(self, widget, color_name):
        """Transform this Code note into a Text note preserving content, id, and file"""
        try:
            # Get complete note data including position and content
            info = self.get_note_data()
            
            # Set new properties for text note
            info['is_code_note'] = False
            info['color'] = color_name
            if 'language' in info:
                del info['language']  # Remove code-specific data
            
            # Create new text note
            from src.note_extended import NoteExtended
            new_note = NoteExtended(self.app, self.app, info)
            
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
            try:
                from src.note_extended import NoteExtended
                NoteExtended.show_info_dialog(self, _("Convert to Text"), _("Failed to convert: %s") % str(e))
            except Exception:
                print(f"Failed to convert to text: {e}")
    
    def get_info(self):
        """Override to save code note specific info"""
        info = super().get_info()
        info['is_code_note'] = True
        info['language'] = self.language_id
        return info

    def _install_gutter_background_renderer(self):
        """Install a low-priority gutter renderer that paints the gutter background to match note color."""
        try:
            class GutterBG(GtkSource.GutterRenderer):
                def __init__(self, rgba):
                    GtkSource.GutterRenderer.__init__(self)
                    self.rgba = rgba
                    # Enable drawing for all states in GtkSource 4
                    self.set_size(5)  # Gutter width
                    
                def set_rgba(self, rgba):
                    self.rgba = rgba
                    self.queue_draw()
                    
                def do_draw(self, cr, background_area, cell_area, start, end, state):
                    # In GtkSource 4, state is a flags enum
                    cr.set_source_rgba(self.rgba.red, self.rgba.green, self.rgba.blue, self.rgba.alpha)
                    cr.rectangle(background_area.x, background_area.y, 
                               background_area.width, background_area.height)
                    cr.fill()
                    
                def do_query_activatable(self, iter, area, event):
                    # GtkSource 4 requires this for click handling
                    return False
                    
            self._gutter_rgba = Gdk.RGBA()
            # Initialize with current note color
            from sticky_unmodified import COLOR_CODES
            color_code = COLOR_CODES.get(self.color, '#f6f907')
            self._gutter_rgba.parse(color_code)
            self._gutter_bg = GutterBG(self._gutter_rgba)
            
            # Get gutter controller in GtkSource 4 style
            gutter = self.source_view.get_gutter(Gtk.TextWindowType.LEFT)
            if gutter:
                # Insert with higher priority to ensure background is drawn first
                gutter.insert(self._gutter_bg, -100)
                
                # Set CSS name for additional styling
                gutter_window = self.source_view.get_window(Gtk.TextWindowType.LEFT)
                if gutter_window:
                    gutter_window.set_name(self._css_id + "-gutter-window")
        except Exception as e:
            print(f"Gutter setup error: {e}")
            self._gutter_bg = None

    def _update_gutter_color(self):
        """Update gutter renderer color to match current note color"""
        try:
            if hasattr(self, '_gutter_bg') and self._gutter_bg:
                from sticky_unmodified import COLOR_CODES
                color_code = COLOR_CODES.get(self.color, '#f6f907')
                self._gutter_rgba.parse(color_code)
                self._gutter_bg.set_rgba(self._gutter_rgba)
        except Exception as e:
            print(f"Error updating gutter color: {e}")

    def _apply_dynamic_css(self):
        """Apply dynamic CSS for editor styling"""
        try:
            from sticky_unmodified import COLOR_CODES
            
            color = COLOR_CODES.get(self.color, '#f6f907')
            text_color = '#eeeeee' if self.color == 'black' else '#303030'
            
            css = f"""
            #{self._css_id} {{
                background-color: {color};
                color: {text_color};
            }}
            #{self._css_id} text {{
                background-color: {color};
                color: {text_color};
            }}
            #{self._css_id} border {{
                background-color: {color};
            }}
            """
            
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, 
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            self._css_provider = provider
            
        except Exception as e:
            print(f"Error applying CSS: {e}")

    def _apply_dynamic_scheme(self):
        """Create and apply a GtkSource style scheme based on current note color"""
        try:
            from sticky_unmodified import COLOR_CODES
            
            # Create scheme directory if needed
            config_dir = os.path.join(os.path.expanduser("~/.config/notebook"), "styles")
            os.makedirs(config_dir, exist_ok=True)
            
            # Generate color scheme
            color = COLOR_CODES.get(self.color, '#f6f907')
            text_color = '#eeeeee' if self.color == 'black' else '#303030'
            scheme_id = f"note-{self.color}"
            
            scheme_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<style-scheme id="{scheme_id}" name="Note {self.color}" version="1.0">
  <author>Note Book</author>
  <description>Dynamic scheme for {self.color} notes</description>
  
  <!-- Basic Settings -->
  <style name="text"                        foreground="{text_color}" background="{color}"/>
  <style name="selection"                   background="#4a90d9"/>
  <style name="cursor"                      foreground="{text_color}"/>
  <style name="current-line"               background="{color}"/>
  <style name="line-numbers"               foreground="{text_color}" background="{color}"/>
  
  <!-- Syntax Highlighting -->
  <style name="def:comment"                foreground="#939393"/>
  <style name="def:constant"               foreground="#8f5902"/>
  <style name="def:boolean"                foreground="#0000ff"/>
  <style name="def:number"                 foreground="#0000ff"/>
  <style name="def:string"                 foreground="#2a6b30"/>
  <style name="def:keyword"                foreground="#a81919" bold="true"/>
  <style name="def:function"               foreground="#c4560c"/>
  <style name="def:type"                   foreground="#2f8c9c" bold="true"/>
  <style name="def:operator"               foreground="#ce5c00"/>
  <style name="def:identifier"             foreground="{text_color}"/>
  <style name="def:statement"              foreground="#204a87"/>
  <style name="def:preprocessor"           foreground="#ac7d00"/>
</style-scheme>'''
            
            # Save scheme
            scheme_path = os.path.join(config_dir, f"{scheme_id}.xml")
            with open(scheme_path, 'w') as f:
                f.write(scheme_xml)
            
            # Load scheme
            style_manager = GtkSource.StyleSchemeManager.get_default()
            style_manager.append_search_path(config_dir)
            scheme = style_manager.get_scheme(scheme_id)
            if scheme:
                self.source_buffer.set_style_scheme(scheme)
        except Exception as e:
            print(f"Error updating color scheme: {e}")
    
    def get_note_data(self):
        """Override to include code note metadata and actual text content"""
        # Get base info (position, size, color, title)
        info = self.get_info()
        # Add code-specific data
        info['is_code_note'] = True
        info['language'] = self.language_id
        # Add file and id info
        info['note_file'] = self.note_file
        if self.note_id:
            info['id'] = self.note_id
        return info
    
    def set_language(self, language_id):
        """Change the syntax highlighting language"""
        self.language_id = language_id
        language_manager = GtkSource.LanguageManager()
        language = language_manager.get_language(language_id)
        if language:
            self.source_buffer.set_language(language)
            # Update tooltip
            for child in self.title_bar.get_children():
                if isinstance(child, Gtk.Button) and not child.get_sensitive():
                    child.set_tooltip_text(_(f"Code Editor ({self.language_id})"))
                    break
