#!/usr/bin/env python2

# Imports the monkeyrunner modules used by this program
import sys
import time
import png
import numpy as np
import math
from PIL import Image
import autopy
from geometry import *
from util import *

# --- Constants ---

lag = 1.1

#adbpath = "/home/thomas/Android/Sdk/platform-tools/adb"
adbpath = "adb"

countdown_seconds = 0

sample_count = 2

time_until_next_shot = 0.5
time_until_next_screenshot = 0

# The streamed screens actual properties
screen_resolution = Point(1080, 1920)
screen_aspect_ratio = float(screen_resolution.y)/screen_resolution.x # 16.0/9

save_debug_images = False


# Init the screen to just 0's
# (A box has a topleft point and a bottom right point)
screen = Box(Point(0,0), Point(0,0))



# Locate the phone stream on the screen
def find_screen():
    # Find the borders of the casted screen by going from the left, right, top and bottom
    # until something interesting happens.

    # Make a countdown so the user can set stream viewer in fullscreen.

    if countdown_seconds:
        print "Fullscreen the viewer. Starting in %d seconds..." % countdown_seconds
    for i in xrange(countdown_seconds, 0, -1):
        print i
        time.sleep(1)
    print "Finding screen..."
    print

    # Take screenshot of the entire screen and analyse it
    pix = capture()

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

    screen_width = x - bottom_left_x
    screen_height = int(round(screen_width*screen_aspect_ratio))

    screen.topleft.x = bottom_left_x
    screen.topleft.y = bottom_left_y - screen_height
    screen.botright.x = bottom_left_x + screen_width
    screen.botright.y = bottom_left_y

    # If the found dimensions are weird (too small), we try again

    if screen.topleft.y < 0:
        print "Negative value for screen.topleft.y. Try again."
        find_screen()
        return

    if screen.width() < 200:
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

# Run ADB with some command
def run_adb(command):
    stdout, stderr, _, _, _ = run_process(adbpath + " " + command)
    return stdout + stderr



# Find location on screen based on percentage
def percent_height(p):
    _, height = screen.dim()
    return int(round(height*p))

def percent_width(p):
    width, _ = screen.dim()
    return int(round(width*p))

def percent_pos(x,y):
    return percent_width(x), percent_height(y)




# Find the ball on the screen
# Takes pixels, return the x,y position of the ball
def find_ball(pix):
    width, height = screen.dim()

    # Percentage position from top of ball
    p = 0.92875
    approx_y = percent_height(p)

    # We will only search inside this
    search_box = Box(Point(0,approx_y), Point(width, approx_y+1))

    if save_debug_images and False:
        pix_debug = capture(search_box + screen.topleft)
        pix_debug.save("images/ball-search.png")

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

    # Percentage position from top of target
    p = 0.3867403
    approx_y = int(round(height*p))

    # We will only search inside this
    search_box = Box(Point(0,approx_y-10), Point(width, approx_y+10))

    if save_debug_images and False:
        pix_debug = capture(search_box + screen.topleft)
        pix_debug.save("images/target-search.png")

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



def predict_target_pos(ball_pos, target_pos, prev_target_pos, now, last_time):
    # The ball is measured to travel the following percentage over the following time
    ball_speed = (407.0/height)/0.8

    # Calculate the distance percentage from ball to target
    dist_to_target = (target_pos - ball_pos).length()/height

    # The delay of the ball should then be
    ball_delay =  ball_speed * dist_to_target

    # The overall delay sums to ~1.5
    delay = ball_delay + 0.87

    delay = 1.5

    #print ball_pos, prev_ball_pos
    #print target_pos, prev_target_pos

    ty  = target_pos.y
    tx1 = prev_target_pos.x
    tx2 = target_pos.x

    dt = now - last_time
    dx = tx2 - tx1
    vx = dx/dt

    #print prev_target_pos.x, target_pos.x
    print "dx =", dx

    if abs(dx) > 5:
        vx = (440 * (dx/abs(dx))) * scaling_factor
    elif abs(dx) > 1:
        vx = (220 * (dx/abs(dx))) * scaling_factor
    else:
        vx = 0

    print "vx =", vx

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

    return Point(pred_target_x, target_pos.y)


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

print "Found screen:", screen
print

width, height = screen.dim()

can_shoot = False

scaling_factor = float(width)/screen_resolution.x

ball_pos   = None
target_pos = None

now = time.time()
last_shot_time = 0
last_screenshot_time = 0

counter = 0
no_progress_counter = 0



if save_debug_images:
    # Remove and recreate the images folder
    reset_image_folder()

    # Save an image of the screen for debugging
    pix_debug = capture_screen()
    pix_debug.save("images/screen.png")


# Main event loop
while True:
    # FPS limit on screenshots taken
    if time.time() - last_screenshot_time < time_until_next_screenshot:
        continue

    # Update values between iterations
    last_time = now
    now       = time.time()

    prev_ball_pos   = ball_pos
    prev_target_pos = target_pos

    # Take screenshot of part of the screen where the stream is
    # After this point, the coordinates for pix is relative to the stream.
    pix = capture_screen()
    last_screenshot_time = time.time()

    if save_debug_images:
        # Save each screenshot to file
        pix.save("images/test%09d.png" % counter)
        counter += 1

    # Try to find the ball and the target
    ball_pos, target_pos = get_ball_target(pix)

    if not ball_pos:
        no_progress_counter += 1
        if no_progress_counter > 40:
            print "Ball was not found."
            no_progress_counter = 0
        continue

    if not target_pos:
        no_progress_counter += 1
        if no_progress_counter > 40:
            print "Target was not found."
            no_progress_counter = 0
        continue
    
    no_progress_counter = 0

    if not prev_ball_pos or not prev_target_pos:
        # Skip the first iteration to get us going
        continue

    if now - last_shot_time > time_until_next_shot:
        can_shoot = True

    if not can_shoot:
        continue

    # Do prediction
    pred_target = predict_target_pos(ball_pos, target_pos, prev_target_pos, now, last_time)

    # Calculate position in FullHD
    new_bx, new_by = scale_to_full_hd(ball_pos.x, ball_pos.y)
    new_tx, new_ty = scale_to_full_hd(pred_target.x, pred_target.y)

    print "Shoot!"

    run_adb("shell input swipe %d %d %d %d" % (new_bx, new_by, new_tx, new_ty))

    can_shoot = False
    last_shot_time = time.time()

    print # Just a newline
