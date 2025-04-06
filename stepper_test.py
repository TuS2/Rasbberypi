import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO_TRIGGER = 4
GPIO_ECHO = 17

GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

def measure_distance():
    # Убедиться, что триггер низкий
    GPIO.output(GPIO_TRIGGER, False)
    time.sleep(0.05)

    # Отправка импульса 10 мкс
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    timeout = time.time() + 1  # максимум 20 мс ожидания

    while GPIO.input(GPIO_ECHO) == 0:
        start = time.time()
        if start > timeout:
            print("Timeout waiting for echo start")
            return None

    timeout = time.time() + 0.02
    while GPIO.input(GPIO_ECHO) == 1:
        stop = time.time()
        if stop > timeout:
            print("Timeout waiting for echo end")
            return None

    elapsed = stop - start
    distance = (elapsed * 34300) / 2

    return distance

try:
    dist = measure_distance()
    if dist is not None:
        print(f"Расстояние: {dist:.2f} см")
    else:
        print("Не удалось измерить расстояние.")
finally:
    GPIO.cleanup()
