import cv2
import numpy as np

# Load the image
image_path = "5330489452029668396.jpg"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Gaussian blur to remove noise
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Use Canny edge detection
edges = cv2.Canny(blurred, 50, 150)

# Find contours
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not contours:
    raise ValueError("No shape detected in the image")

# Find the largest contour with significant area
largest_contour = max(contours, key=cv2.contourArea)
if cv2.contourArea(largest_contour) < 1000:
    raise ValueError("No sufficiently large shape detected")

# Get bounding box and crop the shape tightly
x, y, w, h = cv2.boundingRect(largest_contour)
cropped_shape = image[y:y+h, x:x+w]

# Create a mask for the extracted shape
shape_mask = np.zeros((h, w), dtype=np.uint8)
cv2.drawContours(shape_mask, [largest_contour - [x, y]], -1, 255, thickness=cv2.FILLED)

# Apply mask to get a clean cutout
cutout = cv2.bitwise_and(cropped_shape, cropped_shape, mask=shape_mask)

# Save the improved cutout
cv2.imwrite("clean_cut.png", cutout)

print("Shape extracted and saved as 'clean_cut.png'")