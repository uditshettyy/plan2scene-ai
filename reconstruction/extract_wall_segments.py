"""
extract_wall_segments.py

Stage: detections -> wall segments

Input:  outputs/v2_detections.json
        YOLO11 output, one entry per detected box:
        {
          "class": "wall" | "door" | "window" | "room" | "stairs",
          "bbox": [x1, y1, x2, y2],   # pixel coords
          "confidence": 0.93
        }

Output: outputs/wall_segments.json
        {
          "walls": [{"id": 0, "p1": [x,y], "p2": [x,y], "thickness": 12.0}, ...],
          "doors": [{"id": 0, "bbox": [x1,y1,x2,y2], "center": [x,y]}, ...],
          "windows": [...],
          "stairs": [...]
        }

Pipeline:
  1. Load detections, split by class.
  2. Convert each "wall" bbox into a line segment: walls detected by YOLO
     are thin rectangles, so the segment is the long axis of the box.
  3. Orthogonalize: snap each segment's angle to the nearest 0/90 degrees
     if it's within an angular tolerance (real floor plans are almost
     always axis-aligned; small angle noise comes from detection jitter).
  4. Merge collinear, overlapping/adjacent segments into single walls.
  5. Snap endpoints that are close together (handled again more
     aggressively later in build_connected_wall_graph.py, but doing a
     first pass here keeps wall_segments.json itself clean).

Usage:
    python extract_wall_segments.py outputs/v2_detections.json outputs/wall_segments.json
"""

import json
import math
import sys
from collections import defaultdict

ANGLE_SNAP_TOL_DEG = 12.0     # snap to 0/90 if within this many degrees
ENDPOINT_SNAP_TOL = 8.0       # px, merge endpoints closer than this
COLLINEAR_MERGE_GAP = 15.0    # px, merge collinear segments with gaps smaller than this


def normalize_bbox(bbox):
    """Accepts either a dict {"x1":.., "y1":.., "x2":.., "y2":..} (also
    tolerates "xmin"/"ymin"/"xmax"/"ymax") or a list/tuple [x1,y1,x2,y2],
    and always returns a plain [x1, y1, x2, y2] list of floats."""
    if isinstance(bbox, dict):
        keys_variants = [
            ("x1", "y1", "x2", "y2"),
            ("xmin", "ymin", "xmax", "ymax"),
        ]
        for kx1, ky1, kx2, ky2 in keys_variants:
            if kx1 in bbox:
                return [float(bbox[kx1]), float(bbox[ky1]),
                         float(bbox[kx2]), float(bbox[ky2])]
        raise ValueError(f"Unrecognized bbox dict keys: {list(bbox.keys())}")
    return [float(v) for v in bbox]


def bbox_to_segment(bbox):
    """A wall bbox is a thin rectangle. The wall's centerline runs along
    its long axis. Thickness is the short axis."""
    x1, y1, x2, y2 = bbox
    w, h = abs(x2 - x1), abs(y2 - y1)
    cx1, cy1 = (x1, (y1 + y2) / 2)
    cx2, cy2 = (x2, (y1 + y2) / 2)
    if h >= w:
        # vertical wall: long axis is y
        p1 = ((x1 + x2) / 2, y1)
        p2 = ((x1 + x2) / 2, y2)
        thickness = w
    else:
        # horizontal wall: long axis is x
        p1 = (x1, (y1 + y2) / 2)
        p2 = (x2, (y1 + y2) / 2)
        thickness = h
    return p1, p2, max(thickness, 4.0)


def snap_angle(p1, p2):
    """Snap a segment's orientation to the nearest 0 or 90 degrees if
    it's within ANGLE_SNAP_TOL_DEG, rotating around its midpoint."""
    x1, y1 = p1
    x2, y2 = p2
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    length = math.hypot(x2 - x1, y2 - y1)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2

    nearest = round(ang / 90.0) * 90.0
    if abs(ang - nearest) <= ANGLE_SNAP_TOL_DEG:
        rad = math.radians(nearest)
        dx, dy = math.cos(rad) * length / 2, math.sin(rad) * length / 2
        return (mx - dx, my - dy), (mx + dx, my + dy)
    return p1, p2


def merge_collinear(walls):
    """Group walls by orientation (horizontal/vertical) and merge those
    that share a line and are close enough along that line to be one
    continuous wall."""
    horiz, vert = [], []
    for w in walls:
        (x1, y1), (x2, y2) = w["p1"], w["p2"]
        if abs(y2 - y1) < abs(x2 - x1):
            horiz.append(w)
        else:
            vert.append(w)

    def merge_group(group, axis_key, cross_key):
        # axis_key: the coordinate that varies along the wall's length
        # cross_key: the coordinate that's constant along the wall
        by_cross = defaultdict(list)
        for w in group:
            cross = round((w["p1"][cross_key] + w["p2"][cross_key]) / 2 / ENDPOINT_SNAP_TOL) \
                * ENDPOINT_SNAP_TOL
            by_cross[cross].append(w)

        merged = []
        for cross, segs in by_cross.items():
            intervals = []
            for w in segs:
                a = w["p1"][axis_key]
                b = w["p2"][axis_key]
                lo, hi = min(a, b), max(a, b)
                intervals.append((lo, hi, w["thickness"]))
            intervals.sort()

            cur_lo, cur_hi, cur_th = intervals[0]
            for lo, hi, th in intervals[1:]:
                if lo <= cur_hi + COLLINEAR_MERGE_GAP:
                    cur_hi = max(cur_hi, hi)
                    cur_th = max(cur_th, th)
                else:
                    merged.append((cur_lo, cur_hi, cross, cur_th))
                    cur_lo, cur_hi, cur_th = lo, hi, th
            merged.append((cur_lo, cur_hi, cross, cur_th))

        out = []
        for lo, hi, cross, th in merged:
            p1 = [0, 0]
            p2 = [0, 0]
            p1[axis_key] = lo
            p1[cross_key] = cross
            p2[axis_key] = hi
            p2[cross_key] = cross
            out.append({"p1": p1, "p2": p2, "thickness": th})
        return out

    out = merge_group(horiz, axis_key=0, cross_key=1)
    out += merge_group(vert, axis_key=1, cross_key=0)
    for i, w in enumerate(out):
        w["id"] = i
    return out


def main(in_path, out_path):
    with open(in_path) as f:
        detections = json.load(f)
    if isinstance(detections, dict):
        detections = detections.get("detections", detections.get("boxes", []))

    walls, doors, windows, stairs = [], [], [], []
    for det in detections:
        cls = det["class"]
        bbox = normalize_bbox(det["bbox"])
        if cls == "wall":
            p1, p2, thickness = bbox_to_segment(bbox)
            p1, p2 = snap_angle(p1, p2)
            walls.append({"p1": list(p1), "p2": list(p2), "thickness": thickness})
        elif cls == "door":
            x1, y1, x2, y2 = bbox
            doors.append({"bbox": bbox, "center": [(x1 + x2) / 2, (y1 + y2) / 2]})
        elif cls == "window":
            x1, y1, x2, y2 = bbox
            windows.append({"bbox": bbox, "center": [(x1 + x2) / 2, (y1 + y2) / 2]})
        elif cls == "stairs":
            x1, y1, x2, y2 = bbox
            stairs.append({"bbox": bbox, "center": [(x1 + x2) / 2, (y1 + y2) / 2]})
        # "room" class boxes are ignored here -- rooms are derived
        # geometrically from the wall graph (vector_room_face_extractor.py),
        # not from the room detector, since the detector's box is only a
        # rough localization hint, not a polygon.

    merged_walls = merge_collinear(walls)
    for i, d in enumerate(doors):
        d["id"] = i
    for i, w in enumerate(windows):
        w["id"] = i
    for i, s in enumerate(stairs):
        s["id"] = i

    out = {"walls": merged_walls, "doors": doors, "windows": windows, "stairs": stairs}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[extract_wall_segments] {len(walls)} raw wall boxes -> "
          f"{len(merged_walls)} merged wall segments")
    print(f"[extract_wall_segments] {len(doors)} doors, {len(windows)} windows, "
          f"{len(stairs)} stairs")


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/v2_detections.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/wall_segments.json"
    main(in_path, out_path)