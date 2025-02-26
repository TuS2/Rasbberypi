import tflite_runtime.interpreter as tflite
import numpy as np
import cv2

# Load the TFLite model
model_path = "model.tflite"
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Get model input details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load and preprocess the image
image_path = "5330489452029668396.jpg"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)  # Load in RGB mode

# Resize while maintaining aspect ratio
input_size = input_details[0]['shape'][1]  # Model input size
h, w, _ = image.shape
aspect_ratio = max(w, h) / input_size
new_w, new_h = int(w / aspect_ratio), int(h / aspect_ratio)
cropped_resized = cv2.resize(image, (new_w, new_h))

# Pad to square
padded = np.ones((input_size, input_size, 3), dtype=np.uint8) * 255  # White background
x_offset = (input_size - new_w) // 2
y_offset = (input_size - new_h) // 2
padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = cropped_resized

cv2.imshow('rfvetv', padded)

# Normalize and add batch dimension
image = padded.astype(np.float32) / 255.0
image = np.expand_dims(image, axis=0)

# Run inference
interpreter.set_tensor(input_details[0]['index'], image)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

# Print confidence scores
class_labels = ["Circle","Square", "Triangle"]  # Assumes these correspond to the first 3 indices
confidence_scores = output_data[0][:3]
print(f"Confidence scores: {confidence_scores}")

# Interpret the result
predicted_class = np.argmax(confidence_scores)  # Select from first 3 output classes

# Print only the shape name
print(class_labels[predicted_class])




