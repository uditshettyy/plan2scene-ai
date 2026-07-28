"""
combine_final_house.py

Stage: combine all generated meshes -> single final model

Input (each optional -- missing files are skipped with a warning, so
the pipeline still produces a model even if e.g. no stairs were
detected):
    outputs/meshes/vector_room_floors.obj
    outputs/meshes/vector_walls.obj
    outputs/meshes/doors_windows.obj
    outputs/meshes/stairs.obj

Output:
    outputs/plan2scene_vector_house.obj

Meshes are kept as separate geometries within one exported scene
(rather than merged into one flat mesh) so the frontend can assign
different materials per part (floor / wall / door / window / stairs)
and, later, toggle visibility per layer.

Usage:
    python combine_final_house.py outputs/meshes outputs/plan2scene_vector_house.obj
"""

import os
import sys

import trimesh

PARTS = {
    "floor": "vector_room_floors.obj",
    "walls": "vector_walls.obj",
    "doors": "doors.obj",
    "windows": "windows.obj",
    "stairs": "stairs.obj",
}


def main(meshes_dir, out_path):
    scene = trimesh.Scene()
    loaded = []
    for name, filename in PARTS.items():
        path = os.path.join(meshes_dir, filename)
        if not os.path.exists(path):
            print(f"[combine_final_house] WARNING: {filename} not found, skipping ({name})")
            continue
        mesh = trimesh.load(path, process=False)
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        loaded.append(name)

    if not loaded:
        raise RuntimeError("No mesh parts found to combine -- run earlier pipeline stages first.")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.export(out_path)

    total_verts = sum(len(g.vertices) for g in scene.geometry.values())
    total_faces = sum(len(g.faces) for g in scene.geometry.values())
    print(f"[combine_final_house] combined parts: {loaded}")
    print(f"[combine_final_house] {total_verts} verts / {total_faces} faces -> {out_path}")


if __name__ == "__main__":
    meshes_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/meshes"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/plan2scene_vector_house.obj"
    main(meshes_dir, out_path)