import json
import os

INPUT_FILE = "outputs/geometry/detections.json"
OUTPUT_DIR = "outputs/geometry"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    detections = json.load(f)

rooms = []

for detection in detections:
    if detection["class"] == "room":
        rooms.append(detection)

output_file = os.path.join(OUTPUT_DIR, "rooms.json")

with open(output_file, "w") as f:
    json.dump(rooms, f, indent=4)

print(f"Total detections : {len(detections)}")
print(f"Room detections  : {len(rooms)}")
print(f"Saved -> {output_file}")