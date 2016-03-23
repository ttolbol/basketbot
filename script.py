#!/usr/bin/env python2

# Imports the monkeyrunner modules used by this program
import sys
import time
import os
import png
import numpy as np
import math
from PIL import Image
import subprocess
from geometry import *
import autopy

# Constants
lag = 1.1

adbpath = "/home/thomas/Android/Sdk/platform-tools/adb"

countdown_seconds = 3

sample_count = 2

time_until_next_shot = 1.3

# Init the screen to just 0's
# (A box has a topleft point and a bottom right point)
screen = Box(Point(0,0), Point(0,0))

# A snapshot of the current scene
# It has a ball point, a target point and a timestamp since we started the current sampling
class Snapshot:
    def __init__(self, ball_pos, target_pos, timestamp):
        self.ball_pos = ball_pos
        self.target_pos = target_pos
        self.timestamp = timestamp

    def __str__(self):
        return "%s, %s, %s" % (self.ball_pos, self.target_pos, self.timestamp)

    def __repr__(self):
        return str(self)

def color_distance(c1, c2):
    rdif = abs(c1[0]-c2[0])
    gdif = abs(c1[1]-c2[1])
    bdif = abs(c1[2]-c2[2])
    dist = rdif+gdif+bdif
    dist = dist/3.0
    return dist


# Locate the phone stream on the screen
def find_screen():
    # Find the borders of the casted screen by going from the left, right, top and bottom
    # until something interesting happens.

    # Make a countdown so the user can set stream viewer in fullscreen.

    print "Fullscreen the viewer. Starting in %d seconds..." % countdown_seconds
    for i in xrange(countdown_seconds, 0, -1):
        print i
        time.sleep(1)
    print "Finding screen..."
    print

    # Take screen shot of the entire screen and analyse it
    pix = capture()

    # Find left border
    # This scan starts from the y-mid of the screen and goes from x = 0 to max.
    for x in xrange(10, pix.width):
        r, g, b = get_pixel(pix, x, pix.height/2)
        s = sum([r,g,b])
        if s >= 243:
            screen.topleft.x = x
            break

    # Find right border
    # This scan starts from the y-mid of the screen and goes from x = max to 0.
    for x in xrange(pix.width-10, 0, -1):
        r, g, b = get_pixel(pix, x,pix.height/2)
        s = sum([r,g,b])
        if s >= 243:
            screen.botright.x = x
            break

    # Find top border
    # This scan starts from the x-quarter of the screen and goes from y = 0 to max.
    for y in xrange(20, pix.height):
        r, g, b = get_pixel(pix, pix.width/4, y)
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen.topleft.y = y
            break

    # Find bottom border
    # This scan starts from the x-quarter of the screen and goes from y = max to 0.
    for y in xrange(pix.height-20, 0, -1):
        r, g, b = get_pixel(pix, pix.width/4,y)
        s = sum([r,g,b])
        if s >= 730: # We found the white screen
            screen.botright.y = y
            break

    # If the found dimensions are weird (too small), we try again

    if screen.width() < 50:
        print "Very small width of screen. Try again."
        find_screen()
        return

    if screen.height() < 50:
        print "Very small height of screen. Try again."
        find_screen()
        return

def get_pixel(pix, x, y):
    return autopy.color.hex_to_rgb(pix.get_color(x,y))

# Take a screenshot of Box of the screen or if not specified, the entire screen.
def capture(box=None):
    if box:
        tuple_in_tuple = (box[:2], box[2:])
        print tuple_in_tuple
        pix = autopy.bitmap.capture_screen(tuple_in_tuple)
    else:
        pix = autopy.bitmap.capture_screen()
    return pix

# Use the found screen to only capture that part of the screen
def capture_screen():
    return capture(screen.to_tuple())

# Execute a shell command
def run_process(cmd, timeout = 60):
    start_time = time.clock()

    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

    stdout_output = ""
    stderr_output = ""

    did_timeout = False

    # Keep asking if the process has ended
    # and every time, store the new stdout and stderr output to strings.
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

# Run ADB with some command
def run_adb(command):
    stdout, stderr, _, _, _ = run_process(adbpath + " " + command)
    return stdout + stderr


# Find the ball on the screen
# Takes pixels, return the x,y position of the ball
def find_ball(pix):
    width, height = screen.dim()

    # We will only search inside this
    search_box = Box(Point(0,0), Point(width, height))

    # The average of all the points that we are looking for.
    centroid = Point(0,0)
    n = 0

    # Go through all pixels and search for a specific color.
    # If the color is found, make it part of the centroid.
    for x in range(search_box.topleft.x, search_box.botright.x):
        for y in range(search_box.topleft.y, search_box.botright.y):
            r, g, b = get_pixel(pix, x, y)

            if r == 255 and g == 150 and b == 48:
                new_p = Point(x,y)
                centroid += new_p
                n += 1

    # Finally, take the average or report an error and stop.
    if n > 0:
        centroid /= n
    else:
        print "Ball was not found."
        sys.exit(1)

    return centroid

# Find the target on the screen
# Takes pixels, return the x,y position of the target
def find_target(pix):
    width, height = screen.dim()

    # We will only search inside this
    search_box = Box(Point(0,0), Point(width, height))

    # The average of all the points that we are looking for.
    centroid = Point(0,0)
    n = 0

    # Go through all pixels and search for a specific color.
    # If the color is found, make it part of the centroid.
    for x in range(search_box.topleft.x, search_box.botright.x):
        for y in range(search_box.topleft.y, search_box.botright.y):
            r, g, b = get_pixel(pix, x, y)

            if r == 255 and g == 38 and b == 18:
                new_p = Point(x,y)
                centroid += new_p
                n += 1

    # Finally, take the average or report an error and stop.
    if n > 0:
        centroid /= n
    else:
        print "Target was not found."
        sys.exit(1)

    return centroid

# Combine the result of the find_ball and find_target
def get_ball_target(pix):
    return (find_ball(pix), find_target(pix))

# Take snapshots of the scene and return a list of them
def sample_ball_target(samples=sample_count, delay=0):
    l = []

    start_time = time.time()

    for i in range(samples):
        screen_time = time.time()
        pix = capture_screen()

        ball_pos, target_pos = get_ball_target(pix)

        snapshot = Snapshot(ball_pos, target_pos, screen_time - start_time)
        print "Snapshot %d: %s" % (i+1, snapshot)

        l.append(snapshot)

        if delay:
            time.sleep(delay)

    return l


# Similar to the map function in Processing
def map_range(value, low1, high1, low2, high2):
    return low2 + (high2 - low2) * (value - low1) / (high1 - low1)

# Use the map_range to scale coordinates to FullHD
def scale_to_full_hd(x, y, small_width=None, small_height=None, big_width=1080, big_height=1920):
    if small_width is None:
        small_width = screen.width()
    if small_height is None:
        small_height = screen.height()
    return map_range(x, 0, small_width, 0, big_width), map_range(y, 0, small_height, 0, big_height)




###################
#   Starts here   #
###################

print color_distance(c1, c2)

devices = run_adb("devices")
print devices

# Determine if a device is connected.
# Stop in none.
tmp_split_devices = devices.split("\n")
if len(tmp_split_devices) > 1 and sum(["device" in s for s in tmp_split_devices[1:]]) > 0:
    print "Connected!"
    print
else:
    print "No device. Aborting."
    sys.exit(1)

# Find the streamed screen by scanning for bight color from each of the for sides.
# If this doesn't work, simply comment this out and hardcode the approximate location.
find_screen()

width, height = screen.dim()

# Tried my luck with a simplified event loop that uses the helper functions above
while True:
    print "Gathering information for shot."
    start_time = time.time()

    # Take some snapshots of the scene
    samples = sample_ball_target()

    end_time = time.time()

    # Extract values
    sample1 = samples[0]
    sample2 = samples[1]

    bx  = sample1.ball_pos.x
    by  = sample1.ball_pos.y

    ty  = sample1.target_pos.y
    tx1 = sample1.target_pos.x
    tx2 = sample2.target_pos.x

    dt = sample2.timestamp - sample1.timestamp
    dx = tx2 - tx1
    vx = dx/dt

    #ball_speed = ...

    print "dt = ", dt, ", dx = ", dx, ", vx = ", vx

    # TODO: Do proper prediction here
    next_tx = tx2 + vx*dt

    print "tx1 = ", tx1, ", tx2 = ", tx2, ", next_tx = ", next_tx


    # Calculate position in FullHD
    new_bx, new_by = scale_to_full_hd(bx,by)
    new_tx, new_ty = scale_to_full_hd(next_tx,ty)

    print "Shoot!"

    run_adb("shell input swipe %d %d %d %d" % (new_bx, new_by, new_tx, new_ty))

    time.sleep(time_until_next_shot)

    print # Just a newline

# Stop here, so we can't enter the loop below.
sys.exit(1)


# Old event loop
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
