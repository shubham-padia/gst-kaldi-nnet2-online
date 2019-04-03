from gi.repository import Gtk, Pango
from envparse import env

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

def get_properties():
    env.read_envfile()

    return {
        'MODEL_FILE': env('MODEL_FILE', default="models/final.mdl"),
        'FST': env('FST', default="models/HCLG.fst"),
        'WORD_SYMS': env('WORD_SYMS', default="models/words.txt"),
        'FEATURE_TYPE': env('FEATURE_TYPE', default='mfcc'),
        'MFCC_CONFIG': env('MFCC_CONFIG', default="conf/mfcc.conf"),
        'IVECTOR_EXTRACTION_CONFIG': env('IVECTOR_EXTRACTION_CONFIG', default="conf/ivector_extractor.fixed.conf"),
        'MAX_ACTIVE': env.int('MAX_ACTIVE', default=7000),
        'BEAM': env('BEAM', default=10.0, cast=float),
        'LATTICE_BEAM': env('LATTICE_BEAM', default=6.0, cast=float),
        'DO_ENDPOINTING': env('DO_ENDPOINTING', default=True, cast=bool),
        'ENDPOINT_SILENCE_PHONES': env('ENDPOINT_SILENCE_PHONES', default='1:2:3:4:5:6:7:8:9:10'),
        'USE_THREADED_DECODER': env('USE_THREADED_DECODER', default=False, cast=bool),
        'CHUNK_LENGTH_IN_SECS': env('CHUNK_LENGTH_IN_SECS', 0.2, cast=bool)
    }


