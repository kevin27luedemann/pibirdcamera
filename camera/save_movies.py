import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
from io import BytesIO
from datetime import datetime as dt
from datetime import timedelta as tidt
import os,sys,signal
from optparse import OptionParser

motion_detected     = False
keep_running        = True

def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

class MyMotionDetector(array.PiMotionAnalysis):
    def analyse(self, a):
        global motion_detected
        a = np.sqrt(np.square(a['x'].astype(float)) +
                    np.square(a['y'].astype(float)))

        if      not(motion_detected)    and \
                (a > 30).sum() > 5:
            motion_detected         = True
            self.no_motion_frames   = 0

        elif    motion_detected         and \
                (a > 30).sum() <= 5     and \
                self.no_motion_frames <= self.camera.framerate:
            self.no_motion_frames  += 1

        elif    motion_detected         and \
                self.no_motion_frames > self.camera.framerate:
            motion_detected         = False
            self.no_motion_frames   = 0

def loop(loglevel=1,concat=False):
    global motion_detected
    global stopped
    camera = PiCamera()
    #Full view but 4 times lower resolution
    camera.resolution   = (1640,1232) 
    camera.framerate    = 30

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)

    #Use circular io buffor
    stream              = circular(camera, seconds=10)
    camera.start_recording(stream, format="h264")

    #Perform motion analysis from second splitter port with lowest resolution.
    #Reson is performance and enhanced noise removal
    camera.start_recording('/dev/null', format='h264',
                            splitter_port=2, resize=(640,480),
                            motion_output=MyMotionDetector(camera,size=(640,480)))
    
    #Do some stuff while motion is not detected and wait
    #start   = dt.now()
    #while dt.now()-start < tidt(seconds=30.):
    while keep_running:
        if loglevel == 0:
            print("Waiting")
        camera.wait_recording(1)
        if motion_detected:
            fname   ="/videos/{}".format(dt.strftime(dt.now(),"%Y%m%d_%H%M%S"))
            if loglevel < 1:
                print("Motion at: {}".format(fname.split("/")[-1]))
            camera.split_recording("{}_during.mp4".format(fname),splitter_port=1)
            stream.copy_to("{}_before.mp4".format(fname))
            stream.clear()
            while motion_detected:
                camera.wait_recording(1)
            camera.wait_recording(5)
            while motion_detected:
                camera.wait_recording(1)
            camera.split_recording(stream,splitter_port=1)

            command = "ffmpeg -f concat --framerate {} -safe 0 -i {}_cat.txt -c copy {}.mp4 1> /dev/null 2> /dev/null && ".format(int(camera.framerate),fname,fname)
            command += "rm -f {}_before.mp4 && ".format(fname)
            command += "rm -f {}_during.mp4 && ".format(fname)
            command += "rm -f {}_cat.txt &".format(fname)
            with open("{}_cat.txt".format(fname),"w") as fi:
                fi.write("file '{}_before.mp4'\n".format(fname))
                fi.write("file '{}_during.mp4'\n".format(fname))
                fi.write("#{}".format(command))
            #Only run this line if you have enough CPU grunt
            if concat:
                os.system(command)

    #Stop all recording
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    camera.stop_preview()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM,signal_handler)

    parser = OptionParser()

    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")
    parser.add_option(  "-c", "--concat", dest="concat",
                        action="store_true",default=False,
                        help="Concat before and during videos and delete")

    (options, args) = parser.parse_args()

    loop(loglevel=int(options.loglevel),concat=options.concat)
