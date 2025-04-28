import time
import cv2
import numpy as np
from picamera2 import Picamera2, Preview

picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)},
                                                  display="lores")
picam2.configure(camera_config)
picam2.start()
time.sleep(2)
picam2.capture_file("capture.jpg")
print("📷 Фото сделано")