from gi.repository import Gtk, Pango

def get_text_view_and_buffer():
    text = Gtk.TextView()
    text_buffer = text.get_buffer()
    text.set_wrap_mode(Gtk.WrapMode.WORD)
    text.modify_font(Pango.FontDescription('Ubuntu 20'))

    return text, text_buffer


def get_scrolled_window():
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_border_width(2)
    scrolled_window.set_policy(
        Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)

    return scrolled_window