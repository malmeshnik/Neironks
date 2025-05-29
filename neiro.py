from ultralytics import YOLO
import cv2

# Завантаження моделі
model = YOLO(r"D:\датасет\runs\detect\train\weights\best.pt")

# Завантаження відео
cap = cv2.VideoCapture(r"D:\neiroset\172.16.0.20_035_072 NEZALEZ-SHID-20230516070000-20230516085959(2)_part1.ts")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Зміна розміру кадру до 640x640
    resized_frame = cv2.resize(frame, (1920, 1280))

    # Передача кадру в модель
    results = model(resized_frame)
    annotated_frame = results[0].plot()

    # Відображення обробленого кадру
    cv2.imshow("Video", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
