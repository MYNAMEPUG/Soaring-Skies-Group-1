import os
from multiprocessing import freeze_support

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO


def main():
    model = YOLO("yolo26n-cls.pt")

    model.train(
        data="classifier_dataset",
        epochs=50,
        imgsz=224,
        device=0,
        workers=0,
        batch=128,
        name="letter_classifier"
    )


if __name__ == "__main__":
    freeze_support()
    main()