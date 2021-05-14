import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
from io import BytesIO

def main():
    camera = PiCamera()
    camera.resolution   = (640, 480)
    camera.framerate    = 10
    #camera.resolution   = (1920, 1080)
    #camera.framerate    = 30
    #camera.resolution   = (2592, 1944)
    #camera.framerate    = 15

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)

    #setup circular io buffer
    stream              = circular(camera, seconds=10)
    
    #start actual recording
    camera.start_recording(stream, format="h264")
    #camera.start_recording('my_video.mjpg')
    camera.start_recording('my_video.mp4', format="h264", splitter_port=2)
    camera.wait_recording(20)
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    stream.copy_to("my_stream.mp4",seconds=10)
    camera.stop_preview()

if __name__ == "__main__":
    main()
