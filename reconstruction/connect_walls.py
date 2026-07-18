import json
import os

INPUT_FILE = "outputs/geometry/snapped_walls.json"
OUTPUT_FILE = "outputs/geometry/connected_walls.json"

TOLERANCE = 25

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

horizontal = [w for w in walls if w["orientation"] == "horizontal"]
vertical = [w for w in walls if w["orientation"] == "vertical"]


for h in horizontal:

    hsx, hsy = h["start"]
    hex, hey = h["end"]

    for v in vertical:

        vsx, vsy = v["start"]
        vex, vey = v["end"]

        # Is vertical endpoint close to horizontal end?
        if abs(hex - vsx) < TOLERANCE and abs(hsy - vsy) < TOLERANCE:

            intersection = [vsx, hsy]

            h["end"] = intersection
            v["start"] = intersection

        # Is vertical endpoint close to horizontal start?
        elif abs(hsx - vsx) < TOLERANCE and abs(hsy - vsy) < TOLERANCE:

            intersection = [vsx, hsy]

            h["start"] = intersection
            v["start"] = intersection

        # Bottom endpoint close to horizontal end
        elif abs(hex - vex) < TOLERANCE and abs(hsy - vey) < TOLERANCE:

            intersection = [vex, hsy]

            h["end"] = intersection
            v["end"] = intersection

        # Bottom endpoint close to horizontal start
        elif abs(hsx - vex) < TOLERANCE and abs(hsy - vey) < TOLERANCE:

            intersection = [vex, hsy]

            h["start"] = intersection
            v["end"] = intersection


connected = horizontal + vertical

os.makedirs("outputs/geometry", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(connected, f, indent=4)

print(f"Connected walls saved -> {OUTPUT_FILE}")