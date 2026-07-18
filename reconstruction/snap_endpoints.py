import json
import math
import os

INPUT_FILE = "outputs/geometry/optimized_walls.json"
OUTPUT_FILE = "outputs/geometry/snapped_walls.json"

SNAP_DISTANCE = 20

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

points = []

for wall in walls:
    points.append(wall["start"])
    points.append(wall["end"])


def distance(p1, p2):
    return math.sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2
    )


# Snap nearby points
for i in range(len(points)):
    for j in range(i + 1, len(points)):

        if distance(points[i], points[j]) < SNAP_DISTANCE:

            avg_x = (points[i][0] + points[j][0]) / 2
            avg_y = (points[i][1] + points[j][1]) / 2

            points[i][0] = avg_x
            points[i][1] = avg_y

            points[j][0] = avg_x
            points[j][1] = avg_y

# Write points back
idx = 0

for wall in walls:
    wall["start"] = points[idx]
    idx += 1

    wall["end"] = points[idx]
    idx += 1

os.makedirs("outputs/geometry", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(walls, f, indent=4)

print(f"Original walls : {len(walls)}")
print(f"Saved snapped walls -> {OUTPUT_FILE}")