"""
create_wall_mesh.py

Stage: wall graph + door/window detections -> 3D wall mesh with real
openings (not solid extrusions with doors/windows floating on top).

Input:
    outputs/vector_wall_graph_v3.json   (nodes, edges, edge_thickness)
    outputs/wall_segments.json          (doors, windows -- for bbox/center)

Output:
    outputs/meshes/vector_walls.obj
    outputs/meshes/wall_openings.json   (metadata: which edge, t-range,
                                          type -- consumed by
                                          door_window_mesh_generator.py)

Approach:
    For each wall edge, project every door/window center onto that
    edge's line. If the projection falls within the edge span (plus a
    small tolerance) and within `MAX_ASSIGN_DIST` of the edge, the
    opening belongs to that wall.

    Each wall edge is then built not as one solid box, but as a set of
    solid boxes: the full-height boxes covering the parts of the wall
    with no opening, plus, under each opening, only the solid bands
    above/below it (lintel above a door, sill+lintel around a window).
    This is done by explicit box construction rather than CSG boolean
    subtraction, so it doesn't depend on a boolean mesh backend
    (blender/manifold) being installed.

Units: assumes plan pixel coordinates map 1:1 to world units after
your existing scale factor -- adjust WALL_HEIGHT / DOOR_HEIGHT /
WINDOW_* to your project's real scale if pixels != mm/cm.

Usage:
    python create_wall_mesh.py outputs/vector_wall_graph_v3.json \
                                outputs/wall_segments.json \
                                outputs/meshes/vector_walls.obj
"""

import json
import math
import os
import sys

import numpy as np
import trimesh

WALL_HEIGHT = 260.0
DOOR_HEIGHT = 210.0
WINDOW_SILL = 90.0
WINDOW_HEIGHT = 120.0
MAX_ASSIGN_DIST = 30.0     # px, max perpendicular distance opening->wall
EDGE_TOLERANCE = 10.0      # px, allowed overshoot past edge endpoints


def project_point_to_segment(p, a, b):
    """Return (t, perp_dist) where t is the 0..len(ab) distance along
    ab of the projection of p, and perp_dist is the perpendicular
    distance from p to the line."""
    ax, ay = a
    bx, by = b
    px, py = p
    abx, aby = bx - ax, by - ay
    seg_len = math.hypot(abx, aby)
    if seg_len < 1e-6:
        return 0.0, math.hypot(px - ax, py - ay), seg_len
    ux, uy = abx / seg_len, aby / seg_len
    t = (px - ax) * ux + (py - ay) * uy
    proj_x, proj_y = ax + ux * t, ay + uy * t
    perp = math.hypot(px - proj_x, py - proj_y)
    return t, perp, seg_len


def assign_openings_to_edges(nodes, edges, openings, max_assign_dist=MAX_ASSIGN_DIST):
    """openings: list of {"id", "bbox", "center", "kind"}
    returns dict edge_key -> list of {t0, t1, kind, id}"""
    assigned = {}
    for op in openings:
        best = None  # (perp, edge_key, t0, t1) -- best found regardless of threshold
        cx, cy = op["center"]
        x1, y1, x2, y2 = op["bbox"]
        width = max(x2 - x1, y2 - y1)  # opening span along its long axis

        for u, v in edges:
            a, b = nodes[u], nodes[v]
            t, perp, seg_len = project_point_to_segment((cx, cy), a, b)
            if t < -EDGE_TOLERANCE or t > seg_len + EDGE_TOLERANCE:
                continue
            t0 = max(0.0, t - width / 2)
            t1 = min(seg_len, t + width / 2)
            if best is None or perp < best[0]:
                best = (perp, (u, v), t0, t1)

        if best is not None and best[0] <= max_assign_dist:
            _, key, t0, t1 = best
            assigned.setdefault(key, []).append(
                {"t0": t0, "t1": t1, "kind": op["kind"], "id": op["id"]}
            )
        elif best is not None:
            print(f"[create_wall_mesh] WARNING: {op['kind']} id={op['id']} "
                  f"nearest wall edge is {best[0]:.1f}px away, exceeds "
                  f"max_assign_dist={max_assign_dist}. Skipped -- try "
                  f"max_assign_dist >= {int(best[0]) + 5}.")
        else:
            print(f"[create_wall_mesh] WARNING: {op['kind']} id={op['id']} "
                  f"has no wall edges within its own endpoint span at all. Skipped.")
    return assigned


def make_box(t0, t1, z0, z1, edge_dir, edge_normal, origin, thickness):
    """Build a box mesh spanning [t0,t1] along edge_dir, [z0,z1] in height,
    centered on the wall centerline with the given thickness."""
    if t1 - t0 < 1e-6 or z1 - z0 < 1e-6:
        return None
    ex, ey = edge_dir
    nx, ny = edge_normal
    ox, oy = origin

    p0 = np.array([ox + ex * t0, oy + ey * t0])
    p1 = np.array([ox + ex * t1, oy + ey * t1])

    half_th = thickness / 2.0
    corners_xy = [
        p0 - np.array([nx, ny]) * half_th,
        p1 - np.array([nx, ny]) * half_th,
        p1 + np.array([nx, ny]) * half_th,
        p0 + np.array([nx, ny]) * half_th,
    ]

    verts = []
    for z in (z0, z1):
        for cx, cy in corners_xy:
            verts.append([cx, cy, z])
    verts = np.array(verts)

    # bottom: 0,1,2,3  top: 4,5,6,7
    faces = [
        [0, 1, 2], [0, 2, 3],          # bottom
        [4, 6, 5], [4, 7, 6],          # top
        [0, 4, 5], [0, 5, 1],          # side 0-1
        [1, 5, 6], [1, 6, 2],          # side 1-2
        [2, 6, 7], [2, 7, 3],          # side 2-3
        [3, 7, 4], [3, 4, 0],          # side 3-0
    ]
    return trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)


def build_wall_edge_mesh(a, b, thickness, openings_on_edge):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    if length < 1e-6:
        return [], []

    ex, ey = (bx - ax) / length, (by - ay) / length   # edge direction
    nx, ny = -ey, ex                                    # edge normal

    boxes = []
    opening_meta = []

    if not openings_on_edge:
        box = make_box(0, length, 0, WALL_HEIGHT, (ex, ey), (nx, ny), a, thickness)
        if box is not None:
            boxes.append(box)
        return boxes, opening_meta

    openings_on_edge = sorted(openings_on_edge, key=lambda o: o["t0"])

    cursor = 0.0
    for op in openings_on_edge:
        t0, t1 = max(op["t0"], cursor), max(op["t1"], cursor)
        if t0 > cursor:
            # solid segment before this opening, full height
            box = make_box(cursor, t0, 0, WALL_HEIGHT, (ex, ey), (nx, ny), a, thickness)
            if box is not None:
                boxes.append(box)

        if op["kind"] == "door":
            # open from floor to DOOR_HEIGHT; solid lintel above
            lintel = make_box(t0, t1, DOOR_HEIGHT, WALL_HEIGHT, (ex, ey), (nx, ny), a, thickness)
            if lintel is not None:
                boxes.append(lintel)
        else:  # window
            sill = make_box(t0, t1, 0, WINDOW_SILL, (ex, ey), (nx, ny), a, thickness)
            head = make_box(t0, t1, WINDOW_SILL + WINDOW_HEIGHT, WALL_HEIGHT,
                             (ex, ey), (nx, ny), a, thickness)
            if sill is not None:
                boxes.append(sill)
            if head is not None:
                boxes.append(head)

        opening_meta.append({
            "id": op["id"], "kind": op["kind"],
            "t0": t0, "t1": t1,
            "edge_origin": list(a), "edge_dir": [ex, ey], "edge_normal": [nx, ny],
            "thickness": thickness,
            "sill_height": WINDOW_SILL if op["kind"] == "window" else 0.0,
            "head_height": (WINDOW_SILL + WINDOW_HEIGHT) if op["kind"] == "window" else DOOR_HEIGHT,
        })
        cursor = t1

    if cursor < length:
        box = make_box(cursor, length, 0, WALL_HEIGHT, (ex, ey), (nx, ny), a, thickness)
        if box is not None:
            boxes.append(box)

    return boxes, opening_meta


def main(graph_path, segments_path, out_obj_path, max_assign_dist=MAX_ASSIGN_DIST):
    with open(graph_path) as f:
        graph = json.load(f)
    with open(segments_path) as f:
        segs = json.load(f)

    nodes = {n["id"]: (n["x"], n["y"]) for n in graph["nodes"]}
    edges = [tuple(e) for e in graph["edges"]]
    edge_thickness = graph.get("edge_thickness", {})

    openings = []
    for d in segs.get("doors", []):
        openings.append({"id": f"door_{d['id']}", "bbox": d["bbox"],
                          "center": d["center"], "kind": "door"})
    for w in segs.get("windows", []):
        openings.append({"id": f"window_{w['id']}", "bbox": w["bbox"],
                          "center": w["center"], "kind": "window"})

    assigned = assign_openings_to_edges(nodes, edges, openings, max_assign_dist)

    all_boxes = []
    all_opening_meta = []
    for u, v in edges:
        key = f"{u}-{v}"
        thickness = edge_thickness.get(key, edge_thickness.get(f"{v}-{u}", 12.0))
        ops = assigned.get((u, v), []) + assigned.get((v, u), [])
        boxes, meta = build_wall_edge_mesh(nodes[u], nodes[v], thickness, ops)
        all_boxes.extend(boxes)
        for m in meta:
            m["edge"] = key
        all_opening_meta.extend(meta)

    if not all_boxes:
        raise RuntimeError("No wall geometry generated -- check input graph.")

    wall_mesh = trimesh.util.concatenate(all_boxes)

    os.makedirs(os.path.dirname(out_obj_path), exist_ok=True)
    wall_mesh.export(out_obj_path)

    meta_path = os.path.join(os.path.dirname(out_obj_path), "wall_openings.json")
    with open(meta_path, "w") as f:
        json.dump(all_opening_meta, f, indent=2)

    print(f"[create_wall_mesh] {len(edges)} edges -> {len(all_boxes)} boxes "
          f"-> {len(wall_mesh.vertices)} verts / {len(wall_mesh.faces)} faces")
    print(f"[create_wall_mesh] {len(all_opening_meta)} openings cut "
          f"(of {len(openings)} detected door/window boxes)")
    print(f"[create_wall_mesh] wrote {out_obj_path} and {meta_path}")


if __name__ == "__main__":
    graph_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/vector_wall_graph_v3.json"
    segments_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/wall_segments.json"
    out_obj_path = sys.argv[3] if len(sys.argv) > 3 else "outputs/meshes/vector_walls.obj"
    max_assign_dist = float(sys.argv[4]) if len(sys.argv) > 4 else MAX_ASSIGN_DIST
    main(graph_path, segments_path, out_obj_path, max_assign_dist)