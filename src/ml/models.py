from ultralytics import YOLO
import cv2
from helper.math_func import calculate3Ddist
from detection import DetectionModelOutput


def yolov26(image_path:str =""):
    model = YOLO("yolo26n.pt")

    image = cv2.imread(image_path)

# Run detection
    results = model.track(source=image, stream=True)
    ordered_pairs = []
    for r in results:
        if r.boxes.id is not None:
            boxes = r.boxes.xyxy.cpu().numpy()
            track_ids = r.boxes.id.cpu().numpy()
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                ordered_pairs.append((cx, cy))

    current_position = [1, 0, 0]

    arranged_graph = []  # Changed to a list for mutability

# Make a mutable copy of ordered_pairs if you intend to modify it
    ordered_points_to_process = list(ordered_pairs)

    while ordered_points_to_process:
        closest_node = min(
            ordered_points_to_process,
            key=lambda i: calculate3Ddist(i, current_position)
        )
        arranged_graph.append(closest_node)
        ordered_points_to_process.remove(closest_node)
        current_position = closest_node

    return arranged_graph

class DetectionModel:
    def __init__(self, parameter_file: str) -> None:
        self.model = YOLO(parameter_file)
        # print(self.model.__dir__())
        # exit(1)

    def predict(self, img_path):
        result = self.model(img_path)[0]
        # print(result.boxes)

        return DetectionModelOutput(result, img_path)


if __name__ == "__main__":
    model = DetectionModel("best_the_actual_dataset.pt")
    # model = DetectionModel("/opt/homebrew/runs/detect/train80/weights/best.pt")
    # model = DetectionModel("/Users/alejansropinto/Dev/Imaging2025/yolo11n.onnx")

    result = model.predict("test_images/visdrone.jpg")
    print(len(result.confs))
    print(result.boxes)
    result.show_bounds()
    result.show_with_all()
