import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
from picamera2 import Picamera2, Preview
from math import atan, degrees

# === НАСТРОЙКИ === #
BOARD_WIDTH_CM = 166   # Ширина доски в см
BOARD_HEIGHT_CM = 95  # Высота доски в см
STEP_ANGLE = 0.32727   # градуса на шаг
STEP_DELAY = 0.001
MIN_CONTOUR_AREA = 500
print("1 - Circle")
print("2 - Squar")
print("3 - Triangle")
shape = int(input("Select shape: "))
if shape == 1:
    FILTER_SHAPE = "Circle"
elif shape == 2:
    FILTER_SHAPE = "Square"
elif shape == 3:
    FILTER_SHAPE = "Triangle"
# Пины ультразвукового датчика
TRIG = 4
ECHO = 17
time.sleep(3)
# Пины моторов
DIR_X = 21
STEP_X = 20
DIR_Y = 7
STEP_Y = 1

# Ограничения по углам моторов
MAX_X_ANGLE = 90
MAX_Y_ANGLE = 30

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
# def rotate_motor(degree_x, degree_y):
#     degree_x = max(-MAX_X_ANGLE, min(MAX_X_ANGLE, degree_x))
#     degree_y = max(-MAX_Y_ANGLE, min(MAX_Y_ANGLE, degree_y))
#
#     steps_x = round(abs(degree_x) / STEP_ANGLE)
#     steps_y = round(abs(degree_y) / STEP_ANGLE)
#
#     if steps_x == 0 and steps_y == 0:
#         print("⚠️ Шагов слишком мало, пропускаем поворот")
#         return
#
#     print(f"   🔁 Шагов X: {steps_x}, Y: {steps_y}")
#
#     GPIO.output(DIR_X, GPIO.HIGH if degree_x > 0 else GPIO.LOW)
#     GPIO.output(DIR_Y, GPIO.HIGH if degree_y > 0 else GPIO.LOW)
#
#     for step in range(max(steps_x, steps_y)):
#         if step < steps_x:
#             GPIO.output(STEP_X, GPIO.HIGH)
#         if step < steps_y:
#             GPIO.output(STEP_Y, GPIO.HIGH)
#         time.sleep(STEP_DELAY)
#         GPIO.output(STEP_X, GPIO.LOW)
#         GPIO.output(STEP_Y, GPIO.LOW)
#         time.sleep(STEP_DELAY)
def rotate_motor(degree_x, degree_y):
    # Ограничиваем углы, чтобы не выйти за физические пределы
    degree_x = max(-MAX_X_ANGLE, min(MAX_X_ANGLE, degree_x))
    degree_y = max(-MAX_Y_ANGLE, min(MAX_Y_ANGLE, degree_y)) # Только вверх!

    steps_x = round(abs(degree_x) / STEP_ANGLE)
    steps_y = round(abs(degree_y) / STEP_ANGLE)

    if steps_x == 0 and steps_y == 0:
        print("⚠️ Шагов слишком мало, пропускаем поворот")
        return

    print(f"   🔁 Шагов X: {steps_x}, Y: {steps_y}")

    # Определяем направления
    GPIO.output(DIR_X, GPIO.HIGH if degree_x > 0 else GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH if degree_x < 0 else GPIO.LOW)

    # Сначала крутим X
    for _ in range(steps_x):
        GPIO.output(STEP_X, GPIO.HIGH)
        GPIO.output(STEP_Y, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(STEP_X, GPIO.LOW)
        GPIO.output(STEP_Y, GPIO.LOW)
        time.sleep(STEP_DELAY)

    GPIO.output(DIR_X, GPIO.HIGH if degree_y > 0 else GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH if degree_y > 0 else GPIO.LOW)

    # Потом крутим Y
    for _ in range(steps_y):
        GPIO.output(STEP_X, GPIO.HIGH)
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


# rotate_motor(20, 0)
# time.sleep(2)
# rotate_motor(10, 20)
# time.sleep(2)
# rotate_motor(-50, -40)
# time.sleep(2)
# rotate_motor(20, 20)
# while True:
#     pass


# === ГЛАВНАЯ ЛОГИКА === #
try:
    distance = 300 #measure_distance()
    if distance:
        print(f"\n📏 Расстояние до доски: {distance:.2f} см")
    else:
        raise Exception("Не удалось измерить расстояние")

    # Фото
    # picam2 = Picamera2()
    # camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)},
    #                                                   display="lores")
    # picam2.configure(camera_config)
    # picam2.start()
    # time.sleep(2)
    # picam2.capture_file("capture.jpg")
    # print("📷 Фото сделано")
    # Обработка
    image = cv2.imread("red.png")
    height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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

        print(f"\n[{i}] {shape}")
        print(f" Центр фигуры в пикселях: ({center_x}, {center_y})")

        # --- Вычисление отклонений ---
        dx_pixels = center_x - (width / 2)
        dy_pixels = height - center_y

        print(f" dx_pixels: {dx_pixels}")
        print(f" dy_pixels: {dy_pixels}")

        dx_cm = dx_pixels * (BOARD_WIDTH_CM / width)
        dy_cm = dy_pixels * (BOARD_HEIGHT_CM / height)
        # dx_cm = 0
        # dy_cm = 10

        print(f" dx_cm: {dx_cm:.2f} см")
        print(f" dy_cm: {dy_cm:.2f} см")

        # --- Вычисление углов ---
        angle_x = degrees(atan(dx_cm / distance))
        angle_y = degrees(atan(dy_cm / distance))

        # ⚠️ Если лазер по X уходит в неправильную сторону, здесь инвертируем
        # angle_x = -degrees(atan(dx_cm / distance))

        print(f" Расчёт углов:")
        print(f"  ➔ Угол X: {angle_x:.2f}°")
        print(f"  ➔ Угол Y: {angle_y:.2f}°")


        # --- Поворот на фигуру ---
        print(" 🔄 Поворачиваем на фигуру")
        rotate_motor(angle_x, angle_y)

        time.sleep(2)

        rotate_motor(-angle_x, -angle_y)

        time.sleep(2)


finally:
    GPIO.output(DIR_X, GPIO.LOW)
    GPIO.output(DIR_Y, GPIO.HIGH)
    GPIO.output(STEP_X, GPIO.LOW)
    GPIO.output(STEP_Y, GPIO.HIGH)
    print("\n✅ Работа завершена, GPIO очищены")