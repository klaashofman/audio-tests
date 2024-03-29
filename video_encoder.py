# !/usr/bin/env python3

'''
Video encoder pipeline featuring live feedback from camera and local capture to file
'''
import argparse
import os
import sys
import random

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gst

from elements import FileSink

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

def main(args):
    parser = argparse.ArgumentParser(description='video demo tool')
    parser.add_argument('-t', '--transcode', help='h264-encode and -decode a camera stream', required=False)
    parser.add_argument('-r', '--rtp', help='h264-encode and -decode a camera and RTP stram', required=False)
    parser.add_argument('-c', '--capture', help='store camera output in h264 encoded file, specify filename',
                        required=False)
    parser.add_argument('-D', '--debug', help='gstreamer debug string')
    args = vars(parser.parse_args())

    os.environ['GST_DEBUG'] = '*:3'
    if args['debug']:
        os.environ['GST_DEBUG'] = args['debug']

    GObject.threads_init()
    Gst.init(None)

    # camera caps of internal camera laptop
    VIDEO_RAW_CAPS = 'video/x-raw,format=YUY2,width=640,height=480,framerate=30/1'
    VIDEO_CAPS_RTP = 'application/x-rtp,media=video,encoding-name=H264,payload=98,clock-rate=90000'
    VIDEOSRC=''' v4l2src device=/dev/video0 do-timestamp=true ! videorate'''

    RTPSINK = '''udpsink host=127.0.0.1,port=5000 '''
    RTPSOURCE = '''udpsrc port=5000'''
    RTP_PAYLOAD = '''98'''

    SRC = VIDEOSRC + ''' ! ''' + VIDEO_RAW_CAPS + ''' ! videoconvert ! '''
    ENCODER = ''' x264enc ! video/x-h264,profile=baseline ! h264parse ! rtph264pay pt=''' + RTP_PAYLOAD  + ''' ! ''' + VIDEO_CAPS_RTP

    DECODER = ''' application/x-rtp,media=video,clock-rate=90000,payload=''' + RTP_PAYLOAD + ''' ! queue ! rtph264depay ! h264parse !  avdec_h264 '''
    SINK =  ''' videoconvert ! ximagesink '''

    if args['transcode']:
        # without rtp overhead, fps=ok, very high delay > 2 sec
        PIPELINE_DESC = SRC + ''' queue ! ''' + ENCODER + ''' ! queue ! '''
        PIPELINE_DESC += DECODER + ''' ! queue ! ''' + SINK

    if args['rtp']:
        # transcoding pipeline using RTP (not working currently)
        PIPELINE_DESC = RTPSOURCE + ''' ! queue ! ''' + DECODER + ''' ! ''' + SINK
        PIPELINE_DESC += SRC + ''' queue ! ''' + ENCODER + ''' ! queue ! ''' + RTPSINK

    if args['capture']:
        filename = args['capture']
        sink = FileSink(filename)
        # simply capture and store video data
        PIPELINE_DESC = SRC + '''queue''' + ENCODER + ''' ! queue ! ''' + sink.get()

    print("pipeline: gst-launch-1.0 " + PIPELINE_DESC)

    pipe = Gst.parse_launch(PIPELINE_DESC)
    loop = GObject.MainLoop()

    bus = pipe.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

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
