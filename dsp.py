# !/usr/bin/env python3

'''
Gstreamer DSP element (webrtc)
'''
import gi

from enum import Enum

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('GstController', '1.0')
from gi.repository import GLib, GObject, Gst, GstController

class Mode(Enum):
# Adaptive mode intended for situations in which an analog volume control
# is unavailable. It operates in a similar fashion to the adaptive analog
# mode, but with scaling instead applied in the digital domain. As with
# the analog mode, it additionally uses a digital compression stage.
        kAdaptiveDigital = 1

 # Fixed mode which enables only the digital compression stage also used by
 # the two adaptive modes.
 #
 # It is distinguished from the adaptive modes by considering only a
 # short time-window of the input signal. It applies a fixed gain through
 # most of the input level range, and compresses (gradually reduces gain
 # with increasing level) the input signal at higher levels. This mode is
 # preferred on embedded devices where the capture signal level is
 # predictable, so that a known gain can be applied.
        kFixedDigital = 2


class Agc:
    def __init__(self):
        self.enable = False
        self.mode = Mode.kAdaptiveDigital
        self.target_level_dbfs = 0
        self.gain_db = 15
        self.limiter_enable = False

class NoiseSuppress:
    def __init__(self):
        self.enable = False
        self.level = 0 # 0 = low, 3 = very-high

class AEC:
    def __init__(self):
        self.enable = False
        self.suppression_level = 1 # 0 - low, 1 - moderate, 2 - high
        self.voice_detection_enabled = False
        self.voice_likehood = 1 # 0 - very low, 3 - high
        self.voice_frame_size = 10 # 10 ms - 30 ms, higher frames = better accuracy but less updates
        self.agnostic_delay = False;


class Dsp:
    def __init__(self, enable = True ):
        self.agc=Agc()
        self.ns=NoiseSuppress()
        self.aec = AEC()
        self.src = ''' webrtcdsp'''
        self.enable = enable
        self.echo_cancel_enable = False
        self.extended_filter = False
        self.high_pass_filter = False

    def set_agc(self, enable=True, mode=Mode.kAdaptiveDigital, target=0, gain=15, limiter=True):
        self.agc.enable = enable
        self.agc.mode = mode
        self.agc.target_level_dbfs = target
        self.agc.gain_db = gain
        self.agc.limiter_enable = limiter

    def set_ns(self, enable=True, level=0):
        self.ns.enable = enable
        self.ns.level = level

    def set_aec(self, enable=True, level = 1, voice_detect = False, voice_likehood = 1, agnostic_delay = False):
        self.aec.enable = enable
        self.aec.suppression_level = level
        self.aec.voice_detection_enabled= voice_detect
        self.aec.voice_likehood = voice_likehood
        self.aec.agnostic_delay = agnostic_delay

    def get(self):
        if not self.enable:
            return ''''''

        s = self.src
        s += ''' high-pass-filter=''' + ( '''true''' if self.high_pass_filter else '''false''')
        s += ''' extended-filter=''' +  ( '''true''' if self.extended_filter else '''false''')
        s += ''' noise-suppression=''' + ( '''true''' if self.ns.enable else '''false''')
        s += ''' noise-suppression-level=''' + str(self.ns.level)
        s += ''' gain-control=''' + ( '''true''' if self.agc.enable else '''false''')
        s += ''' target-level-dbfs=''' + str(self.agc.target_level_dbfs)
        s += ''' compression-gain-db=''' + str(self.agc.gain_db)
        s += ''' limiter=''' + ( '''true'''  if self.agc.limiter_enable else '''false''' )
        # echo cancellar
        s +=  ''' echo-cancel=''' + ( '''true''' if self.aec.enable else '''false''')
        s +=  ''' echo-suppression-level=''' + str(self.aec.suppression_level)
        s +=  ''' voice-detection=''' + ( '''true''' if self.aec.voice_detection_enabled else '''false''')
        s +=  ''' voice-detection-likelihood=''' + str(self.aec.voice_likehood)
        s +=  ''' voice-detection-frame-size-ms=''' + str(self.aec.voice_frame_size)
        s +=  ''' ! '''
        return s

