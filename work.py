import tflite_runtime.interpreter as tflite
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import time

# Load image`
image_path = "2shapes.png"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Gaussian blur
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Use Canny edge detection
edges = cv2.Canny(blurred, 50, 150)

# Find contours
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not contours:
    raise ValueError("No shape detected in the image")

# Find the largest contour with significant area
largest_contour = max(contours, key=cv2.contourArea)
if cv2.contourArea(largest_contour) < 500:
    raise ValueError("No sufficiently large shape detected")

# Get bounding box
x, y, w, h = cv2.boundingRect(largest_contour)

# Compute the center of the detected shape
center_x = x + w // 2
center_y = y + h // 2

# Define reference points
origin = (0, 0)  # Top-left corner of the image
center = (center_x, center_y)  # Center of the detected shape

# Draw points on the image for visualization
cv2.circle(image, origin, 5, (0, 0, 255), -1)  # Red dot at (0,0)
image = cv2.circle(image, center, 5, (0, 0, 0), -1)  # Blue dot at center of the shape

# Save and display image with marked points
cv2.imwrite("output_with_points.jpg", image)
print(f"Reference points: Origin {origin}, Center {center}")

# Continue with the existing TFLite model processing

# Load the TFLite model
model_path = "model.tflite"
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Get model input details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load and preprocess the image
image_path = "clean_cut.png"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Convert to HSV color space
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define color ranges for red, green, and blue
color_ranges = {
    "red": [(0, 100, 100), (10, 255, 255), (160, 100, 100), (180, 255, 255)],
    "green": [(40, 40, 40), (90, 255, 255)],
    "blue": [(90, 50, 50), (140, 255, 255)]
}

# Create mask for color segmentation
mask = np.zeros_like(hsv[:, :, 0])
for color, ranges in color_ranges.items():
    for i in range(0, len(ranges), 2):
        lower, upper = ranges[i], ranges[i + 1]
        mask |= cv2.inRange(hsv, np.array(lower), np.array(upper))

# Find contours
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if len(contours) == 0:
    raise ValueError("No shape detected in the image")

# Find the largest contour
contours = sorted(contours, key=cv2.contourArea, reverse=True)
largest_contour = None
for contour in contours:
    if cv2.contourArea(contour) > 500:  # Filter out small noise
        largest_contour = contour
        break

if largest_contour is None:
    raise ValueError("No valid shape detected")

# Create a mask to extract the shape
shape_mask = np.zeros_like(mask)
cv2.drawContours(shape_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

# Apply mask to extract the shape
extracted = cv2.bitwise_and(image, image, mask=shape_mask)

# Get bounding box and crop the shape
x, y, w, h = cv2.boundingRect(largest_contour)
cropped_shape = extracted[y:y + h, x:x + w]

# Add alpha channel for transparency
b, g, r = cv2.split(cropped_shape)
alpha = shape_mask[y:y + h, x:x + w]
cutout = cv2.merge([b, g, r, alpha])

# Save the extracted shape with transparency
cv2.imwrite("cut.png", cutout)

# Resize while maintaining aspect ratio
input_size = input_details[0]['shape'][1]
aspect_ratio = max(w, h) / input_size
new_w, new_h = int(w / aspect_ratio), int(h / aspect_ratio)
cropped_resized = cv2.resize(cropped_shape, (new_w, new_h))

# Pad to square
padded = np.ones((input_size, input_size, 3), dtype=np.uint8) * 255
x_offset = (input_size - new_w) // 2
y_offset = (input_size - new_h) // 2
padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = cropped_resized

# Normalize and add batch dimension
image_input = padded.astype(np.float32) / 255.0
image_input = np.expand_dims(image_input, axis=0)

# Run inference
interpreter.set_tensor(input_details[0]['index'], image_input)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

# Interpret the result
class_labels = ["Circle", "Square"]
confidence_scores = output_data[0][:3]
predicted_class = np.argmax(confidence_scores)

# Print results
print(f"Confidence scores: {confidence_scores}")
print(class_labels[predicted_class])
