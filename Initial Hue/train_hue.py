import os
from multiprocessing import freeze_support

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from ultralytics import YOLO


def main():
    model = YOLO("yolo26n.pt")

    model.train(
        data="dataset_hue/data.yaml",
        epochs=50,
        imgsz=640,
        device=0,
        workers=0,
        name="train_hue"
    )


if __name__ == "__main__":
    freeze_support()
    main()