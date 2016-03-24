import math
import time
import subprocess
import shutil
import os

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


def reset_image_folder():
    shutil.rmtree('images')
    if not os.path.exists("images"):
        os.makedirs("images")




# Similar to the map function in Processing
def map_range(value, low1, high1, low2, high2):
    return low2 + (high2 - low2) * (value - low1) / (high1 - low1)



def color_distance(c1, c2):
    rdif = abs(c1[0]-c2[0])
    gdif = abs(c1[1]-c2[1])
    bdif = abs(c1[2]-c2[2])
    dist = rdif*rdif+gdif*gdif+bdif*bdif
    dist = math.sqrt(dist)
    return dist
