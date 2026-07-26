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

import numpy as np

ANGLE_SNAP_TOL_DEG = 12.0     # snap to 0/90 if within this many degrees
ENDPOINT_SNAP_TOL = 8.0       # px, merge endpoints closer than this
COLLINEAR_MERGE_GAP = 15.0    # px, merge collinear segments with gaps smaller than this
# Tolerance for deciding two parallel wall boxes are the SAME real wall
# (fragmented by YOLO into multiple boxes) vs two DIFFERENT, genuinely
# adjacent walls (e.g. an exterior wall and a nearby interior partition).
# This was previously reusing ENDPOINT_SNAP_TOL (8px), which was proven
# to be too loose -- it was fusing real distinct walls together and
# destroying the cycles needed for rooms to close (confirmed by testing
# with merging disabled: cycle count went from 0 to 1+ immediately).
CROSS_GROUP_TOL = 3.0


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


def nearest_point_on_segment(p, a, b):
    """Closest point on segment a-b to point p, and the distance to it."""
    p, a, b = np.array(p, dtype=float), np.array(a, dtype=float), np.array(b, dtype=float)
    ab = b - a
    length_sq = ab.dot(ab)
    if length_sq < 1e-9:
        return a, float(np.linalg.norm(p - a))
    t = max(0.0, min(1.0, (p - a).dot(ab) / length_sq))
    proj = a + t * ab
    return proj, float(np.linalg.norm(p - proj))


def close_wall_gaps(walls, search_radius=180.0, already_connected_tol=10.0):
    """
    Real floor plans have walls that visually meet at corners, but
    detection/merging noise leaves small gaps between them. Previously
    these gaps were only closed topologically (adding a graph edge
    that doesn't correspond to real geometry) -- rooms still couldn't
    close because the wall SHAPES themselves never actually touched.

    This instead moves each dangling ("open") wall endpoint to the
    nearest point on the nearest OTHER wall segment, if that distance
    is within search_radius. This is the same technique real floor-plan
    vectorization tools use to close corners. It intentionally does NOT
    touch endpoints that are already connected (within
    already_connected_tol), so real intersections are left alone.
    """
    endpoints = []  # (wall_idx, which_end, point)
    for i, w in enumerate(walls):
        endpoints.append((i, "p1", np.array(w["p1"], dtype=float)))
        endpoints.append((i, "p2", np.array(w["p2"], dtype=float)))

    closed_count = 0
    for i, which, pt in endpoints:
        # already connected to something? leave it alone.
        is_open = True
        for j, which2, pt2 in endpoints:
            if j == i and which2 == which:
                continue
            if np.linalg.norm(pt - pt2) < already_connected_tol:
                is_open = False
                break
        if not is_open:
            continue

        best = None  # (distance, projected_point)
        for k, w in enumerate(walls):
            if k == i:
                continue
            proj, dist = nearest_point_on_segment(pt, w["p1"], w["p2"])
            if best is None or dist < best[0]:
                best = (dist, proj)

        if best is not None and already_connected_tol <= best[0] <= search_radius:
            walls[i][which] = best[1].tolist()
            closed_count += 1

    print(f"[extract_wall_segments] closed {closed_count} dangling wall "
          f"endpoint(s) by extending to the nearest wall (search_radius="
          f"{search_radius}px)")
    return walls


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
            cross = round((w["p1"][cross_key] + w["p2"][cross_key]) / 2 / CROSS_GROUP_TOL) \
                * CROSS_GROUP_TOL
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

    walls, doors, windows, stairs, room_boxes = [], [], [], [], []
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
        elif cls == "room":
            # Not used for wall-graph reconstruction (that still comes
            # from the actual wall geometry, which is the geometrically
            # correct source). Kept here purely as a fallback so
            # create_room_floor_mesh.py can still render an approximate
            # floor when the wall graph is too sparse to close any real
            # room loop (e.g. too few wall detections to form a cycle).
            room_boxes.append({"bbox": bbox, "confidence": det.get("confidence")})

    merged_walls = merge_collinear(walls)
    merged_walls = close_wall_gaps(merged_walls)
    for i, d in enumerate(doors):
        d["id"] = i
    for i, w in enumerate(windows):
        w["id"] = i
    for i, s in enumerate(stairs):
        s["id"] = i
    for i, r in enumerate(room_boxes):
        r["id"] = i

    out = {"walls": merged_walls, "doors": doors, "windows": windows,
           "stairs": stairs, "room_boxes": room_boxes}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[extract_wall_segments] {len(walls)} raw wall boxes -> "
          f"{len(merged_walls)} merged wall segments")
    print(f"[extract_wall_segments] {len(doors)} doors, {len(windows)} windows, "
          f"{len(stairs)} stairs, {len(room_boxes)} room boxes (fallback only)")


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/v2_detections.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/wall_segments.json"
    main(in_path, out_path)