import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
from io import BytesIO
from datetime import datetime as dt
from datetime import timedelta as tidt

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

def main():
    global motion_detected
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

    #Perform motion analysis from second splitter port
    camera.start_recording('/dev/null', format='h264', splitter_port=2,
                            motion_output=MyMotionDetector(camera))
    
    start   = dt.now()
    #Do some stuff while motion is not detected and wait
    while dt.now()-start < tidt(seconds=30.):
        print("Waiting")
        camera.wait_recording(1)
        if motion_detected:
            fname   ="{}".format(dt.strftime(dt.now(),"%Y%m%d_%H%M%S"))
            camera.split_recording("{}_during.mp4".format(fname),splitter_port=1)
            stream.copy_to("{}_before.mp4".format(fname),seconds=10)
            stream.clear()
            while motion_detected:
                camera.wait_recording(1)
            camera.split_recording(stream,splitter_port=1)

    #Stop all recording
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    camera.stop_preview()

if __name__ == "__main__":
    main()
