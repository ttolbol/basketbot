# Imports the monkeyrunner modules used by this program
import time
import os
import png
import numpy as np
from PIL import Image

lag = 1.1

adbpath = "/home/thomas/Android/Sdk/platform-tools/adb"

os.system(adbpath+" devices")
print "Connected!"

while True:
    startTime = time.time()
    os.system(adbpath+" shell screencap -p /mnt/sdcard/sc.png")
    startTime2 = time.time()
    os.system(adbpath+" shell screencap -p /mnt/sdcard/sc2.png")
    os.system(adbpath+" pull /mnt/sdcard/sc.png")
    os.system(adbpath+" pull /mnt/sdcard/sc2.png")
    #os.system(adbpath+" shell rm /mnt/sdcard/sc.png")
    im = Image.open("/home/thomas/Android/Sdk/sc.png")
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
    im = Image.open("/home/thomas/Android/Sdk/sc2.png")
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
