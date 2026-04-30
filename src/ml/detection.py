import cv2

class DetectionModelOutput:
    def __init__(self, result, img_path):
        self.boxes: list[list[float]] = result.boxes.xywh
        self.names: list[str] = [result.names[cls.item()] for cls in result.boxes.cls.int()]
        self.confs: list[float] = result.boxes.conf
        self.letters: list[str] = []  # Store classified letters
        self.letter_confs: list[float] = []  # Store letter classification confidences

        self.result = result
        self.image_path = img_path

    def get_centers(self):
        """Extract center coordinates (x, y) for each detection"""
        centers = []
        for box in self.boxes:
            x, y, w, h = box
            cx = int(x)  # Center x is already x in xywh format
            cy = int(y)  # Center y is already y in xywh format
            centers.append((cx, cy))
        return centers

    def add_letter_data(self, letters: list[str], letter_confs: list[float]):
        """Add classified letters and their confidences"""
        self.letters = letters
        self.letter_confs = letter_confs

    def get_detections_with_letters(self):
        """Returns complete detection data: shape, letter, center coords, and confidences"""
        detections = []
        for i, (box, shape, conf) in enumerate(zip(self.boxes, self.names, self.confs)):
            x, y, w, h = box
            cx = int(x)
            cy = int(y)
            
            letter = self.letters[i] if i < len(self.letters) else "?"
            letter_conf = self.letter_confs[i] if i < len(self.letter_confs) else 0.0
            
            detections.append({
                'shape': shape,
                'letter': letter,
                'center_x': cx,
                'center_y': cy,
                'detection_confidence': float(conf),
                'classification_confidence': letter_conf
            })
        return detections

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
