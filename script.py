#!/usr/bin/env python2

# Imports the monkeyrunner modules used by this program
import sys
import time
import os
import shutil
import png
import numpy as np
import math
from PIL import Image
import subprocess
from geometry import *
import autopy

# Constants
lag = 1.1

#adbpath = "/home/thomas/Android/Sdk/platform-tools/adb"
adbpath = "adb"

countdown_seconds = 0

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
    dist = rdif*rdif+gdif*gdif+bdif*bdif
    dist = math.sqrt(dist)
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

    ratio = 16.0/9
    padding = 40

    # Find bottom left corner of the screen
    y = pix.height - padding
    found = False
    while not found:
        for x in xrange(padding, pix.width/2-padding):
            r, g, b = get_pixel(pix, x, y)
            if r > 20:
                found = True
                break
        y -= 1

    bottom_left_x = x
    bottom_left_y = y

    for x in xrange(x, pix.width/2-padding):
        r, g, b = get_pixel(pix, x, y)
        if r < 20:
            break

    screen_width = x- bottom_left_x
    screen_height = int(round(screen_width*ratio))

    screen.topleft.x = bottom_left_x
    screen.topleft.y = bottom_left_y - screen_height
    screen.botright.x = bottom_left_x + screen_width
    screen.botright.y = bottom_left_y

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
        tuple_in_tuple = (box.topleft.to_tuple(), box.dim())
        pix = autopy.bitmap.capture_screen(tuple_in_tuple)
    else:
        pix = autopy.bitmap.capture_screen()
    return pix

# Use the found screen to only capture that part of the screen
def capture_screen():
    return capture(screen)

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

    p = 1764.0/1920
    approx_y = screen.topleft.y + int(round(height*p))

    # We will only search inside this
    search_box = Box(Point(0,approx_y), Point(width, approx_y+1))

    # The average of all the points that we are looking for.
    centroid = Point(0,0)
    n = 0

    # Go through all pixels and search for a specific color.
    # If the color is found, make it part of the centroid.
    for x in range(search_box.topleft.x, search_box.botright.x):
        for y in range(search_box.topleft.y, search_box.botright.y):
            r, g, b = get_pixel(pix, x, y)

            if np.average((r,g,b)) < 200:
                new_p = Point(x,y)
                centroid += new_p
                n += 1

    # Finally, take the average or report an error and stop.
    if n > 100:
        centroid /= n
    else:
        return

    return centroid

# Find the target on the screen
# Takes pixels, return the x,y position of the target
def find_target(pix):
    width, height = screen.dim()

    target_color = (255, 39, 18)

    p = 734.0/1920
    approx_y = screen.topleft.y + int(round(height*p))

    # We will only search inside this
    search_box = Box(Point(0,approx_y-20), Point(width, approx_y))

    # The average of all the points that we are looking for.
    centroid = Point(0,0)
    n = 0

    for x in xrange(search_box.topleft.x, search_box.botright.x):
        for y in xrange(search_box.topleft.y, search_box.botright.y):
            r, g, b = get_pixel(pix, x, y)
            if color_distance((r,g,b), target_color) < 10:
                new_p = Point(x,y)
                centroid += new_p
                n += 1

    # Finally, take the average or report an error and stop.
    if n > 0:
        centroid /= n
    else:
        return

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

        if not ball_pos:
            return

        if not target_pos:
            return

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

can_shoot = False

scaling_factor = width/1080.0

ball_pos   = None
target_pos = None

now = time.time()
last_shot = 0

counter = 0

shutil.rmtree('images')
# Create image directory
if not os.path.exists("images"):
    os.makedirs("images")

# Tried my luck with a simplified event loop that uses the helper functions above
while True:
    #print "(Gathering information for shot.)"

    # Update values between iterations
    last_time = now
    now       = time.time()

    prev_ball_pos   = ball_pos
    prev_target_pos = target_pos

    pix = capture_screen()

    # Save each screenshot to file
    pix.save("images/test%09d.png" % counter)
    counter += 1

    ball_pos, target_pos = get_ball_target(pix)

    if not ball_pos:
        #print "Ball was not found."
        continue

    if not target_pos:
        #print "Target was not found."
        continue

    if not prev_ball_pos or not prev_target_pos:
        # Skip the first iteration to get us going
        continue

    if now - last_shot > 0.0:
        can_shoot = True

    if not can_shoot:
        continue

    # --- Do prediction ---

    #print ball_pos, prev_ball_pos
    #print target_pos, prev_target_pos

    delay = 1.5

    bx  = ball_pos.x
    by  = ball_pos.y

    ty  = target_pos.y
    tx1 = prev_target_pos.x
    tx2 = target_pos.x

    dt = now - last_time
    dx = tx2 - tx1
    vx = dx/dt

    #print prev_target_pos.x, target_pos.x
    #print dx

    if abs(dx) > 1:
        vx = (220 * (dx/abs(dx))) * scaling_factor
    else:
        vx = 0

    scaled_vx = (1/scaling_factor) * vx

    #print "vx = ", vx
    #print "scaled vx = ", scaled_vx

    pred_target_x = target_pos.x + vx*delay

    basket_width = scaling_factor * 280
    bw2 = basket_width / 2 

    print basket_width

    if pred_target_x+bw2 > width:
        print "To right"
        pred_target_x = (width - bw2) - (pred_target_x - (width-bw2))

    if pred_target_x-bw2 < 0:
        print "To left"
        pred_target_x = bw2-(pred_target_x - bw2)


    while tx2 > 940 or tx2 < 140:
        if tx2 > 940:
            tx2 = 940-(tx2-940)

        if tx2 < 140:
            tx2 = 140-(tx2-140)
    # Calculate position in FullHD
    new_bx, new_by = scale_to_full_hd(bx,by)
    new_tx, new_ty = scale_to_full_hd(pred_target_x,ty)

    print "Shoot!"

    run_adb("shell input swipe %d %d %d %d" % (new_bx, new_by, new_tx, new_ty))

    #time.sleep(time_until_next_shot)
    can_shoot = False
    last_shot = time.time()

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
