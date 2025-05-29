from ultralytics import YOLO
import os

# Перевірка файлів
train_images = os.listdir('images/Train')
train_labels = os.listdir('labels/Train')

print("Зображення:", len(train_images))
print("Мітки:", len(train_labels))

# Порівняння імен файлів
image_names = [f.split('.')[0] for f in train_images]
label_names = [f.split('.')[0] for f in train_labels]

missing_labels = set(image_names) - set(label_names)
print("Відсутні мітки:", missing_labels)

model = YOLO('best.pt')
results = model.train(
    data='data.yaml', 
    epochs=10, 
    imgsz=1280
)