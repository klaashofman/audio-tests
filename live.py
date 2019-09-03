# !/usr/bin/env python3

'''
capture from microphone adjust signal levels and print out dB
'''
import argparse
import math
import sys
import gi
import select

import agc
from elements import Mic, Level, Amplify

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('GstController', '1.0')
from gi.repository import GLib, GObject, Gst, GstController

LOGGING=False


def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ELEMENT:
        s = Gst.Message.get_structure(message)
        name =  s.get_name()
        # print ("bus callback: element:" + name)
        if name == 'level' and LOGGING == True:
            # limitiation: only works with mono channel
            rms_db = s.get_value("rms")[0]
            rms_norm = math.pow(10, rms_db / 20)
            rms_norm = 0.0
            peak_db = s.get_value("peak")[0]
            decay_db = s.get_value("decay")[0]
            print ("RMS(dB)=" + str(rms_db) + " RMS(norm)=" + str(rms_norm))
            print ("Peak(dB)" + str(peak_db))

    elif t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

def update_vol(pdata):
    print ("volume:" + str(pdata.vol))
    cs = pdata.cs
    rv = cs.set(1, pdata.vol)
    print ("cs: " + rv)
    pdata.vol += 1.0

    if pdata.vol == 10.0:
        pdata.vol =0

    #el = pipe.get_by_name("amp")
    #vol  = el.get_property("amplification")
    #vol += step
    #print ("new volume: " + str(vol))
    #el.set_property("amplification", step)

def keypress_cb(pdata):
    input = select.select([sys.stdin], [], [], 1)[0]
    if input:
        key = sys.stdin.readline().rstrip()
        print("key:" + key)
        if key == '+':
            pdata.vol += 1.0
            update_vol(pdata)
        elif key == '-':
            pdata.vol -= 1.0
            update_vol(pdata)
        elif key == 'L':
            global LOGGING=True
        elif key == 'l':
            global LOGGING=False

    return True

class Live:
    def __init__(self, pipe):
        self.pipe = pipe
        self.vol = 1.0
        self.cs = GstController.InterpolationControlSource.new()
        el = pipe.get_by_name("amp")
        el.add_control_binding(GstController.DirectControlBinding.new(el, "amplification", self.cs))
        # control.set_property("volume", GstController.InterpolationMode.LINEAR)
        # control.set_property("amplification", GstController.InterpolationMode.LINEAR)

def main(args):
    GObject.threads_init()
    Gst.init(None)

    parser = argparse.ArgumentParser(description='raspi-recording-calibration')
    parser.add_argument('-t', '--testsrc', help='use a test src ipv microphone', required=False)

    args = vars(parser.parse_args())
    if args [ 'testsrc' ]:
        src = agc.src()
        src.audiotestsrc(1000.0)
    else:
        src = Mic()

    level = Level()
    amp = Amplify()
    PIPELINE_DESC = src.get() + ''' ! ''' + amp.get() + ''' ! audio/x-raw,rate=48000,format=S32LE,channels=1 ! audioconvert ! ''' + level.get() + ''' ! autoaudiosink'''

    print("pipeline: gst-launch-1.0 " + PIPELINE_DESC)

    pipe = Gst.parse_launch(PIPELINE_DESC)
    loop = GObject.MainLoop()

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    live = Live(pipe=pipe)

    # poll for keyboard events
    GLib.timeout_add(100, keypress_cb, live)

    pipe.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except KeyboardInterrupt:
        pass

    # pass EOS to all elements prior of switching down
    pipe.send_event(Gst.Event.new_eos())
    pipe.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
