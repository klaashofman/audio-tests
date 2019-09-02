# !/usr/bin/env python3

'''
Wave-file Analyser
'''

import argparse
import sys
import wave
import audioop
import math

class Rms:
    def __init__(self, name):
        self.channels = 0
        self.samplewidth = 0
        self.avg = 0.0
        self.rms = 0.0
        self.name = name

    def stats(self):
        try:
            self.wav = wave.open(self.name, mode='rb')
        except wave.Error:
            pass

        self.channels = self.wav.getnchannels()
        self.samplewidth = self.wav.getsampwidth()
        self.framerate = self.wav.getframerate()
        # this printed value does not seem to be correct
        # either it is the sample produced by gstreamer
        # either there is a bug here
        # anyway value needs to be correct in order to continue
        self.samplecount = self.wav.getnframes()

        print ("channels: " + str(self.channels) + " samplewidth (bits): " + str(self.samplewidth * 8) )
        print ("framerate: " + str(self.framerate) + " samplecount: " + str(self.samplecount))
        frames = self.wav.getnframes()
        width = self.wav.getsampwidth()

        self.wav.rewind()
        self.avg = audioop.avg(self.wav.readframes(frames), width)
        self.wav.rewind()
        rms = audioop.rms(self.wav.readframes(frames), width)
        self.rms = 20 * math.log10(rms)
        print ("avg: " + str(self.avg) + " rms: " + str(self.rms))


def main(args):
    parser  = argparse.ArgumentParser(description="wav-file analyzer")
    parser.add_argument('-f', '--file', help="location of wave file", required=True)
    args = vars(parser.parse_args())
    file_name = args['file']
    rms = Rms(file_name)
    rms.stats()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
