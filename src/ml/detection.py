import cv2
class DetectionModelOutput:
    def __init__(self, result, img_path):
        self.boxes: list[list[float]] = result.boxes.xywh
        self.names: list[str] = [result.names[cls.item()] for cls in result.boxes.cls.int()]
        self.confs: list[float] = result.boxes.conf

        self.result = result
        self.image_path = img_path

    def show_with_all(self):
        self.result.show()

    def show_bounds(self):
        image = cv2.imread(self.image_path)

        color = (0, 255, 0)
        for box in self.boxes:
            x, y, w, h = box
            x, y, w, h = int(x - int(w) // 2), int(y - int(h) // 2), int(w), int(h)

            thickness = 2

            cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)

        cv2.imshow("Bounding Box", image)
        cv2.waitKey()

    def __repr__(self):
        out = "(Label): (Confidence)\n--------------------\n"
        for name, conf in zip(self.names, self.confs):
            out += f"{name}: {conf:.4f}\n"

        return out
