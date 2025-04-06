import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
from picamera2 import Picamera2, Preview

# === НАСТРОЙКИ === #
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
FOV_DEGREES = 90
STEP_ANGLE = 0.1607  # градуса на шаг
STEP_DELAY = 0.001   # задержка между шагами (можно уменьшить для скорости)
MIN_CONTOUR_AREA = 500
FILTER_SHAPE = "Circle"  # только этот тип фигур будем обрабатывать

# Пины ультразвукового датчика
TRIG = 4
ECHO = 17

# Пины моторов
DIR_X = 21
STEP_X = 20
DIR_Y = 7
STEP_Y = 1

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
        if start > timeout:
            return None

    timeout = time.time() + 0.02
    while GPIO.input(ECHO) == 1:
        stop = time.time()
        if stop > timeout:
            return None

    elapsed = stop - start
    return (elapsed * 34300) / 2

# === МОТОРЫ === #
def rotate_motor(degree_x, degree_y):
    steps_x = int(abs(degree_x) / STEP_ANGLE)
    steps_y = int(abs(degree_y) / STEP_ANGLE)

    GPIO.output(DIR_X, GPIO.HIGH if degree_x > 0 else GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH if degree_y > 0 else GPIO.LOW)

    for step in range(max(steps_x, steps_y)):
        if step < steps_x:
            GPIO.output(STEP_X, GPIO.HIGH)
        if step < steps_y:
            GPIO.output(STEP_Y, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(STEP_X, GPIO.LOW)
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
    distance = measure_distance()
    if distance:
        print(f"\n📏 Расстояние до доски: {distance:.2f} см")

    # # Фото
    # picam2 = Picamera2()
    # config = picam2.create_still_configuration(main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}, lores={"size": (640, 480)}, display="lores")
    # picam2.configure(config)
    # picam2.start_preview(Preview.QTGL)
    # picam2.start()
    # time.sleep(2)
    # picam2.capture_file("capture.jpg")
    # print("📷 Фото сделано")

    # Обработка
    image = cv2.imread("2shapes.png")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]

    print(f"🔍 Найдено фигур: {len(valid_contours)}")

    total_degree_x = 0
    total_degree_y = 0

    for i, contour in enumerate(valid_contours, 1):
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2
        shape = detect_shape(contour)

        if shape != FILTER_SHAPE:
            continue

        print(f"[{i}] {shape} в пикселях: ({center_x}, {center_y})")

        offset_x = center_x - CAMERA_WIDTH // 2
        offset_y = center_y - CAMERA_HEIGHT // 2

        degree_x = (offset_x / CAMERA_WIDTH) * FOV_DEGREES
        degree_y = (offset_y / CAMERA_HEIGHT) * FOV_DEGREES

        print(f" -> Поворот моторов на X: {degree_x:.2f}°, Y: {degree_y:.2f}°")
        rotate_motor(degree_x, degree_y)
        total_degree_x += degree_x
        total_degree_y += degree_y
        time.sleep(2)

    # Возврат в исходную позицию (в центр)
    print("\n↩️ Возврат в исходную позицию")
    rotate_motor(-total_degree_x, -total_degree_y)

finally:
    GPIO.output(DIR_X, GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH)
    GPIO.output(STEP_X, GPIO.LOW)
    GPIO.output(STEP_Y, GPIO.HIGH)
    print("\nРабота завершена, GPIO очищены")
