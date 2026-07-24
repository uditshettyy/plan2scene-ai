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
    "floor":         ("vector_room_floors.obj", [214, 200, 180, 255]),
    "walls":         ("vector_walls.obj",       [235, 235, 230, 255]),
    "doors_windows": ("doors_windows.obj",      [120, 150, 200, 180]),
    "stairs":        ("stairs.obj",             [160, 160, 165, 255]),
}


def colorize(mesh, rgba):
    color = np.array(rgba, dtype=np.uint8)
    mesh.visual = trimesh.visual.ColorVisuals(
        mesh, face_colors=np.tile(color, (len(mesh.faces), 1))
    )
    return mesh


def main(meshes_dir, out_path):
    scene = trimesh.Scene()
    loaded = []
    for name, (filename, rgba) in PART_STYLE.items():
        path = os.path.join(meshes_dir, filename)
        if not os.path.exists(path):
            print(f"[convert_to_glb] WARNING: {filename} not found, skipping ({name})")
            continue
        mesh = trimesh.load(path, process=False)
        colorize(mesh, rgba)
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        loaded.append(name)

    if not loaded:
        raise RuntimeError("No mesh parts found -- run earlier pipeline stages first.")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.export(out_path)

    total_verts = sum(len(g.vertices) for g in scene.geometry.values())
    total_faces = sum(len(g.faces) for g in scene.geometry.values())
    print(f"[convert_to_glb] parts included: {loaded}")
    print(f"[convert_to_glb] {total_verts} verts / {total_faces} faces -> {out_path}")


if __name__ == "__main__":
    meshes_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/meshes"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/plan2scene_vector_house.glb"
    main(meshes_dir, out_path)