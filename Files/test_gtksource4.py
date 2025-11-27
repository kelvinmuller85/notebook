import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, GtkSource, Gdk

# Create a window with a source view to test GtkSource 4
win = Gtk.Window()
buf = GtkSource.Buffer()
view = GtkSource.View(buffer=buf)
lang_mgr = GtkSource.LanguageManager()
python_lang = lang_mgr.get_language('python')
buf.set_language(python_lang)
buf.set_highlight_syntax(True)
win.add(view)
win.show_all()
Gtk.main()
