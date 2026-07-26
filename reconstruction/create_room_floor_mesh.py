"""
create_vector_room_floor_mesh.py

Stage: room polygons -> floor mesh

Input:  outputs/vector_rooms.json   (from vector_room_face_extractor.py)
Output: outputs/meshes/vector_room_floors.obj

Since vector_room_face_extractor.py now guarantees clean, non-self-
intersecting, non-duplicated polygons (one per actual room, by
construction of the planar face traversal), triangulation here is
straightforward -- no special-casing for nested/duplicate polygons is
needed, unlike with the old DFS-based room list.

Usage:
    python create_room_floor_mesh.py outputs/vector_rooms.json outputs/meshes/vector_room_floors.obj
"""

import json
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate as shapely_triangulate


def triangulate_room(polygon_pts):
    poly = Polygon(polygon_pts)
    if not poly.is_valid:
        poly = poly.buffer(0)  # attempt self-repair for near-valid polygons
    if poly.is_empty or poly.area < 1.0:
        return None

    # constrained triangulation: use shapely's triangulate on the
    # polygon's vertices, then keep only triangles whose centroid
    # falls inside the original polygon (this correctly handles
    # concave rooms, which naive fan triangulation does not).
    candidate_tris = shapely_triangulate(poly)
    kept = [t for t in candidate_tris if poly.contains(t.centroid)]
    if not kept:
        return None

    verts = []
    faces = []
    for tri in kept:
        coords = list(tri.exterior.coords)[:3]
        base = len(verts)
        for x, y in coords:
            verts.append([x, y, 0.0])
        faces.append([base, base + 1, base + 2])

    return trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=False)


def main(rooms_path, out_path, wall_segments_path=None):
    with open(rooms_path) as f:
        data = json.load(f)

    rooms = data["rooms"]
    used_fallback = False

    if not rooms and wall_segments_path and os.path.exists(wall_segments_path):
        with open(wall_segments_path) as f:
            segs = json.load(f)
        room_boxes = segs.get("room_boxes", [])
        if room_boxes:
            used_fallback = True
            print(f"[create_room_floor_mesh] wall-graph produced 0 rooms -- "
                  f"falling back to {len(room_boxes)} raw YOLO 'room' boxes "
                  f"as approximate rectangular floors. These are NOT precise "
                  f"room polygons (no shared-wall trimming between adjacent "
                  f"rooms, so floors may overlap slightly) -- fix the "
                  f"underlying wall detection/graph for accurate rooms.")
            rooms = [{"polygon": [
                [b["bbox"][0], b["bbox"][1]], [b["bbox"][2], b["bbox"][1]],
                [b["bbox"][2], b["bbox"][3]], [b["bbox"][0], b["bbox"][3]],
            ]} for b in room_boxes]

    meshes = []
    skipped = 0
    for room in rooms:
        mesh = triangulate_room(room["polygon"])
        if mesh is None:
            skipped += 1
            continue
        meshes.append(mesh)

    if not meshes:
        print(f"[create_room_floor_mesh] WARNING: no valid room polygons "
              f"({len(rooms)} room(s) in input, {skipped} degenerate), and "
              f"no usable fallback. Skipping floor mesh output (no {out_path} "
              f"written) so the rest of the pipeline can still run.")
        return

    combined = trimesh.util.concatenate(meshes)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    combined.export(out_path)

    source = "YOLO room-box fallback" if used_fallback else "wall-graph face extraction"
    print(f"[create_room_floor_mesh] {len(rooms)} room polygons ({source}) -> "
          f"{len(meshes)} floor meshes ({skipped} skipped as degenerate)")
    print(f"[create_room_floor_mesh] {len(combined.vertices)} verts / "
          f"{len(combined.faces)} faces -> {out_path}")


if __name__ == "__main__":
    rooms_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/vector_rooms.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/meshes/vector_room_floors.obj"
    wall_segments_path = sys.argv[3] if len(sys.argv) > 3 else None
    main(rooms_path, out_path, wall_segments_path)
