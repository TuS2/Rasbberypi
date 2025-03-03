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
image_path = "circle_1.jpg"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Convert to grayscale and apply adaptive threshold
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV, 11, 1)
# thresh = cv2.inRange(image, (180, 0, 0), (0, 0, 180))

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if len(contours) == 0:
    raise ValueError("No shape detected in the image")

# Find the largest contour (assumed to be the main shape)
largest_contour = max(contours, key=cv2.contourArea)

# Create a mask to extract the shape
mask = np.zeros_like(gray)
cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

# Convert mask to 3 channels
mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

# Apply mask to extract the shape
extracted = cv2.bitwise_and(image, mask_colored)

# Get bounding box and crop the shape
x, y, w, h = cv2.boundingRect(largest_contour)
cropped_shape = extracted[y:y+h, x:x+w]

# Save the extracted shape
cv2.imwrite("cut.png", cropped_shape)

# Resize while maintaining aspect ratio
input_size = input_details[0]['shape'][1]
aspect_ratio = max(w, h) / input_size
new_w, new_h = int(w / aspect_ratio), int(h / aspect_ratio)
cropped_resized = cv2.resize(cropped_shape, (new_w, new_h))

# Pad to square
padded = np.ones((input_size, input_size, 3), dtype=np.uint8) * 255
x_offset = (input_size - new_w) // 2
y_offset = (input_size - new_h) // 2
padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = cropped_resized

# Normalize and add batch dimension
image_input = padded.astype(np.float32) / 255.0
image_input = np.expand_dims(image_input, axis=0)

# Run inference
interpreter.set_tensor(input_details[0]['index'], image_input)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

# Interpret the result
class_labels = ["Circle", "Square", "Triangle"]
confidence_scores = output_data[0][:3]
predicted_class = np.argmax(confidence_scores)

# Print results
print(f"Confidence scores: {confidence_scores}")
print(class_labels[predicted_class])
