import json
import os

INPUT_FILE = "outputs/geometry/walls.json"
OUTPUT_FILE = "outputs/geometry/wall_segments.json"

os.makedirs("outputs/geometry", exist_ok=True)

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

segments = []

for wall in walls:

    x1 = wall["bbox"]["x1"]
    y1 = wall["bbox"]["y1"]
    x2 = wall["bbox"]["x2"]
    y2 = wall["bbox"]["y2"]

    width = wall["width"]
    height = wall["height"]

    # Horizontal wall
    if width >= height:

        center_y = (y1 + y2) / 2

        segment = {
            "orientation": "horizontal",
            "start": [round(x1, 2), round(center_y, 2)],
            "end": [round(x2, 2), round(center_y, 2)],
            "thickness": round(height, 2)
        }

    # Vertical wall
    else:

        center_x = (x1 + x2) / 2

        segment = {
            "orientation": "vertical",
            "start": [round(center_x, 2), round(y1, 2)],
            "end": [round(center_x, 2), round(y2, 2)],
            "thickness": round(width, 2)
        }

    segments.append(segment)

with open(OUTPUT_FILE, "w") as f:
    json.dump(segments, f, indent=4)

print(f"Converted {len(segments)} wall boxes into wall segments.")
print(f"Saved -> {OUTPUT_FILE}")