# basketbot

A bot to beat the mindless basketball game in Facebook messenger


# Dependencies

Make sure ADB is installed (can be installed from the Android SDK). 

Can sometimes also be installed by `android-tools-adb`.

Also install Python packages:

```
sudo pip install -r requirements.txt
```

Finally, find a way to stream the screen of the phone to your desktop.
It must be possible to maximize/fullscreen the viewer such that there
are black borders around the screen.

One way to do this is to use AllCast and the app Mirror.
See: http://www.guidingtech.com/36734/mirror-android-display-pc-tv/


# Use

1. Change the variable "adbpath" to your own path to ADB. 
2. Connect your device, start the streaming on phone and pc
3. Open the basketball game. 
4. Run script.py and before the countdown, switch to the stream in fullscreen


