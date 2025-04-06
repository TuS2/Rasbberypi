import tflite_runtime.interpreter as tflite
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import time
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)},
                                                  display="lores")
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)
picam2.start()
time.sleep(2)
picam2.capture_file("test.jpg")
# cut
image_path = "test.jpg"
# Функция для определения типа фигуры
def detect_shape(contour):
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    sides = len(approx)

    if sides == 3:
        return "Triangle"
    elif sides == 4:
        return "Square"
    elif sides > 4:
        return "Circle"
    else:
        return "Unknown"

# Загружаем изображение
# image_path = "2shapes.png"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Преобразуем в градации серого
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Применяем размытие
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Поиск границ с помощью Canny
edges = cv2.Canny(blurred, 50, 150)

# Находим контуры
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if not contours:
    raise ValueError("Фигуры не найдены!")

# Минимальная площадь контура (чтобы исключить шум)
MIN_CONTOUR_AREA = 500

# Оставляем только контуры, которые больше MIN_CONTOUR_AREA
valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]

# Количество найденных фигур
shape_count = len(valid_contours)
print(f"Количество найденных фигур: {shape_count}")

# Открываем файл для записи координат
with open("shapes.txt", "w") as file:
    file.write(f"Количество найденных фигур: {shape_count}\n")

    # Перебираем все найденные фигуры
    for i, contour in enumerate(valid_contours, 1):
        # Определяем тип фигуры
        shape_name = detect_shape(contour)

        # Получаем координаты ограничивающего прямоугольника
        x, y, w, h = cv2.boundingRect(contour)

        # Записываем координаты и тип фигуры в файл
        file.write(f"{i}. {shape_name}: x={x}, y={y}, w={w}, h={h}\n")

        # Рисуем контур
        cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)

        # Вычисляем центр фигуры
        M = cv2.moments(contour)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            cv2.circle(image, (center_x, center_y), 5, (255, 0, 0), -1)  # Отмечаем центр

print("Координаты сохранены в 'shapes.txt'")

# Сохраняем изображение с выделенными фигурами
cv2.imwrite("output_with_all_shapes.jpg", image)
print("Фигуры успешно найдены и сохранены в 'output_with_all_shapes.jpg'")

# === ОСТАЛЬНАЯ ЧАСТЬ КОДА ДЛЯ ОБРАБОТКИ В TFLITE ===

# Загружаем TFLite модель
model_path = "model.tflite"
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Получаем информацию о входных и выходных данных модели
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Загружаем и подготавливаем изображение для модели
image_path = "clean_cut.png"
image = cv2.imread(image_path, cv2.IMREAD_COLOR)

# Преобразуем в HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Определяем диапазоны цветов
color_ranges = {
    "red": [(0, 100, 100), (10, 255, 255), (160, 100, 100), (180, 255, 255)],
    "green": [(40, 40, 40), (90, 255, 255)],
    "blue": [(90, 50, 50), (140, 255, 255)]
}

# Создаём маску по цветам
mask = np.zeros_like(hsv[:, :, 0])
for color, ranges in color_ranges.items():
    for i in range(0, len(ranges), 2):
        lower, upper = ranges[i], ranges[i + 1]
        mask |= cv2.inRange(hsv, np.array(lower), np.array(upper))

# Ищем контуры на маске
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if len(contours) == 0:
    raise ValueError("Фигуры не найдены!")

# Оставляем только контуры, которые больше MIN_CONTOUR_AREA
contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]
if not contours:
    raise ValueError("Нет достаточно больших фигур!")

# Создаём маску для выделенной фигуры
shape_mask = np.zeros_like(mask)
cv2.drawContours(shape_mask, contours, -1, 255, thickness=cv2.FILLED)

# Извлекаем фигуру
extracted = cv2.bitwise_and(image, image, mask=shape_mask)

# Получаем bounding box и вырезаем фигуру
x, y, w, h = cv2.boundingRect(contours[0])
cropped_shape = extracted[y:y + h, x:x + w]

# Добавляем альфа-канал
b, g, r = cv2.split(cropped_shape)
alpha = shape_mask[y:y + h, x:x + w]
cutout = cv2.merge([b, g, r, alpha])

# Сохраняем результат
cv2.imwrite("cut.png", cutout)

# Подготавливаем изображение для модели
input_size = input_details[0]['shape'][1]
aspect_ratio = max(w, h) / input_size
new_w, new_h = int(w / aspect_ratio), int(h / aspect_ratio)
cropped_resized = cv2.resize(cropped_shape, (new_w, new_h))

# Создаём квадратное изображение
padded = np.ones((input_size, input_size, 3), dtype=np.uint8) * 255
x_offset = (input_size - new_w) // 2
y_offset = (input_size - new_h) // 2
padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = cropped_resized

# Нормализация и добавление размерности batch
image_input = padded.astype(np.float32) / 255.0
image_input = np.expand_dims(image_input, axis=0)

# Запуск модели
interpreter.set_tensor(input_details[0]['index'], image_input)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

# Интерпретация результатов
class_labels = ["Circle", "Square"]
confidence_scores = output_data[0][:3]
predicted_class = np.argmax(confidence_scores)

# Вывод результатов
print(f"Confidence scores: {confidence_scores}")
print(class_labels[predicted_class])
