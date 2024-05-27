import numpy as np

def greedy_policy(Qtable, state):
    action = np.argmax(Qtable[tuple(state)])
    return action

def get_sensor_values(distances, cam_check=None):
    k1 = 2
    k2 = 2
    k3 = 3
    k4 = 3
    k5 = 1
    k6 = 1

    # check the left side sensor
    dist = min(distances[0:3])
    if (dist > 40 and dist < 70):
        k1 = 1  #zone 1
    elif (dist <= 40):
        k1 = 0  #zone 0

    # check the right side sensor
    dist = min(distances[2:])
    if (dist > 40 and dist < 70):
        k2 = 1  #zone 1
    elif (dist <= 40):
        k2 = 0  #zone 0

    detected = [distance < 100 for distance in distances]
    # the left sector of the vehicle
    if detected[0] and detected[2]:
        k3 = 0 # both subsectors have obstacles
    elif (detected[1] or detected[2]) and not detected[0]:
        k3 = 1 # inner left subsector
    elif (detected[0] or detected[1]) and not detected[2]:
        k3 = 2 # outter left subsector

    # the right sector of the vehicle
    if detected[2] and detected[4]:
        k4 = 0 # both subsectors have obstacles
    elif (detected[2] or detected[3]) and not detected[4]:
        k4 = 1 # inner right subsector
    elif (detected[3] or detected[4]) and not detected[2]:
        k4 = 2 # outter right subsector 

    if "tracking-both" in cam_check:
        k5, k6 = 0, 0
    elif "tracking-right" in cam_check:
        k6 = 0
    elif "tracking-left" in cam_check:
        k5 = 0      

    return [k1, k2, k3, k4, k5, k6]
