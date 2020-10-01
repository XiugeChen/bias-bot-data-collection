import tobii_research as tr
import time

######## Constants ########

EYE_TRACKER = None

######## Functions ########

def print_eyetracker(eyetracker):
    if eyetracker is None:
        return

    "print information about this eye tracker"
    print("Find eye tracker: ")
    print("Address: " + eyetracker.address)
    print("Model: " + eyetracker.model)
    print("Name (It's OK if this is empty): " + eyetracker.device_name)
    print("Serial number: " + eyetracker.serial_number)

def cali_eyetracker(eyetracker):
    "calibrate this eye tacker"
    if eyetracker is None:
        return

    return

def gaze_data_callback(gaze_data):
    "call back function to get gaze data from subscribed eye tacker"
    print("Left eye: ({gaze_left_eye}) \t Right eye: ({gaze_right_eye})".format(
        gaze_left_eye=gaze_data['left_gaze_point_on_display_area'],
        gaze_right_eye=gaze_data['right_gaze_point_on_display_area']))

######## Main ########

def register_eyetracker():
    stdin = raw_input("Start tobii eye tracking? [y/n]")

    while (stdin != "n"):
        found_eyetrackers = tr.find_all_eyetrackers()

        if len(found_eyetrackers) > 0:
            EYE_TRACKER = found_eyetrackers[0]
            break
        else:
            stdin = raw_input("Can't find eye trackers, try it again? [y/n]")

    if EYE_TRACKER != None:
        print_eyetracker(EYE_TRACKER)
        cali_eyetracker(EYE_TRACKER)
        EYE_TRACKER.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

if __name__ == '__main__':
    try:
        register_eyetracker()

        while(True):
            continue

    except KeyboardInterrupt:
        print("Key board interrupt, terminate program")

        if EYE_TRACKER != None:
            EYE_TRACKER.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)