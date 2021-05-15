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
from PIL import Image

motion_detected     = False
keep_running        = True

def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

class MotionDetec(array.PiMotionAnalysis):
    def __init__(self,  camera,size=None,
                        threshold=30,
                        num_blocks=10,
                        num_no_motion_frames=30,
                        local_motion_mask=np.ones((40,30))):
        super().__init__(camera,size)
        self.no_motion_frames       = 0
        self.threshold              = threshold
        self.num_blocks             = num_blocks
        self.num_no_motion_frames   = num_no_motion_frames
        self.motion_mask            = np.transpose(local_motion_mask)
        self.motion_mask            = np.pad(   self.motion_mask,
                                                ((0,0),(0,1)),
                                                mode="constant",
                                                constant_values=0)
        
    def analyse(self, a):
        global motion_detected
        a = np.sqrt(np.square(a['x'].astype(float)) +
                    np.square(a['y'].astype(float)))

        a = a*self.motion_mask

        if      not(motion_detected)    and \
                (a > self.threshold).sum() > self.num_blocks:
            motion_detected         = True
            self.no_motion_frames   = 0

        elif    motion_detected         and \
                (a > self.threshold).sum() > self.num_blocks:
            self.no_motion_frames   = 0

        elif    motion_detected         and \
                (a > self.threshold).sum() <= self.num_blocks     and \
                self.no_motion_frames <= self.num_no_motion_frames:
            self.no_motion_frames  += 1

        elif    motion_detected         and \
                self.no_motion_frames > self.num_no_motion_frames:
            motion_detected         = False
            self.no_motion_frames   = 0

def loop(   praefix="",
            loglevel=1,
            concat=False,
            buffer_time=5,
            motion_mask=np.ones((40,30))):
    global motion_detected
    global keep_running

    #Full view but 4 times lower resolution
    camera = PiCamera()
    if camera.revision == "imx219":
        camera.resolution   = (1640,1232) 
    else:
        camera.resolution   = (1296,972) 
    camera.framerate    = 30

    #start warmup befor recording to get exposure right
    if loglevel == 0:
        print("Starting warmup")
    camera.start_preview()
    time.sleep(2)
    if loglevel == 0:
        print("Done with warmup")

    #Use circular io buffor
    if loglevel == 0:
        print("Create 10 seconds circular io buffer and start recording h264")
    stream              = circular(camera, seconds=buffer_time)
    camera.start_recording(stream, format="h264")

    #Perform motion analysis from second splitter port with lowest resolution.
    #Reson is performance and enhanced noise removal
    if loglevel == 0:
        print("Set up motion detection on 640x480 resolution")
    camera.start_recording('/dev/null', format='h264',
                            splitter_port=2, resize=(640,480),
                            motion_output=MotionDetec(  camera,
                                                        size=(640,480),
                                                        num_no_motion_frames=camera.framerate,
                                                        local_motion_mask=motion_mask))
    
    #Do some stuff while motion is not detected and wait
    #start   = dt.now()
    #while dt.now()-start < tidt(seconds=30.):
    while keep_running:
        if loglevel == 0:
            print("Waiting for motion")
        camera.wait_recording(1)
        if motion_detected:
            fname   = "{}{}".format(praefix,dt.strftime(dt.now(),"%Y%m%d_%H%M%S"))
            if loglevel < 2:
                print("Motion at: {}".format(fname.split("/")[-1]))
            camera.split_recording("{}_during.mp4".format(fname),splitter_port=1)
            stream.copy_to("{}_before.mp4".format(fname),seconds=buffer_time)
            stream.clear()
            while motion_detected:
                camera.wait_recording(1)
            camera.wait_recording(5)
            while motion_detected:
                camera.wait_recording(1)
            if loglevel == 0:
                print("Motion done, splitting back to circular io")
            camera.split_recording(stream,splitter_port=1)

            command = "ffmpeg -f concat -safe 0 -i {}_cat.txt -c copy {}.mp4 1> /dev/null 2> /dev/null && ".format(fname,fname)
            command += "rm -f {}_before.mp4 && ".format(fname)
            command += "rm -f {}_during.mp4 && ".format(fname)
            command += "rm -f {}_cat.txt &".format(fname)
            if loglevel == 0:
                print(command)
            with open("{}_cat.txt".format(fname),"w") as fi:
                fi.write("file '{}_before.mp4'\n".format(fname))
                fi.write("file '{}_during.mp4'\n".format(fname))
                fi.write("#{}".format(command))
            #Only run this line if you have enough CPU grunt
            if concat:
                if loglevel == 0:
                    print("Running ffmpeg command")
                os.system(command)

    #Stop all recording
    if loglevel == 0:
        print("Closing everything off")
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()
    camera.stop_preview()

def create_mask(loglevel=1,praefix=""):
    if loglevel == 0:
        print("Some image will be taken")
    camera = PiCamera()
    if camera.revision == "imx219":
        camera.resolution   = (1640,1232) 
    else:
        camera.resolution   = (1296,972) 
    if loglevel == 0:
        print(camera.resolution)
    fname   = praefix+"mask_image"
    if loglevel == 0:
        print("Warmup for exposure")
    camera.start_preview()
    time.sleep(2)

    if loglevel == 0:
        print("Capture image")
    camera.capture(fname+".png")

    if loglevel == 0:
        print("Taking second image with 640 by 480")
    camera.capture(fname+"640_480.png",resize=(640,480))

    camera.stop_preview()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    parser = OptionParser()

    parser.add_option(  "-f", "--praefix", dest="praefix",default="",
                        help="File praefix and folder localtion")
    parser.add_option(  "-m", "--mask", dest="mask",default="",
                        help="Filename for the mask image")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")
    parser.add_option(  "-c", "--concat", dest="concat",
                        action="store_true",default=False,
                        help="Concat before and during video and delete both")
    parser.add_option(  "", "--create_mask", dest="create_mask",
                        action="store_true",default=False,
                        help="Take an image for the creation of motion mask")

    (options, args) = parser.parse_args()

    if options.create_mask:
        create_mask(    loglevel=int(options.loglevel),
                        praefix=options.praefix)
    else:
        if options.mask != "":
            img         = Image.open(options.mask).convert('LA').resize((40,30))
            mask        = np.array(img.getdata())[:,0].reshape((40,30))
            mask[mask>0]= 1.0
        else:
            mask        = np.ones((40,30))

        loop(   praefix=options.praefix,
                loglevel=int(options.loglevel),
                concat=options.concat,
                motion_mask=mask)
