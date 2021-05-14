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
fname               = ""

class MyMotionDetector(array.PiMotionAnalysis):
    def analyse(self, a):
        global motion_detected
        global fname
        np.save("{}.npy".format(fname),a)
        a = np.sqrt(
            np.square(a['x'].astype(float)) +
            np.square(a['y'].astype(float))
            ).clip(0, 255).astype(np.uint8)
        if (a > 60).sum() > 10:
            motion_detected     = True
        else:
            motion_detected     = False

def loop(loglevel=1):
    global motion_detected
    global fname
    camera = PiCamera()
    #Full view but 4 times lower resolution
    #camera.resolution   = (1640,1232) 
    camera.resolution   = (640,480) 
    camera.framerate    = 1

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)

    #Use circular io buffor
    stream              = circular(camera, seconds=20)
    camera.start_recording(stream, format='h264',
                            motion_output=MyMotionDetector(camera))
    
    start   = dt.now()
    #Do some stuff while motion is not detected and wait
    while dt.now()-start < tidt(seconds=20.):
        fname   ="{}".format(dt.strftime(dt.now(),"%Y%m%d_%H%M%S"))
        print("waiting")
        camera.wait_recording(1)

    #Stop all recording
    camera.stop_recording()
    stream.copy_to("fname.mp4".format(fname),seconds=10)
    camera.stop_preview()

if __name__ == "__main__":
    loop()
