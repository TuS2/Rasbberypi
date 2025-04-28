import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
from picamera2 import Picamera2, Preview
from math import atan, degrees

# === НАСТРОЙКИ === #
BOARD_WIDTH_CM = 60   # ширина доски в см
BOARD_HEIGHT_CM = 40  # высота доски в см
STEP_ANGLE = 0.32727  # угол за один шаг (с ременной передачей)
STEP_DELAY = 0.001
MIN_CONTOUR_AREA = 500
FILTER_SHAPE = "Circle"

# Пины ультразвукового датчика
TRIG = 4
ECHO = 17

# Пины моторов
DIR_X = 21
STEP_X = 20
DIR_Y = 7
STEP_Y = 1

# Ограничения по углам моторов
MAX_X_ANGLE = 45
MAX_Y_ANGLE = 45

# === НАСТРОЙКА GPIO === #
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(DIR_X, GPIO.OUT)
GPIO.setup(STEP_X, GPIO.OUT)
GPIO.setup(DIR_Y, GPIO.OUT)
GPIO.setup(STEP_Y, GPIO.OUT)

# === УЛЬТРАЗВУК === #
def measure_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time() + 1
    while GPIO.input(ECHO) == 0:
        start = time.time()
        if time.time() > timeout:
            print("Timeout (start)")
            return None

    timeout = time.time() + 1
    while GPIO.input(ECHO) == 1:
        stop = time.time()
        if time.time() > timeout:
            print("Timeout (stop)")
            return None

    elapsed = stop - start
    distance = (elapsed * 34300) / 2
    return distance

# === ВЫРЕЗАТЬ ДОСКУ === #
def extract_board(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    board_contour = None
    max_area = 0

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            if area > max_area:
                max_area = area
                board_contour = approx

    if board_contour is None:
        print("📛 Доска не найдена.")
        return image

    pts = board_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    width, height = 640, 480
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, matrix, (width, height))
    return warped

# === МОТОРЫ === #
def rotate_motor(degree_x, degree_y):
    degree_x = max(-MAX_X_ANGLE, min(MAX_X_ANGLE, degree_x))
    degree_y = max(0, min(MAX_Y_ANGLE, degree_y))  # Только вверх!

    steps_x = round(abs(degree_x) / STEP_ANGLE)
    steps_y = round(abs(degree_y) / STEP_ANGLE)

    if steps_x == 0 and steps_y == 0:
        print("⚠️ Шагов слишком мало, пропускаем поворот")
        return (0, 0)

    print(f"   🔁 Шагов X: {steps_x}, Y: {steps_y}")

    # Устанавливаем направления
    GPIO.output(DIR_X, GPIO.HIGH if degree_x > 0 else GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH if degree_y > 0 else GPIO.LOW)

    # Двигаем по X
    for _ in range(steps_x):
        GPIO.output(STEP_X, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(STEP_X, GPIO.LOW)
        time.sleep(STEP_DELAY)

    # Двигаем по Y
    for _ in range(steps_y):
        GPIO.output(STEP_Y, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(STEP_Y, GPIO.LOW)
        time.sleep(STEP_DELAY)




# === ОПРЕДЕЛЕНИЕ ФИГУР === #
def detect_shape(contour):
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    sides = len(approx)
    if sides == 3:
        return "Triangle"
    elif sides == 4:
        return "Square"
    elif sides > 4:
        return "Circle"
    return "Unknown"

# === ГЛАВНАЯ ЛОГИКА === #
try:
    distance = 300 #measure_distance()
    if distance:
        print(f"\n📏 Расстояние до доски: {distance:.2f} см")
    else:
        raise Exception("Не удалось измерить расстояние")

    # picam2 = Picamera2()
    # config = picam2.create_still_configuration(lores={"size": (640, 480)}, display="lores")
    # picam2.configure(config)
    # picam2.start_preview(Preview.QTGL)
    # picam2.start()
    # time.sleep(2)
    # picam2.capture_file("capture.jpg")
    # print("📷 Фото сделано")

    image = cv2.imread("desk3.jpg")
    cropped = image
    height, width = cropped.shape[:2]

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]

    print(f"🔍 Найдено фигур: {len(valid_contours)}")

    for i, contour in enumerate(valid_contours, 1):
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2
        shape = detect_shape(contour)

        if shape != FILTER_SHAPE:
            continue

        print(f"\n[{i}] {shape} в пикселях: ({center_x}, {center_y})")

        dx_pixels = center_x - (width / 2)
        dy_pixels = height - center_y

        dx_cm = dx_pixels * (BOARD_WIDTH_CM / width)
        dy_cm = dy_pixels * (BOARD_HEIGHT_CM / height)

        angle_x = degrees(atan(dx_cm / distance))
        angle_y = degrees(atan(dy_cm / distance))

        print(f" ➔ Поворот X: {angle_x:.2f}°, Y: {angle_y:.2f}°")

        steps_x, steps_y = rotate_motor(angle_x, angle_y)
        time.sleep(2)

        # Возврат
        print(" ↩️ Возврат к центру")

        GPIO.output(DIR_X, GPIO.LOW if angle_x > 0 else GPIO.HIGH)
        GPIO.output(DIR_Y, GPIO.LOW if angle_y > 0 else GPIO.HIGH)

        for _ in range(max(steps_x, steps_y)):
            if _ < steps_x:
                GPIO.output(STEP_X, GPIO.HIGH)
                time.sleep(STEP_DELAY)
                GPIO.output(STEP_X, GPIO.LOW)
                time.sleep(STEP_DELAY)
            if _ < steps_y:
                GPIO.output(STEP_Y, GPIO.HIGH)
                time.sleep(STEP_DELAY)
                GPIO.output(STEP_Y, GPIO.LOW)
                time.sleep(STEP_DELAY)

finally:
    GPIO.output(DIR_X, GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH)
    GPIO.output(STEP_X, GPIO.LOW)
    GPIO.output(STEP_Y, GPIO.HIGH)
    print("\n✅ Работа завершена, GPIO очищены")
