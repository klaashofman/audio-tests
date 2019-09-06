# !/usr/bin/env python3

'''
capture from microphone, run one stream to the AGC, store the other file straight to a file
'''
import argparse
import math
import sys
import random
import time
import agc
import gi
from elements import Mic,Amplify, HighPassAudio, Level, Speaker, FileSink, Wavesrc
from dsp import Dsp, Agc

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst


def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ELEMENT:
        s = Gst.Message.get_structure(message)
        name =  s.get_name()
        # print ("bus callback: element:" + name)
        if name == 'level':
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

def main(args):
    mic_dev = "plughw:1"
    speak_dev = "plughw:0"

    GObject.threads_init()
    Gst.init(None)

    parser = argparse.ArgumentParser(description='raspi-recording-calibration')
    parser.add_argument('-m', '--mic', help='alsa microphone address, e.g. plughw:1', required=False)
    parser.add_argument('-s', '--speaker', help='alsa speaker address, e.g plughw:0', required=False)
    args = vars(parser.parse_args())
    if args['mic']:
        mic_dev = args['mic']
    if args['speaker']:
        speak_dev = args['speaker']

    src = Mic(alsadev=mic_dev)
    #src = Wavesrc("capture-indoor-1m.wav")
    level_clean = Level(name='lclean')
    level_agc = Level(name='lagc')
    filter = HighPassAudio(cutoff=300)
    amply = Amplify()
    amply.set(amp_db=50.0)
    speaker = Speaker(alsadev=speak_dev)
    sink_clean = FileSink("clean.wav")
    sink_agc = FileSink("agc.wav")
    dsp = Dsp(enable=True)
    # enable AGC with default settings
    dsp.set_agc(enable=True)
    # max noise suppression
    dsp.set_ns(enable=True, level = 3)

    PIPELINE_DESC = src.get() + ''' ! audio/x-raw,rate=48000,format=S32LE,channels=1 ! audioconvert ! ''' + filter.get() + ''' ! ''' + amply.get() \
                    + ''' ! audioconvert ! ''' + level_clean.get() + ''' ! tee name=t ! ''' \
                    + ''' queue ! audioconvert ! fakesink'''  \
                    + ''' t. ! queue ! audioconvert ! wavenc ! ''' + sink_clean.get() \
                    + ''' t. ! queue ! audioconvert ! ''' + dsp.get() + '''wavenc ! ''' + sink_agc.get()

    print("pipeline: gst-launch-1.0 " + PIPELINE_DESC)

    pipe = Gst.parse_launch(PIPELINE_DESC)
    loop = GObject.MainLoop()

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

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
