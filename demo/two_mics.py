#!/usr/bin/env python
#
# Copyright (c) 2013 Tanel Alumae
# Copyright (c) 2008 Carnegie Mellon University.
#
# Inspired by the CMU Sphinx's Pocketsphinx Gstreamer plugin demo (which has BSD license)
#
# Licence: BSD

from gi.repository import GObject, Gst, Gtk, Gdk
from transcription_view import TranscriptionView
import sys
import os
import gi
import copy
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
GObject.threads_init()


class DemoApp(object):
    """GStreamer/Kaldi Demo Application"""

    def __init__(self):
        """Initialize a DemoApp object"""
        self.transcription_1 = TranscriptionView("Speaker 1", "pulsesrc", "pulsesrc", False, 'blue')
        self.transcription_2 = TranscriptionView("Speaker 2", "pulsesrc", "pulsesrc", False, 'green')
        self.init_gui()

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

        self.transcription_1.frame.set_label("SCDF - Caller ")
        self.transcription_2.frame.set_label("SCDF - Operator")

        # Tag
        self.tag = Gtk.TextTag()
        self.tag.set_property('family', 'Monospace')
        self.tag.set_property('family-set', True)
        self.tag.set_property('scale', 0.9)
        self.tag.set_property('scale-set', True)
        self.tag.set_property('background', 'orange')
        self.tag_table = Gtk.TextTagTable()
        self.tag_table.add(self.tag)

        # Button
        self.button = Gtk.Button("Speak")
        self.button.connect('clicked', self.button_clicked)
        # self.buttonClr = Gtk.Button("Clear", halign=Gtk.Align.END)
        self.buttonClr = Gtk.Button("Clear")
        self.buttonClr.connect('clicked', self.buttonClr_clicked)

        hbox.pack_start(self.transcription_1.frame, True, True, 1)
        hbox.pack_start(self.transcription_2.frame, True, True, 1)

        vbox.pack_start(hbox, True, True, 1)

        vbox.pack_start(self.button, False, True, 2)
        vbox.pack_start(self.buttonClr, False, True, 1)
        vbox.pack_start(grid, False, True, 1)

        self.window.add(vbox)
        self.window.show_all()

    def quit(self, window):
        Gtk.main_quit()

    def button_clicked(self, button):
        """Handle button presses."""
        if button.get_label() == "Speak":
            button.set_label("Stop")
            self.transcription_1.asr.set_property("silent", False)
            self.transcription_2.asr.set_property("silent", False)
        else:
            button.set_label("Speak")
            self.transcription_1.asr.set_property("silent", True)
            self.transcription_2.asr.set_property("silent", True)

    def buttonClr_clicked(self, buttonClr):
        """Clear textarea button presses."""
        self.transcription_1.textbuf.set_text("")
        self.transcription_2.textbuf.set_text("")


if __name__ == '__main__':
    app = DemoApp()
    Gdk.threads_enter()
    Gtk.main()
    Gdk.threads_leave()
