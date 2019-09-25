# !/usr/bin/env python3

'''
Video encoder pipeline featuring live feedback from camera and local capture to file
'''
import os
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

def main(args):
    #os.environ['GST_DEBUG'] = '*:3,base*:5,caps:2,v4l2src:3,*264*:5,avdec_h264:7,ximagesink:7'
    os.environ['GST_DEBUG'] = '*:3'

    GObject.threads_init()
    Gst.init(None)

    # camera caps of internal camera laptop
    VIDEO_RAW_CAPS = 'video/x-raw,format=YUY2,width=640,height=480,framerate=30/1'
    VIDEO_CAPS_RTP = 'application/x-rtp,media=video,encoding-name=H264,payload=98,clock-rate=90000'
    VIDEOSRC=''' v4l2src device=/dev/video0 do-timestamp=true ! videorate'''

    RTPSINK = '''udpsink host=localhost port=5000 sync=true async=false '''
    RTPSOURCE = '''udpsrc port=5000'''
    RTP_PAYLOAD = '''98'''

    TEE_RTP = ''' tee name=t '''
    TEE_RAW = ''' tee name=r '''

    #PIPELINE_DESC = ''' v4l2src device=/dev/video0 ! ''' + VIDEO_RAW_CAPS + ''' ! videoconvert ! ''' + TEE_RAW + '''! queue ! x264enc ! h264parse ! rtph264pay ! ''' + TEE_RTP + '''!''' +  VIDEO_CAPS_RTP + ''' ! queue ! '''  + SINK
    #PIPELINE_DESC += '''  t. ! ''' + VIDEO_CAPS_RTP + ''' ! queue ! filesink location=capture.av '''
    #PIPELINE_DESC += ''' r.  ! queue !  +  ''' + VIDEO_RAW_CAPS + ''' ximagesink '''

    # PIPELINE_DESC =  ''' v4l2src device=/dev/video0 ! ''' + VIDEO_RAW_CAPS + ''' ! tee name=s ! videoconvert ! ''' + TEE_RAW + '''! queue  ! ximagesink '''
    # PIPELINE_DESC += ''' r. ! queue ! filesink location=capture.raw '''
    # #PIPELINE_DESC += ''' s. ! queue ! ''' + VIDEO_CAPS_ENC + ''' ! x264enc tune=zerolatency ! h264parse ! rtph264pay ! filesink location=capture.avc '''
    # PIPELINE_DESC += ''' s. ! queue ! videoconvert ! x264enc tune=zerolatency ! h264parse ! rtph264pay ! filesink location=capture.avc '''
    SRC = VIDEOSRC + ''' ! ''' + VIDEO_RAW_CAPS + ''' ! videoconvert ! '''
    ENCODER = ''' x264enc ! video/x-h264,profile=baseline ! h264parse ! rtph264pay pt=''' + RTP_PAYLOAD  + ''' ! ''' + VIDEO_CAPS_RTP

    DECODER = ''' application/x-rtp,media=video,clock-rate=90000,payload=''' + RTP_PAYLOAD + ''' ! queue ! rtph264depay ! h264parse !  avdec_h264 '''
    SINK =  ''' videoconvert ! ximagesink '''

    # without rtp overhead, fps=ok, very high delay > 2 sec
    PIPELINE_DESC = SRC + ''' queue ! ''' + ENCODER + ''' ! queue ! '''
    PIPELINE_DESC += DECODER + ''' ! queue ! ''' + SINK

    # transcoding pipeline using RTP (not working currently)
    PIPELINE_DESC = SRC + ''' queue ! ''' + ENCODER + ''' ! queue ! ''' + RTPSINK
    PIPELINE_DESC += RTPSOURCE  + ''' ! queue ! ''' + DECODER + ''' ! ''' + SINK

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
