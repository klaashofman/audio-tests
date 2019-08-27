# !/usr/bin/env python3

'''
Simple example to demonstrate dynamically adding and removing source elements
to a playing pipeline.
'''
import argparse
import sys
import random
import time

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

class test:
    def __init__(self, strategy, pipe, volume, loop):
        self.strategy = strategy
        self.pipe = pipe
        self.volume = volume
        self.delta = +0.1
        self.loop = loop
        self.elapsed = 0

class src:
    def __init__(self):
        self.src = '''audiotestsrc'''

    def audiotestsrc(self, freq):
        self.src = '''audiotestsrc'''
        self.src += ''' is-live=true name=volume freq=''' + str(freq) + ''' ! audio/x-raw,rate=48000,format=S32LE,channels=1 ! '''

    def filesrc(self, filename):
        self.src = '''filesrc '''
        self.src += ''' location=''' + filename + ''' ! wavparse ! '''

    def get(self):
        return self.src

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

class filesink:
    def __init__(self, name):
        self.sink = ''' filesink'''
        self.name = name

    def get(self):
        s = self.sink
        s += ''' location=''' + self.name
        return s

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

def dispose_src_cb(src):
    src.set_state(Gst.State.NULL)

def update_vol(pipe, vol):
    el = pipe.get_by_name("volume")
    el.set_property("volume", vol)

def test_increment(pdata):
    print("volume" + str(pdata.volume))
    if pdata.volume >= 1.0:
        pdata.delta = -0.1
    if pdata.volume < 0.1:
        # stop the test
        pdata.loop.quit()
        return False

    update_vol(pdata.pipe, pdata.volume)
    pdata.volume += pdata.delta
    return True

def test_oscillating(pdata):
    print("count: " + str(pdata.elapsed) + " volume: " + str(pdata.volume))
    if pdata.elapsed % 3 == 0:
        pdata.volume = 1.0
    else:
        pdata.volume = 0.1

    if pdata.elapsed % 20 == 0:
        #end the test
        pdata.loop.quit()
        return False

    update_vol(pdata.pipe, pdata.volume)
    return True

def timeout_cb(pdata):
    pdata.elapsed += 1
    if pdata.strategy == 'incremental':
        return test_increment(pdata)
    if pdata.strategy == 'oscillating':
        return test_oscillating(pdata)
    else:
        print("unkown strategy, aborting...")
        return False

    return True

def main(args):
    GObject.threads_init()
    Gst.init(None)

    volume = 0.1
    file_name = 'test.wav'
    test_strategy = 'none'

    parser = argparse.ArgumentParser(description='gstreamer-agc-testtool')
    parser.add_argument('-a', '--agc', help='enable/disable agc', required=True)
    parser.add_argument('-f', '--file', help='name of output file', required=False)
    parser.add_argument('-i', '--input', help='name of the input file', required=False)
    parser.add_argument('-t', '--test', help='test strategy: incremental, oscillating', required=False)

    args = vars(parser.parse_args())
    if args['agc'] == 'enable':
        agc_enable = True
    else:
        agc_enable = False

    if args['file']:
        file_name = args[ 'file']

    testsrc = src()
    if args['input']:
        input_file = args[ 'input']
        testsrc.filesrc(filename = input_file)
    else:
        # 1 khz sinus test tone
        testsrc.audiotestsrc(1000.0)

    if args['test']:
        test_strategy = args[ 'test']

    testdsp = dsp(agc=agc_enable)
    testsink = filesink(name=file_name)
    PIPELINE_DESC = testsrc.get() + ''' audioconvert !''' + testdsp.get() + ''' wavenc !''' + testsink.get()

    print("pipeline: gst-launch-1.0 " + PIPELINE_DESC)

    pipe = Gst.parse_launch(PIPELINE_DESC)
    loop = GObject.MainLoop()

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    pdata = test(strategy=test_strategy, pipe=pipe, volume=volume, loop=loop)

    GLib.timeout_add_seconds(1, timeout_cb, pdata)

    # start play back and listen to events
    pipe.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except KeyboardInterrupt:
        pass

    # cleanup
    # the wav-encoder needs an explicit eos, otherwise the file ends up being corrupt
    pipe.send_event(Gst.Event.new_eos())
    pipe.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
