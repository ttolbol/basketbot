#!/usr/bin/env python2

# Imports the monkeyrunner modules used by this program
import sys
import time
import os
import png
import numpy as np
from PIL import Image
import pyscreenshot
import subprocess

lag = 1.1

adbpath = "adb"

countdown_seconds = 3

screen_topleft_x = 0
screen_topleft_y = 0
screen_botright_x = 0
screen_botright_y = 0

def get_screen_tuple():
    return (screen_topleft_x, screen_topleft_y, screen_botright_x, screen_botright_y)

def find_screen():
    # Find the borders of the casted screen by going from the left, right, top and bottom
    # until something interesting happens.
    global screen_topleft_x
    global screen_topleft_y
    global screen_botright_x
    global screen_botright_y

    print "Fullscreen the viewer. Starting in %d seconds..." % countdown_seconds
    for i in xrange(countdown_seconds, 0, -1):
        print i
        time.sleep(1)
    print "Starting..."
    print

    im = capture()
    pix = im.load()

    # Find left border
    for x in xrange(10, im.width):
        r, g, b = pix[x,im.height/2]
        s = sum([r,g,b])
        if s >= 243:
            screen_topleft_x = x
            break

    # Find right border
    for x in xrange(im.width-10, 0, -1):
        r, g, b = pix[x,im.height/2]
        s = sum([r,g,b])
        if s >= 243:
            screen_botright_x = x
            break

    # Find top border
    for y in xrange(20, im.height):
        r, g, b = pix[im.width/4,y]
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen_topleft_y = y
            break

    # Find bottom border
    for y in xrange(im.height-20, 0, -1):
        r, g, b = pix[im.width/4,y]
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen_botright_y = y
            break


    if abs(screen_topleft_x - screen_botright_x) < 50:
        print "Very small width of screen. Try again."
        find_screen()

    if abs(screen_topleft_y - screen_botright_y) < 50:
        print "Very small height of screen. Try again."
        find_screen()

def capture(x1=None, y1=None, x2=None, y2=None):
    if x1 and y1 and x2 and y2:
        box = (x1, y1, x2, y2)
    else:
        box = None
    grab = pyscreenshot.grab(bbox=box)
    return grab

def capture_screen():
    return capture(screen_topleft_x,  screen_topleft_y,
                   screen_botright_x, screen_botright_y)

def run_process(cmd, timeout = 60):
    start_time = time.clock()

    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)

    stdout_output = ""
    stderr_output = ""

    did_timeout = False

    while True:
        retcode = p.poll() #returns None while subprocess is running
        stdout_line = p.stdout.read()
        stdout_output += stdout_line.decode("ascii")
        stderr_line = p.stderr.read()
        stderr_output += stderr_line.decode("ascii")
        elapsed_time = time.clock() - start_time
        if retcode is not None:
            break
        elif elapsed_time >= timeout:
            p.terminate()
            did_timeout = True
            break

    return (stdout_output.strip(), stderr_output.strip(), retcode, elapsed_time, did_timeout)

def run_adb(command):
    output, _, _, _, _ = run_process(adbpath + " " + command)
    return output


# Takes pixels, return the x,y position of the ball
def find_ball(pix):
    # TODO
    pass

# Takes pixels, return the x,y position of the target
def find_target(img):
    # TODO
    pass


###################
#   Starts here   #
###################

devices = run_adb("devices")
print devices

tmp_split_devices = devices.split("\n")
if len(tmp_split_devices) > 1 and "device" in tmp_split_devices[1]:
    print "Connected!"
    print
else:
    print "No device. Aborting."
    sys.exit(1)

# Find the streamed screen by scanning for bight color from each of the for sides.
# If this doesn't work, simply comment this out and hardcode the approximate location
# in the values above starting with screen_*.
find_screen()


while True:
    startTime = time.time()
    #os.system(adbpath+" shell screencap -p /mnt/sdcard/sc.png")
    im1 = capture_screen()
    print "Screenshot 1"
    startTime2 = time.time()
    im2 = capture_screen()
    print "Screenshot 2"
    #os.system(adbpath+" shell screencap -p /mnt/sdcard/sc2.png")
    #os.system(adbpath+" pull /mnt/sdcard/sc.png")
    #os.system(adbpath+" pull /mnt/sdcard/sc2.png")
    #os.system(adbpath+" shell rm /mnt/sdcard/sc.png")
    #im = Image.open("sc.png")
    pix = im1.load()

    width  = im1.width
    height = im1.height

    approx_ball_height = height - 10
    approx_target_height = 247

    #find ball
    bx = 0
    n = 0
    for i in range(width):
        if np.average(pix[i,approx_ball_height]) < 200:
            bx += i
            n += 1
    if n > 0:
        bx = bx/n

    #find targets prev. position
    tx1 = 0
    n = 0
    for i in range(width):
        if np.average(pix[i,approx_target_height]) < 200:
            tx1 += i
            n += 1
    if n > 0:
        tx1 = tx1/n

    #os.system(adbpath+" shell rm /mnt/sdcard/sc.png")
    #im = Image.open("sc2.png")
    pix = im2.load()

    #find targets new position
    tx2 = 0
    n = 0
    for i in range(width):
        if np.average(pix[i,approx_target_height]) < 200:
            tx2 += i
            n += 1
    if n > 0:
        tx2 = tx2/n

    endTime = time.time()

    timeDif = (startTime2-startTime)
    print (tx2-tx1)/timeDif

    velocity = 0
    if tx2 > tx1:
        velocity = 220
    if tx2 < tx1:
        velocity = -220
    delay = (endTime-startTime2)+lag


    change = velocity*delay
    print velocity
    tx2 += change

    while tx2 > 940 or tx2 < 140:
        if tx2 > 940:
            txx = tx2-940
            tx2 = 940-(tx2-940)

        if tx2 < 140:
            tx2 = 140-(tx2-140)

    run_adb("shell input swipe "+str(bx)+" 1764 "+str(tx2)+" 734")
    time.sleep(1.3)
