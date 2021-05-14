import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
from io import BytesIO

class MyMotionDetector(array.PiMotionAnalysis):
    def analyse(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > 60).sum() > 10:
            print('Motion detected!')

def main():
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
    
    camera.wait_recording(20)
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    stream.copy_to("my_stream.mp4",seconds=10)
    camera.stop_preview()

if __name__ == "__main__":
    main()
