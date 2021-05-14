import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
from io import BytesIO
from datetime import datetime as dt
from datetime import timedelta as tidt
import os,sys

motion_detected     = False

class MyMotionDetector(array.PiMotionAnalysis):
    def analyse(self, a):
        global motion_detected
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > 60).sum() > 10:
            motion_detected     = True
        else:
            motion_detected     = False

def loop(loglevel=1):
    global motion_detected
    camera = PiCamera()
    #Full view but 4 times lower resolution
    camera.resolution   = (1640,1232) 
    camera.framerate    = 30

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)

    #Use circular io buffor
    stream              = circular(camera, seconds=5)
    camera.start_recording(stream, format="h264")

    #Perform motion analysis from second splitter port
    camera.start_recording('/dev/null', format='h264', splitter_port=2,
                            motion_output=MyMotionDetector(camera))
    
    start   = dt.now()
    #Do some stuff while motion is not detected and wait
    while dt.now()-start < tidt(seconds=30.):
        if loglevel == 0::
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
            camera.split_recording(stream,splitter_port=1)
            camera.wait_recording(5)
            stream.copy_to("{}_after.mp4".format(fname))
            stream.clear()

            command = "ffmpeg -f concat --framerate {} -safe 0 -i {}_cat.txt -c copy {}.mp4 1> /dev/null 2> /dev/null && ".format(int(camera.framerate),fname,fname)
            command += "rm -f {}_before.mp4 && ".format(fname)
            command += "rm -f {}_during.mp4 && ".format(fname)
            command += "rm -f {}_after.mp4 && ".format(fname)
            command += "rm -f {}_cat.txt &".format(fname)
            with open("{}_cat.txt".format(fname),"w") as fi:
                fi.write("file '{}_before.mp4'\n".format(fname))
                fi.write("file '{}_during.mp4'\n".format(fname))
                fi.write("file '{}_after.mp4' \n".format(fname))
                fi.write("#{}".format(command))
            #Only run this line if you have enough CPU grunt
            #os.system(command)

    #Stop all recording
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    camera.stop_preview()

if __name__ == "__main__":
    main()
