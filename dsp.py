# !/usr/bin/env python3

'''
Gstreamer DSP element (webrtc)
'''
import argparse
import math
import sys
import gi
import select

import agc

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('GstController', '1.0')
from gi.repository import GLib, GObject, Gst, GstController

class dsp:
    def __init__(self, enable = True, aec=False, noise=False, extended_filter=False, hp_filter=False, agc=True):
        self.src = ''' webrtcdsp'''
        self.enable = enable
        self.echo_cancel_enable = aec
        self.extended_filter = extended_filter
        self.high_pass_filter = hp_filter
        self.noise_suppression_enable = noise
        self.noise_suppression_level = 1
        self.agc_enable = agc
        self.agc_target_level_dbfs = 0
        self.agc_gain_db = 15
        self.agc_limiter = True
        self.agc_mode = 1
        self.voice_detection = False

    def get(self):
        if not self.enable:
            return ''''''

        s = self.src
        s += ''' echo-cancel=''' + ('''true''' if self.echo_cancel_enable else '''false''')
        s += ''' high-pass-filter=''' + ( '''true''' if self.high_pass_filter else '''false''')
        s += ''' extended-filter=''' +  ( '''true''' if self.extended_filter else '''false''')
        s += ''' noise-suppression=''' + ( '''true''' if self.noise_suppression_enable else '''false''')
        s += ''' gain-control=''' + ( '''true''' if self.agc_enable else '''false''')
        s += ''' target-level-dbfs=''' + str(self.agc_target_level_dbfs)
        s += ''' compression-gain-db=''' + str(self.agc_gain_db)
        s += ''' ! '''
        return s

