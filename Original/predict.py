from ultralytics import YOLO

model = YOLO("runs/detect/train-7/weights/best.pt")

model.predict(
    source="your_test_image.jpg",
    save=True,
    conf=0.25
)