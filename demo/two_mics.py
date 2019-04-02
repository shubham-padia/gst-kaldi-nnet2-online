#!/usr/bin/env python
#
# Copyright (c) 2013 Tanel Alumae
# Copyright (c) 2008 Carnegie Mellon University.
#
# Inspired by the CMU Sphinx's Pocketsphinx Gstreamer plugin demo (which has BSD license)
#
# Licence: BSD

from gi.repository import GObject, Gst, Gtk, Gdk
import sys
import os
import gi
import copy
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
GObject.threads_init()
Gdk.threads_init()

Gst.init(None)


def get_text_view_and_buffer():
    text = Gtk.TextView()
    text_buffer = text.get_buffer()
    text.set_wrap_mode(Gtk.WrapMode.WORD)

    return text, text_buffer


def get_scrolled_window():
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_border_width(2)
    scrolled_window.set_policy(
        Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)

    return scrolled_window

class DemoApp(object):
    """GStreamer/Kaldi Demo Application"""

    def __init__(self):
        """Initialize a DemoApp object"""
        self.init_gui()
        self.init_gst()

    def init_gui(self):
        """Initialize the GUI components"""
        self.window = Gtk.Window()
        self.window.connect("destroy", self.quit)
        self.window.set_title("NTU Live ASR v3.0 (SG-CN)")
        self.window.set_name("MyWindow")
        self.window.set_default_size(1200, 800)
        self.window.set_border_width(10)

        self.lang = 'EN'
        # Container
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        grid = Gtk.Grid()

        self.scrolled_window = get_scrolled_window()
        self.text, self.textbuf = get_text_view_and_buffer()
        self.scrolled_window.add(self.text)

        self.scrolled_window_gg = get_scrolled_window()
        self.ggtext, self.ggtextbuf = get_text_view_and_buffer()
        self.scrolled_window_gg.add(self.ggtext)

        # frame
        self.frameLV = Gtk.Frame()
        self.frameLV.set_label("SCDF - Caller ")
        self.frameGG = Gtk.Frame()
        self.frameGG.set_label("SCDF - Operator")

        # Tag
        self.tag = Gtk.TextTag()
        self.tag.set_property('family', 'Monospace')
        self.tag.set_property('family-set', True)
        self.tag.set_property('scale', 0.9)
        self.tag.set_property('scale-set', True)
        self.tag.set_property('background', 'orange')
        self.tag_table = Gtk.TextTagTable()
        self.tag_table.add(self.tag)

        # A list to hold our active tags
        self.tags_on = []
        # Our Bold tag.
        # self.tag_bold = self.textbuf.create_tag("bold", weight=Pango.WEIGHT_BOLD)

        # Button
        self.button = Gtk.Button("Speak")
        self.button.connect('clicked', self.button_clicked)
        # self.buttonClr = Gtk.Button("Clear", halign=Gtk.Align.END)
        self.buttonClr = Gtk.Button("Clear")
        self.buttonClr.connect('clicked', self.buttonClr_clicked)

        self.frameLV.add(self.scrolled_window)
        self.frameGG.add(self.scrolled_window_gg)

        hbox.pack_start(self.frameLV, True, True, 1)
        hbox.pack_start(self.frameGG, True, True, 1)
        vbox.pack_start(hbox, True, True, 1)

        vbox.pack_start(self.button, False, True, 2)
        vbox.pack_start(self.buttonClr, False, True, 1)
        vbox.pack_start(grid, False, True, 1)

        self.window.add(vbox)
        self.window.show_all()

    def quit(self, window):
        Gtk.main_quit()

    def init_gst(self):
        """Initialize the speech components"""
        self.pulsesrc = Gst.ElementFactory.make("pulsesrc", "pulsesrc")
        if self.pulsesrc == None:
            print >> sys.stderr, "Error loading pulsesrc GST plugin. You probably need the gstreamer1.0-pulseaudio package"
            sys.exit()
        self.audioconvert = Gst.ElementFactory.make(
            "audioconvert", "audioconvert")
        self.audioresample = Gst.ElementFactory.make(
            "audioresample", "audioresample")
        self.asr = Gst.ElementFactory.make("kaldinnet2onlinedecoder", "asr")
        self.fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.prev_hyp_len = 0
        self.partial_tag = self.textbuf.create_tag(
            tag_name="partial_tag", foreground="red")
        self.textbuf.apply_tag(
            self.partial_tag, self.textbuf.get_end_iter(), self.textbuf.get_end_iter())

        if self.asr:
            model_file = "models/final.mdl"
            if not os.path.isfile(model_file):
                print >> sys.stderr, "Models not downloaded? Run prepare-models.sh first!"
                sys.exit(1)
            self.asr.set_property("fst", "models/HCLG.fst")
            self.asr.set_property("model", model_file)
            self.asr.set_property("word-syms", "models/words.txt")
            self.asr.set_property("feature-type", "mfcc")
            self.asr.set_property("mfcc-config", "conf/mfcc.conf")
            self.asr.set_property(
                "ivector-extraction-config", "conf/ivector_extractor.fixed.conf")
            self.asr.set_property("max-active", 7000)
            self.asr.set_property("beam", 10.0)
            self.asr.set_property("lattice-beam", 6.0)
            self.asr.set_property("do-endpointing", True)
            self.asr.set_property(
                "endpoint-silence-phones", "1:2:3:4:5:6:7:8:9:10")
            self.asr.set_property("use-threaded-decoder", False)
            self.asr.set_property("chunk-length-in-secs", 0.2)
        else:
            print >> sys.stderr, "Couldn't create the kaldinnet2onlinedecoder element. "
            if os.environ.has_key("GST_PLUGIN_PATH"):
                print >> sys.stderr, "Have you compiled the Kaldi GStreamer plugin?"
            else:
                print >> sys.stderr, "You probably need to set the GST_PLUGIN_PATH envoronment variable"
                print >> sys.stderr, "Try running: GST_PLUGIN_PATH=../src %s" % sys.argv[0]
            sys.exit()

        # initially silence the decoder
        self.asr.set_property("silent", True)

        self.pipeline = Gst.Pipeline()
        for element in [self.pulsesrc, self.audioconvert, self.audioresample, self.asr, self.fakesink]:
            self.pipeline.add(element)
        self.pulsesrc.link(self.audioconvert)
        self.audioconvert.link(self.audioresample)
        self.audioresample.link(self.asr)
        self.asr.link(self.fakesink)

        self.asr.connect('partial-result', self._on_partial_result)
        self.asr.connect('final-result', self._on_final_result)
        self.pipeline.set_state(Gst.State.PLAYING)

    def _on_partial_result(self, asr, hyp):
        """Delete any previous selection, insert text and select it."""
        Gdk.threads_enter()
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        end_iter = self.textbuf.get_end_iter()
        prev_hyp_start = self.textbuf.get_end_iter()
        prev_hyp_start.backward_chars(self.prev_hyp_len)
        self.textbuf.remove_tag(self.partial_tag, prev_hyp_start, end_iter)
        self.textbuf.delete(prev_hyp_start, end_iter)

        current_hyp_len = len(hyp)
        self.textbuf.insert(self.textbuf.get_end_iter(), hyp)
        current_hyp_len_start = self.textbuf.get_end_iter()
        current_hyp_len_start.backward_chars(current_hyp_len)
        self.textbuf.apply_tag(
            self.partial_tag, current_hyp_len_start, self.textbuf.get_end_iter())
        self.prev_hyp_len = current_hyp_len
        # self.textbuf.apply_tag()

        # iter = self.textbuf.get_iter_at_mark(ins)
        # print(hyp)
        # iter.backward_chars(len(hyp))
        # self.textbuf.move_mark(ins, iter)
        self.textbuf.end_user_action()
        Gdk.threads_leave()

    def _on_final_result(self, asr, hyp):
        Gdk.threads_enter()
        """Insert the final result."""
        # All this stuff appears as one single action
        print(hyp)
        self.textbuf.begin_user_action()
        end_iter = self.textbuf.get_end_iter()
        prev_hyp_start = self.textbuf.get_end_iter()
        prev_hyp_start.backward_chars(self.prev_hyp_len)
        self.textbuf.delete(prev_hyp_start, end_iter)

        new_end_iter = self.textbuf.get_end_iter()
        self.textbuf.insert(new_end_iter, hyp)
        # print(hyp)
        if (len(hyp) > 0):
            self.textbuf.insert(new_end_iter, " ")

        self.prev_hyp_len = 0
        self.textbuf.end_user_action()
        Gdk.threads_leave()

    def button_clicked(self, button):
        """Handle button presses."""
        if button.get_label() == "Speak":
            button.set_label("Stop")
            self.asr.set_property("silent", False)
        else:
            button.set_label("Speak")
            self.asr.set_property("silent", True)

    def buttonClr_clicked(self, buttonClr):
        """Clear textarea button presses."""
        self.textbuf.set_text("")
        self.ggtextbuf.set_text("")

    def btn_press_event(self, switch, flag):
        """Handle switch button presses."""
        print 'switch state', switch.props.active
        # print 'switch is toggle-ed'
        switch_state = switch.props.active

        if (switch_state):
            self.useGoogle = True
            self.frameGG.show()
        else:
            self.useGoogle = False
            self.frameGG.hide()


if __name__ == '__main__':
    app = DemoApp()
    Gdk.threads_enter()
    Gtk.main()
    Gdk.threads_leave()
