"""
stair_mesh_generator.py

Stage: stairs detections -> 3D stair geometry

Input:
    outputs/wall_segments.json   (uses the "stairs" list -- bbox per run)

Output:
    outputs/meshes/stairs.obj

Builds a straight-run staircase (one box per step) filling the
detected bounding box, running along the box's long axis, rising from
z=0 to WALL_HEIGHT (i.e. reaching the floor above). This replaces
treating stair detections as generic wall extrusion.

Assumptions (flagged clearly since these can't be inferred from a 2D
bbox alone):
  * the box's long axis is the direction of ascent
  * the run rises the full inter-floor height (WALL_HEIGHT)
  * step count is derived from a target step depth, not detected

Usage:
    python stair_mesh_generator.py outputs/wall_segments.json outputs/meshes/stairs.obj
"""

import json
import os
import sys

import numpy as np
import trimesh

WALL_HEIGHT = 260.0          # total rise, matches create_wall_mesh.py
TARGET_STEP_DEPTH = 28.0     # px, desired tread depth -> determines step count
MIN_STEPS = 3
MAX_STEPS = 24


def make_step_box(x0, x1, y0, y1, z0, z1):
    verts = np.array([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ])
    faces = np.array([
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3],
        [3, 7, 4], [3, 4, 0],
    ])
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def build_staircase(bbox):
    x1, y1, x2, y2 = bbox
    w, h = abs(x2 - x1), abs(y2 - y1)
    ascends_along_x = w >= h

    run_length = max(w, h)
    n_steps = int(round(run_length / TARGET_STEP_DEPTH))
    n_steps = max(MIN_STEPS, min(MAX_STEPS, n_steps))

    step_depth = run_length / n_steps
    step_rise = WALL_HEIGHT / n_steps

    boxes = []
    for i in range(n_steps):
        z0, z1 = 0.0, step_rise * (i + 1)   # solid from floor up to this tread
        if ascends_along_x:
            sx0 = min(x1, x2) + i * step_depth
            sx1 = sx0 + step_depth
            boxes.append(make_step_box(sx0, sx1, min(y1, y2), max(y1, y2), z0, z1))
        else:
            sy0 = min(y1, y2) + i * step_depth
            sy1 = sy0 + step_depth
            boxes.append(make_step_box(min(x1, x2), max(x1, x2), sy0, sy1, z0, z1))

    return trimesh.util.concatenate(boxes), n_steps


def main(segments_path, out_path):
    with open(segments_path) as f:
        segs = json.load(f)

    stairs = segs.get("stairs", [])
    if not stairs:
        print("[stair_mesh_generator] no stairs detected, nothing to generate")
        return

    meshes = []
    for s in stairs:
        mesh, n_steps = build_staircase(s["bbox"])
        meshes.append(mesh)
        print(f"[stair_mesh_generator] stairs id={s['id']}: {n_steps} steps")

    combined = trimesh.util.concatenate(meshes)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    combined.export(out_path)
    print(f"[stair_mesh_generator] {len(stairs)} stair run(s) -> {out_path}")


if __name__ == "__main__":
    segments_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/wall_segments.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/meshes/stairs.obj"
    main(segments_path, out_path)