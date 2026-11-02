import subprocess
import cv2
import numpy as np

DEVICE = "emulator-5554"

def get_screen():
    result = subprocess.run(
        ["adb", "-s", DEVICE,
         "exec-out", "screencap", "-p"],
        capture_output=True,
        check=True
    )

    image = cv2.imdecode(
        np.frombuffer(result.stdout, np.uint8),
        cv2.IMREAD_COLOR
    )

    return image

screen = get_screen()

if screen is not None:
    cv2.imshow("Thunder Agent", screen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()