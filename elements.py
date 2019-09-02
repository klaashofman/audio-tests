# !/usr/bin/env python3

'''
Common gstreamer elements
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

class src:
    def __init__(self):
        self.src = '''audiotestsrc'''

    def audiotestsrc(self, freq):
        self.src = '''audiotestsrc'''
        self.src += ''' is-live=true name=volume freq=''' + str(freq)

    def filesrc(self, filename):
        self.src = '''filesrc '''
        self.src += ''' location=''' + filename + ''' ! wavparse ! '''

    def get(self):
        return self.src

class filesink:
    def __init__(self, name):
        self.sink = ''' filesink'''
        self.name = name

    def get(self):
        s = self.sink
        s += ''' location=''' + self.name
        return s

class Mic:
    def __init__ (self, alsadev="plughw:1"):
        self.dev = alsadev

    def get(self):
        s = '''alsasrc device=''' + self.dev
        return s

class Level:
    def __init__ (self):
        pass
    def get(self):
        s = ''' level name=level'''
        return s

class Amplify:
    def __init__(self, amp=1.0, clip=0):
        self.amp = amp
        self.clip = clip

    def get(self):
        s = ''' audioamplify name=amp amplification=''' + str(self.amp) + ''' clipping-method=''' + str(self.clip) + '''  '''
        return s

# LADSPA high pass filter with programmable cutoff frequency
class HighAudio:
    def __init__(self, cutoff=440.0):
        self.cutoff = cutoff

    def get(self):
        s = ''' ladspa-filter-so-hpf '''
        s += ''' cutoff-frequency=''' + self.cutoff
        return s