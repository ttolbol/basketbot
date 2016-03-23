import autopy
pix = autopy.bitmap.capture_screen()
print autopy.color.hex_to_rgb(pix.get_color(400,400))
