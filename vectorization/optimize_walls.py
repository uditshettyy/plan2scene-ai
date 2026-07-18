import json
import os

INPUT_FILE = "outputs/geometry/wall_segments.json"
OUTPUT_FILE = "outputs/geometry/optimized_walls.json"

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

HORIZONTAL_TOLERANCE = 15  # pixels

horizontal = [w for w in walls if w["orientation"] == "horizontal"]
vertical = [w for w in walls if w["orientation"] == "vertical"]

horizontal.sort(key=lambda w: w["start"][1])

merged = []

for wall in horizontal:

    if not merged:
        merged.append(wall)
        continue

    last = merged[-1]

    same_line = abs(last["start"][1] - wall["start"][1]) < HORIZONTAL_TOLERANCE

    overlap = wall["start"][0] <= last["end"][0]

    if same_line and overlap:

        last["end"][0] = max(last["end"][0], wall["end"][0])

        last["thickness"] = max(last["thickness"], wall["thickness"])

    else:
        merged.append(wall)

optimized = merged + vertical

with open(OUTPUT_FILE, "w") as f:
    json.dump(optimized, f, indent=4)

print(f"Original walls : {len(walls)}")
print(f"Optimized walls: {len(optimized)}")