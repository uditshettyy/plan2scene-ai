from ultralytics import YOLO
import json
import sys
from pathlib import Path


MODEL_PATH = "models/yolo_plan2scene_v2.pt"


class_names = {
    0: "wall",
    1: "room",
    2: "door",
    3: "window"
}


# Load model once
model = YOLO(MODEL_PATH)


def run_inference(image_path, output_path):

    print("[backend_inference] Loading image:")
    print(image_path)


    results = model.predict(
        source=image_path,
        save=False,
        conf=0.25,
        imgsz=640
    )


    detections = []


    for r in results:

        boxes = r.boxes


        for box in boxes:

            cls_id = int(box.cls[0])

            confidence = float(box.conf[0])


            x1, y1, x2, y2 = box.xyxy[0].tolist()


            detections.append(
                {
                    "class": class_names[cls_id],

                    "confidence": round(
                        confidence,
                        3
                    ),

                    "bbox":
                    {
                        "x1": round(x1,2),
                        "y1": round(y1,2),
                        "x2": round(x2,2),
                        "y2": round(y2,2)
                    }
                }
            )


    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(output_path,"w") as f:

        json.dump(
            detections,
            f,
            indent=4
        )


    print(
        f"[backend_inference] Saved {len(detections)} detections"
    )



if __name__ == "__main__":


    if len(sys.argv) != 3:

        print(
            "Usage: python backend_inference.py input_image output_json"
        )

        sys.exit(1)



    image_path = sys.argv[1]

    output_path = sys.argv[2]


    run_inference(
        image_path,
        output_path
    )