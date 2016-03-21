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


def find_screen():
    # Find the borders of the casted screen by going from the left, right, top and bottom
    # until something interesting happens.
    pass


def capture(x1=None, y1=None, x2=None, y2=None):
    if x1 and y1 and x2 and y2:
        box = (x1, y1, x2, y2)
    else:
        box = None
    grab = pyscreenshot.grab(bbox=box)
    return grab


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

print run_adb("devices")
print "Connected!"

while True:
    startTime = time.time()
    os.system(adbpath+" shell screencap -p /mnt/sdcard/sc.png")
    startTime2 = time.time()
    os.system(adbpath+" shell screencap -p /mnt/sdcard/sc2.png")
    os.system(adbpath+" pull /mnt/sdcard/sc.png")
    os.system(adbpath+" pull /mnt/sdcard/sc2.png")
    #os.system(adbpath+" shell rm /mnt/sdcard/sc.png")
    im = Image.open("sc.png")
    pix = im.load()

    #find ball
    bx = 0
    n = 0
    for i in range(1080):
        if np.average(pix[i,1764]) < 200:
            bx += i
            n += 1
    if n > 0:
        bx = bx/n

    #find targets prev. position
    tx1 = 0
    n = 0
    for i in range(1080):
        if np.average(pix[i,734]) < 200:
            tx1 += i
            n += 1
    if n > 0:
        tx1 = tx1/n

    #os.system(adbpath+" shell rm /mnt/sdcard/sc.png")
    im = Image.open("sc2.png")
    pix = im.load()

    #find targets new position
    tx2 = 0
    n = 0
    for i in range(1080):
        if np.average(pix[i,734]) < 200:
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

    os.system(adbpath+" shell input swipe "+str(bx)+" 1764 "+str(tx2)+" 734")
    time.sleep(1.3)
