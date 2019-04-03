from utils import get_text_view_and_buffer, get_scrolled_window
import os
import sys
from gi.repository import Gtk, Gst, Gdk

Gst.init(None)
Gdk.threads_init()

class TranscriptionView:
    def __init__(self, name, src_type, src_name, should_set_device_id, name_color):
        self.name = name
        self.gst = Gst
        self.gdk = Gdk
        self.init_gui(name_color)
        self.prev_hyp_len = 0
        self.asr = self.init_gst(self.textbuf, self.partial_tag, src_type, src_name, should_set_device_id)

    def init_gui(self, name_color):
        self.scrolled_window = get_scrolled_window()
        self.text, self.textbuf = get_text_view_and_buffer()
        self.scrolled_window.add(self.text)

        self.frame = Gtk.Frame()
        self.frame.add(self.scrolled_window)
        self.partial_tag = self.textbuf.create_tag(
            tag_name="partial_tag", foreground="red")
        self.name_tag = self.textbuf.create_tag(
            tag_name="name", foreground=name_color)

    def init_gst(self, text_buffer, partial_tag, src_type, src_name, should_set_device_id):
        """Initialize the speech components"""
        pulsesrc = self.gst.ElementFactory.make(src_type, src_type)
        if should_set_device_id:
            pulsesrc.set_property("device", src_name)
        if pulsesrc == None:
            print >> sys.stderr, "Error loading pulsesrc GST plugin. You probably need the gstreamer1.0-pulseaudio package"
            sys.exit()
        audioconvert = self.gst.ElementFactory.make(
            "audioconvert", "audioconvert")
        audioresample = self.gst.ElementFactory.make(
            "audioresample", "audioresample")
        asr = self.gst.ElementFactory.make("kaldinnet2onlinedecoder", self.name)
        fakesink = self.gst.ElementFactory.make("fakesink", "fakesink")

        text_buffer.apply_tag(
            partial_tag, text_buffer.get_end_iter(), text_buffer.get_end_iter())

        if asr:
            model_file = "models/final.mdl"
            if not os.path.isfile(model_file):
                print >> sys.stderr, "Models not downloaded? Run prepare-models.sh first!"
                sys.exit(1)
            asr.set_property("fst", "models/HCLG.fst")
            asr.set_property("model", model_file)
            asr.set_property("word-syms", "models/words.txt")
            asr.set_property("feature-type", "mfcc")
            asr.set_property("mfcc-config", "conf/mfcc.conf")
            asr.set_property(
                "ivector-extraction-config", "conf/ivector_extractor.fixed.conf")
            asr.set_property("max-active", 7000)
            asr.set_property("beam", 10.0)
            asr.set_property("lattice-beam", 6.0)
            asr.set_property("do-endpointing", True)
            asr.set_property(
                "endpoint-silence-phones", "1:2:3:4:5:6:7:8:9:10")
            asr.set_property("use-threaded-decoder", False)
            asr.set_property("chunk-length-in-secs", 0.2)
        else:
            print >> sys.stderr, "Couldn't create the kaldinnet2onlinedecoder element. "
            if os.environ.has_key("GST_PLUGIN_PATH"):
                print >> sys.stderr, "Have you compiled the Kaldi GStreamer plugin?"
            else:
                print >> sys.stderr, "You probably need to set the GST_PLUGIN_PATH envoronment variable"
                print >> sys.stderr, "Try running: GST_PLUGIN_PATH=../src %s" % sys.argv[0]
            sys.exit()

        # initially silence the decoder
        asr.set_property("silent", True)

        pipeline = self.gst.Pipeline()
        for element in [pulsesrc, audioconvert, audioresample, asr, fakesink]:
            pipeline.add(element)
        pulsesrc.link(audioconvert)
        audioconvert.link(audioresample)
        audioresample.link(asr)
        asr.link(fakesink)

        asr.connect('partial-result', self._on_partial_result, text_buffer)
        asr.connect('final-result', self._on_final_result, text_buffer)
        pipeline.set_state(self.gst.State.PLAYING)

        return asr

    def _on_partial_result(self, asr, hyp, text_buffer):
        """Delete any previous selection, insert text and select it."""
        self.gdk.threads_enter()
        # All this stuff appears as one single action
        text_buffer.begin_user_action()
        end_iter = text_buffer.get_end_iter()
        prev_hyp_start = text_buffer.get_end_iter()
        prev_hyp_start.backward_chars(self.prev_hyp_len)
        text_buffer.remove_tag(self.partial_tag, prev_hyp_start, end_iter)
        text_buffer.delete(prev_hyp_start, end_iter)

        text_to_insert = "%s: %s\n" % (self.name, hyp)
        name_len = len(self.name) + 2                       # 2 added for `: `
        current_hyp_len = len(text_to_insert)
        text_buffer.insert(text_buffer.get_end_iter(), text_to_insert)
        
        current_hyp_len_start = text_buffer.get_end_iter()
        current_hyp_len_start.backward_chars(current_hyp_len - name_len)
        text_buffer.apply_tag(
            self.partial_tag, current_hyp_len_start, text_buffer.get_end_iter())

        name_start = text_buffer.get_end_iter()
        name_start.backward_chars(current_hyp_len)
        text_buffer.apply_tag(
            self.name_tag, name_start, current_hyp_len_start)

        self.prev_hyp_len = current_hyp_len
        text_buffer.end_user_action()
        self.gdk.threads_leave()

    def _on_final_result(self, asr, hyp, text_buffer):
        self.gdk.threads_enter()
        """Insert the final result."""
        # All this stuff appears as one single action
        text_buffer.begin_user_action()
        end_iter = text_buffer.get_end_iter()
        prev_hyp_start = text_buffer.get_end_iter()
        prev_hyp_start.backward_chars(self.prev_hyp_len)
        text_buffer.delete(prev_hyp_start, end_iter)
        
        new_end_iter = text_buffer.get_end_iter()
        text_to_insert = "%s: %s\n" % (self.name, hyp)
        name_len = len(self.name) + 2                       # 2 added for `: `
        current_hyp_len = len(text_to_insert)
        text_buffer.insert(text_buffer.get_end_iter(), text_to_insert)
        
        current_hyp_len_start = text_buffer.get_end_iter()
        current_hyp_len_start.backward_chars(current_hyp_len - name_len)
        name_start = text_buffer.get_end_iter()
        name_start.backward_chars(current_hyp_len)
        text_buffer.apply_tag(
            self.name_tag, name_start, current_hyp_len_start)

        self.prev_hyp_len = 0
        text_buffer.end_user_action()
        self.gdk.threads_leave()
