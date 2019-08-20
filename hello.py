# !/usr/bin/env python3

'''
Simple example to demonstrate dynamically adding and removing source elements
to a playing pipeline.
'''

import sys
import random

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

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

def update_vol(pipe):
    el = pipe.get_by_name("volume")
    el.set_property("volume", 0.8)

def main(args):
    GObject.threads_init()
    Gst.init(None)

    PIPELINE_DESC = '''audiotestsrc ! volume name=volume ! autoaudiosink'''
    pipe = Gst.parse_launch(PIPELINE_DESC)
    loop = GObject.MainLoop()

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    update_vol(pipe)

    # start play back and listen to events
    pipe.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # cleanup
    pipe.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
