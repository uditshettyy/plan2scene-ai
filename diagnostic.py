import json, sys
sys.path.insert(0, "reconstruction")
from extract_wall_segments import normalize_bbox, bbox_to_segment, snap_angle

with open("outputs/test_lowconf.json") as f:
    detections = json.load(f)

raw_walls = []
for det in detections:
    if det["class"] != "wall":
        continue
    bbox = normalize_bbox(det["bbox"])
    p1, p2, thickness = bbox_to_segment(bbox)
    p1, p2 = snap_angle(p1, p2)
    raw_walls.append({"p1": list(p1), "p2": list(p2), "thickness": thickness})

print(f"RAW (unmerged) wall count: {len(raw_walls)}")
out = {"walls": raw_walls, "doors": [], "windows": [], "stairs": [], "room_boxes": []}
with open("outputs/wall_segments_raw_unmerged.json", "w") as f:
    json.dump(out, f, indent=2)