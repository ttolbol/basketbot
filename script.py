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
from geometry import *

lag = 1.1

adbpath = "adb"

countdown_seconds = 3

sample_count = 2

approx_ball_height   = -80 # Plus height
approx_target_height = 266

# Init the screen to just 0's
screen = Box(Point(0,0), Point(0,0))
screen_topleft_x = 0
screen_topleft_y = 0
screen_botright_x = 0
screen_botright_y = 0

class Snapshot:
    def __init__(self, ball_pos, target_pos, timestamp):
        self.ball_pos = ball_pos
        self.target_pos = target_pos
        self.timestamp = timestamp

    def __str__(self):
        return "%s, %s, %s" % (self.ball_pos, self.target_pos, self.timestamp)

    def __repr__(self):
        return str(self)

def find_screen():
    # Find the borders of the casted screen by going from the left, right, top and bottom
    # until something interesting happens.

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
            screen.topleft.x = x
            break

    # Find right border
    for x in xrange(im.width-10, 0, -1):
        r, g, b = pix[x,im.height/2]
        s = sum([r,g,b])
        if s >= 243:
            screen.botright.x = x
            break

    # Find top border
    for y in xrange(20, im.height):
        r, g, b = pix[im.width/4,y]
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen.topleft.y = y
            break

    # Find bottom border
    for y in xrange(im.height-20, 0, -1):
        r, g, b = pix[im.width/4,y]
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen.botright.y = y
            break


    if screen.width() < 50:
        print "Very small width of screen. Try again."
        find_screen()

    if screen.height() < 50:
        print "Very small height of screen. Try again."
        find_screen()

def capture(box=None):
    grab = pyscreenshot.grab(bbox=box)
    return grab

def capture_screen():
    return capture(screen.to_tuple())

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
    stdout, stderr, _, _, _ = run_process(adbpath + " " + command)
    return stdout + stderr


# Takes pixels, return the x,y position of the ball
def find_ball(pix):
    width, height = screen.dim()

    # Approx ball height 
    y = height + approx_ball_height

    # Swipe left to right
    for x in xrange(width):
        r, g, b = pix[x,y]

        if r == 255 and g == 150 and b == 48:
            return Point(x,y)

    print "Ball was not found."
    sys.exit(1)

# Takes pixels, return the x,y position of the target
def find_target(pix):
    width, height = screen.dim()

    # Approx target height 
    y = approx_target_height

    # Swipe left to right
    for x in xrange(width):
        r, g, b = pix[x,y]

        if r == 255 and g == 38 and b == 18:
            return Point(x,y)

    print "Target was not found."
    sys.exit(1)

def get_ball_target(pix):
    return (find_ball(pix), find_target(pix))

def sample_ball_target(samples=sample_count, delay=0):
    l = []

    start_time = time.time()

    for i in range(samples):
        screen_time = time.time()
        img = capture_screen()
        pix = img.load()

        ball_pos, target_pos = get_ball_target(pix)

        snapshot = Snapshot(ball_pos, target_pos, screen_time - start_time)
        l.append(snapshot)

        if delay:
            time.sleep(delay)

    return l


def map_range(value, low1, high1, low2, high2):
    return low2 + (high2 - low2) * (value - low1) / (high1 - low1)

def scale_to_full_hd(x, y, small_width, small_height, big_width=1080, big_height=1920):
    return map_range(x, 0, small_width, 0, big_width), map_range(y, 0, small_height, 0, big_height)




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

width, height = screen.dim()

# Tried my luck with a simplified event loop that uses the helper functions above
while True:
    start_time = time.time()

    samples = sample_ball_target()

    end_time = time.time()

    sample1 = samples[0]
    sample2 = samples[1]

    bx  = sample1.ball_pos.x
    by  = sample1.ball_pos.y

    ty  = sample1.target_pos.y
    tx1 = sample1.target_pos.x
    tx2 = sample2.target_pos.x

    dt = sample2.timestamp - sample1.timestamp
    dx = tx2 - tx2
    vx = dx/dt

    next_tx = tx2 + vx*end_time

    # Calculate position in FullHD
    new_bx, new_by = scale_to_full_hd(bx,by,width,height)
    new_tx, new_ty = scale_to_full_hd(next_tx,ty,width,height)

    run_adb("shell input swipe %d %d %d %d" % (new_bx, new_by, new_tx, new_ty))
    time.sleep(1.3)

sys.exit(1)


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
