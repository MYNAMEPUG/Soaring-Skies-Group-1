from ultralytics import YOLO
import cv2
from pathlib import Path
import random
import gc
import torch

# Paths
detector_path = "runs/detect/train_bg/weights/best.pt"
classifier_path = "runs/classify/letter_classifier-3/weights/best.pt"

source = "test_images"

output_dir = Path("combined_predictions")
output_dir.mkdir(exist_ok=True)

allowed_letters = {
    "Pentagon": ["M"],
    "Rectangle": ["Y"],
    "Hexagon": ["F"],
    "Triangle": ["X"],
    "Cross": ["H", "E"],
    "Square": ["V"],
    "Semi Circle": ["B"],
    "Octagon": ["S"],
    "Quarter Circle": ["U"],
}

CROSS_CONF_THRESHOLD = 0.60

# -------------------------
# Step 1: Load detector only
# -------------------------
detector = YOLO(detector_path)
detector_results = detector.predict(source=source, conf=0.25, save=False)

all_images = []

for result in detector_results:
    img = result.orig_img.copy()
    img_path = Path(result.path)

    detections = []

    for box in result.boxes:
        shape_id = int(box.cls[0])
        shape_name = detector.names[shape_id]
        detect_conf = float(box.conf[0])

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        pad = 10
        h, w = img.shape[0],img.shape[1]

        x1p = max(0, x1 - pad)
        y1p = max(0, y1 - pad)
        x2p = min(w, x2 + pad)
        y2p = min(h, y2 + pad)

        crop = img[y1p:y2p, x1p:x2p]

        if crop.size == 0:
            continue

        detections.append({
            "shape": shape_name,
            "detect_conf": detect_conf,
            "box": (x1, y1, x2, y2),
            "crop": crop,
        })

    all_images.append({
        "img": img,
        "path": img_path,
        "detections": detections,
    })

# Clear detector from RAM/GPU memory
del detector
gc.collect()

if torch.cuda.is_available():
    torch.cuda.empty_cache()

print("Detector cleared from memory.")

# ----------------------------
# Step 2: Load classifier only
# ----------------------------
classifier = YOLO(classifier_path)
class_names = list(classifier.names.values())

for item in all_images:
    img = item["img"]
    img_path = item["path"]
    detections = item["detections"]

    for d in detections:
        shape_name = d["shape"]
        crop = d["crop"]

        cls_result = classifier.predict(crop, save=False, verbose=False)[0]
        probs = cls_result.probs.data.cpu().numpy()

        allowed = allowed_letters.get(shape_name, class_names)

        best_letter = None
        best_conf = -1.0

        for letter in allowed:
            if letter not in class_names:
                continue

            letter_id = class_names.index(letter)
            conf_score = float(probs[letter_id])

            if conf_score > best_conf:
                best_conf = conf_score
                best_letter = letter

        if best_letter is None:
            best_letter = "?"
            best_conf = 0.0

        d["letter"] = best_letter
        d["conf"] = best_conf

    # Cross rule: one E and one H
    cross_indices = [
        idx for idx, d in enumerate(detections)
        if d["shape"] == "Cross"
    ]

    if len(cross_indices) == 2:
        c1_idx, c2_idx = cross_indices
        c1 = detections[c1_idx]
        c2 = detections[c2_idx]

        c1_confident = c1["conf"] >= CROSS_CONF_THRESHOLD
        c2_confident = c2["conf"] >= CROSS_CONF_THRESHOLD

        if c1_confident and not c2_confident:
            detections[c2_idx]["letter"] = "H" if c1["letter"] == "E" else "E"
            detections[c2_idx]["conf"] = 0.50

        elif c2_confident and not c1_confident:
            detections[c1_idx]["letter"] = "H" if c2["letter"] == "E" else "E"
            detections[c1_idx]["conf"] = 0.50

        elif not c1_confident and not c2_confident:
            letters = ["H", "E"]
            random.shuffle(letters)
            detections[c1_idx]["letter"] = letters[0]
            detections[c1_idx]["conf"] = 0.50
            detections[c2_idx]["letter"] = letters[1]
            detections[c2_idx]["conf"] = 0.50

        elif c1["letter"] == c2["letter"]:
            if c1["conf"] >= c2["conf"]:
                detections[c2_idx]["letter"] = "H" if c1["letter"] == "E" else "E"
                detections[c2_idx]["conf"] = 0.50
            else:
                detections[c1_idx]["letter"] = "H" if c2["letter"] == "E" else "E"
                detections[c1_idx]["conf"] = 0.50

    # Draw detections
    for d in detections:
        shape_name = d["shape"]
        letter = d["letter"]
        conf = d["conf"]
        detect_conf = d["detect_conf"]
        x1, y1, x2, y2 = d["box"]

        label = f"{shape_name}: {letter} ({conf:.2f})"

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(
            img,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        print(
            f"{img_path.name}: {shape_name} -> {letter} "
            f"| detect={detect_conf:.2f}, classify={conf:.2f}"
        )

    save_path = output_dir / img_path.name
    cv2.imwrite(str(save_path), img)

# Clear classifier too
del classifier
gc.collect()

if torch.cuda.is_available():
    torch.cuda.empty_cache()

print("Done! Results saved in combined_predictions/")