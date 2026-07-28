"""
convert_to_glb.py

Stage: mesh parts -> textured/colored GLB for the web viewer

Input:
    outputs/meshes/vector_room_floors.obj
    outputs/meshes/vector_walls.obj
    outputs/meshes/doors_windows.obj
    outputs/meshes/stairs.obj

Output:
    outputs/plan2scene_vector_house.glb

Rebuilds the scene directly from the individual part meshes (rather
than re-loading the combined .obj from combine_final_house.py) so
each part keeps its own named node and a distinct material -- OBJ's
group/material support is inconsistent across loaders, GLB's is not,
so this is done once, directly into GLB.

Usage:
    python convert_to_glb.py outputs/meshes outputs/plan2scene_vector_house.glb
"""

import os
import sys

import numpy as np
import trimesh

PART_STYLE = {
    # name -> (filename, RGBA color 0-255)
    "floor":   ("vector_room_floors.obj", [214, 200, 180, 255]),
    "walls":   ("vector_walls.obj",       [235, 235, 230, 255]),
    "doors":   ("doors.obj",              [101, 67, 33, 255]),    # wood brown
    "windows": ("windows.obj",            [140, 180, 210, 160]),  # glass blue, semi-transparent
    "stairs":  ("stairs.obj",             [160, 160, 165, 255]),
}


def colorize(mesh, rgba):
    color = np.array(rgba, dtype=np.uint8)
    mesh.visual = trimesh.visual.ColorVisuals(
        mesh, face_colors=np.tile(color, (len(mesh.faces), 1))
    )
    return mesh


def zup_to_yup_centered_transform(center_x, center_y):
    """
    Our pipeline builds geometry in a Z-up convention: X/Y are the floor
    plan's horizontal position (raw pixel coordinates from the source
    image, which can run into the thousands), Z is height off the floor
    (0 to WALL_HEIGHT, e.g. 0-260).

    glTF (and therefore Three.js/React Three Fiber) requires Y-up:
    trimesh's GLB exporter does NOT do this conversion automatically --
    it writes X/Y/Z straight through. Without this fix, wall "height"
    lands on the depth axis and the raw pixel X/Y (up to ~3800 units)
    lands on the "up" axis, producing tall diagonal slivers instead of
    a normal-looking building.

    This returns a single 4x4 transform that:
      1. Translates so the horizontal (X, Y-pixel) center of the whole
         model sits at the origin -- fixes "not in the middle".
      2. Rotates -90 degrees about X, which maps old Z (height) -> new Y
         (up) and old Y (pixel row) -> new -Z (depth), i.e. proper Z-up
         to Y-up conversion.
    """
    translate = np.eye(4)
    translate[0, 3] = -center_x
    translate[1, 3] = -center_y

    theta = -np.pi / 2
    c, s = np.cos(theta), np.sin(theta)
    rotate = np.eye(4)
    rotate[1, 1] = c
    rotate[1, 2] = -s
    rotate[2, 1] = s
    rotate[2, 2] = c

    return rotate @ translate


def main(meshes_dir, out_path):
    raw_meshes = {}
    for name, (filename, rgba) in PART_STYLE.items():
        path = os.path.join(meshes_dir, filename)
        if not os.path.exists(path):
            print(f"[convert_to_glb] WARNING: {filename} not found, skipping ({name})")
            continue
        mesh = trimesh.load(path, process=False)
        colorize(mesh, rgba)
        raw_meshes[name] = mesh

    if not raw_meshes:
        raise RuntimeError("No mesh parts found -- run earlier pipeline stages first.")

    # Combined bounding box across ALL parts (in original Z-up pixel
    # space) so every part gets centered consistently relative to the
    # whole model, not each part centered on itself.
    all_bounds = np.array([m.bounds for m in raw_meshes.values()])  # (N, 2, 3)
    overall_min = all_bounds[:, 0, :].min(axis=0)
    overall_max = all_bounds[:, 1, :].max(axis=0)
    center_x = (overall_min[0] + overall_max[0]) / 2
    center_y = (overall_min[1] + overall_max[1]) / 2

    transform = zup_to_yup_centered_transform(center_x, center_y)

    scene = trimesh.Scene()
    loaded = []
    for name, mesh in raw_meshes.items():
        mesh.apply_transform(transform)
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        loaded.append(name)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.export(out_path)

    total_verts = sum(len(g.vertices) for g in scene.geometry.values())
    total_faces = sum(len(g.faces) for g in scene.geometry.values())
    print(f"[convert_to_glb] parts included: {loaded}")
    print(f"[convert_to_glb] centered at pixel-space ({center_x:.0f}, {center_y:.0f}), "
          f"converted Z-up -> Y-up")
    print(f"[convert_to_glb] {total_verts} verts / {total_faces} faces -> {out_path}")


if __name__ == "__main__":
    meshes_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/meshes"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/plan2scene_vector_house.glb"
    main(meshes_dir, out_path)