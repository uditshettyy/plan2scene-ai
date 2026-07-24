"""
door_window_mesh_generator.py

Stage: wall openings -> door/window panel meshes

Input:
    outputs/meshes/wall_openings.json   (from create_wall_mesh.py)

Output:
    outputs/meshes/doors_windows.obj

For each opening, builds a thin flat panel (the door slab, or the
window glazing) sized to the opening and centered in the wall
thickness. This is intentionally simple geometry -- a frame + panel,
not modeled hardware -- matching the level of detail of the rest of
the current pipeline. It's a natural place to later swap in actual
door/window asset meshes keyed by `kind`.

Usage:
    python door_window_mesh_generator.py outputs/meshes/wall_openings.json \
                                          outputs/meshes/doors_windows.obj
"""

import json
import os
import sys

import numpy as np
import trimesh

PANEL_THICKNESS_FRACTION = 0.5   # panel thickness as fraction of wall thickness
FRAME_MARGIN = 3.0                # px, frame border width around the panel


def make_panel(t0, t1, z0, z1, origin, edge_dir, edge_normal, wall_thickness):
    ex, ey = edge_dir
    nx, ny = edge_normal
    ox, oy = origin

    p0 = np.array([ox + ex * t0, oy + ey * t0])
    p1 = np.array([ox + ex * t1, oy + ey * t1])

    half_th = (wall_thickness * PANEL_THICKNESS_FRACTION) / 2.0
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

    faces = [
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3],
        [3, 7, 4], [3, 4, 0],
    ]
    return trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)


def main(openings_path, out_path):
    with open(openings_path) as f:
        openings = json.load(f)

    panels = []
    for op in openings:
        t0 = op["t0"] + FRAME_MARGIN
        t1 = op["t1"] - FRAME_MARGIN
        if t1 <= t0:
            continue
        z0 = op["sill_height"] if op["kind"] == "window" else 0.0
        z1 = op["head_height"]

        panel = make_panel(
            t0, t1, z0, z1,
            origin=op["edge_origin"], edge_dir=op["edge_dir"],
            edge_normal=op["edge_normal"], wall_thickness=op["thickness"],
        )
        panels.append(panel)

    if not panels:
        print("[door_window_mesh_generator] no openings found, nothing to generate")
        return

    mesh = trimesh.util.concatenate(panels)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    mesh.export(out_path)
    print(f"[door_window_mesh_generator] {len(panels)} panels -> {out_path}")


if __name__ == "__main__":
    openings_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/meshes/wall_openings.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/meshes/doors_windows.obj"
    main(openings_path, out_path)