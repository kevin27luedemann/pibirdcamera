#!/usr/bin/python3
import numpy as np
import time
from picamera import PiCamera
from picamera import array
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
from fractions import Fraction

def capture_to_image_obj():
    camera  = PiCamera()

    # Create the in-memory stream
    stream = BytesIO()
    #reso                = (2592, 1944) #largest possible resolution (full view)
    reso                = (3280,2464) #largest possible resolution (full view)
    #reso                = (1920, 1088)
    camera.resolution   = reso

    camera.start_preview()
    # Camera warm-up time
    time.sleep(2)

    camera.capture(stream, format='jpeg')
    # "Rewind" the stream to the beginning so we can read its content
    stream.seek(0)
    image = Image.open(stream)

    fig,ax  = plt.subplots()
    ax.imshow(image,cmap="inferno") # for grayscale
    plt.show()

def main():

    # Create the in-memory stream
    #reso                = (2592, 1944) #largest possible resolution (full view)
    reso                = (3280,2464) #largest possible resolution (full view)
    #reso                = (1920, 1080)
    #camera.framerate    = 2.0
    #camera.resolution   = reso
    #camera.framerate    = 30
    camera  = PiCamera( 
                        resolution=reso
                        #resolution=reso,
                        #framerate=Fraction(1,6),
                        #sensor_mode=3
                        )
    #camera.shutter_speed = 10000000
    #camera.iso          = 800

    camera.start_preview()
    # Camera warm-up time
    #time.sleep(20)
    time.sleep(2)

    output              = array.PiYUVArray(camera,size=reso)
    camera.capture(output, format='yuv')
    #output              = array.PiRGBArray(camera,size=(2592,1944))
    #camera.capture(output, format='rgb')
    # "Rewind" the stream to the beginning so we can read its content

    cmaps   = ["inferno","inferno","inferno"]
    #cmaps   = ["Reds","Greens","Blues"]
    fig,ax  = plt.subplots(1,3)
    for i in range(3):
        ax[i].imshow(output.array[:,:,i],cmap=cmaps[i]) # for grayscale

    fig2,ax2  = plt.subplots()
    ax2.imshow(output.array[:,:,0],cmap="gray") # for grayscale
    plt.show()

if __name__ == "__main__":
        main()
