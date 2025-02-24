import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2, Preview
import time
# picamera setting
picam2 = Picamera2()

camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

# take photo
picam2.start()
time.sleep(1)
picam2.capture_file("test_photo.jpg")

# load model
interpreter = tflite.Interpreter(model_path="model.tflite")
print("TensorFlow Lite успешно загружен!")




