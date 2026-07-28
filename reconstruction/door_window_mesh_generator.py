"""
door_window_mesh_generator.py

Stage: wall openings -> door/window panel meshes

Input:
    outputs/meshes/wall_openings.json   (from create_wall_mesh.py)

Output:
    outputs/meshes/doors.obj
    outputs/meshes/windows.obj

Doors and windows are now written as SEPARATE files (previously
combined into one doors_windows.obj), so convert_to_glb.py can give
them different materials/colors -- e.g. doors in brown, windows in
glass-blue. If one category has zero detections, its file is simply
not written (downstream stages already handle missing optional parts).

Usage:
    python door_window_mesh_generator.py outputs/meshes/wall_openings.json \
                                          outputs/meshes/doors.obj \
                                          outputs/meshes/windows.obj
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


def build_panels(openings, kind):
    panels = []
    for op in openings:
        if op["kind"] != kind:
            continue
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
    return panels


def main(openings_path, doors_out_path, windows_out_path):
    with open(openings_path) as f:
        openings = json.load(f)

    for kind, out_path in [("door", doors_out_path), ("window", windows_out_path)]:
        panels = build_panels(openings, kind)
        if not panels:
            print(f"[door_window_mesh_generator] no {kind}s found, skipping {out_path}")
            continue
        mesh = trimesh.util.concatenate(panels)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        mesh.export(out_path)
        print(f"[door_window_mesh_generator] {len(panels)} {kind} panel(s) -> {out_path}")


if __name__ == "__main__":
    openings_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/meshes/wall_openings.json"
    doors_out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/meshes/doors.obj"
    windows_out_path = sys.argv[3] if len(sys.argv) > 3 else "outputs/meshes/windows.obj"
    main(openings_path, doors_out_path, windows_out_path)