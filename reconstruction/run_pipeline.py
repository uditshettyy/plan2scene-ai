"""
run_pipeline.py

Runs the full Plan2Scene-AI pipeline, detection output -> final GLB:

    v2_detections.json
        -> extract_wall_segments.py       -> wall_segments.json
        -> build_connected_wall_graph.py  -> vector_wall_graph_v3.json
        -> vector_room_face_extractor.py  -> vector_rooms.json
        -> create_wall_mesh.py            -> meshes/vector_walls.obj (+ wall_openings.json)
        -> door_window_mesh_generator.py  -> meshes/doors_windows.obj
        -> stair_mesh_generator.py        -> meshes/stairs.obj
        -> create_room_floor_mesh.py      -> meshes/vector_room_floors.obj
        -> combine_final_house.py         -> plan2scene_vector_house.obj
        -> convert_to_glb.py              -> plan2scene_vector_house.glb

Each stage is invoked as a subprocess (matching how you already run
individual stages), so any stage can still be re-run standalone while
debugging.

Usage:
    python run_pipeline.py [detections.json] [outputs_dir] [snap_tol] [bridge_tol] [max_assign_dist]

    snap_tol, bridge_tol, max_assign_dist are in the same pixel units
    as your detections. If build_connected_wall_graph.py reports
    remaining components with a nearest-gap distance, or create_wall_mesh.py
    reports doors/windows too far from any wall, re-run with those
    numbers raised past what it printed.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    cmd = [str(c) for c in cmd]
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[run_pipeline] stage failed: {' '.join(cmd)}")
        sys.exit(result.returncode)


def main(detections_path, out_dir, snap_tol=6.0, bridge_tol=90.0, max_assign_dist=80.0):
    meshes_dir = os.path.join(out_dir, "meshes")
    os.makedirs(meshes_dir, exist_ok=True)

    wall_segments = os.path.join(out_dir, "wall_segments.json")
    wall_graph = os.path.join(out_dir, "vector_wall_graph_v3.json")
    rooms = os.path.join(out_dir, "vector_rooms.json")
    walls_obj = os.path.join(meshes_dir, "vector_walls.obj")
    doors_windows_obj = os.path.join(meshes_dir, "doors_windows.obj")
    stairs_obj = os.path.join(meshes_dir, "stairs.obj")
    floors_obj = os.path.join(meshes_dir, "vector_room_floors.obj")
    combined_obj = os.path.join(out_dir, "plan2scene_vector_house.obj")
    combined_glb = os.path.join(out_dir, "plan2scene_vector_house.glb")

    py = sys.executable

    run([py, os.path.join(HERE, "extract_wall_segments.py"), detections_path, wall_segments])
    run([py, os.path.join(HERE, "build_connected_wall_graph.py"), wall_segments, wall_graph,
         snap_tol, bridge_tol])
    run([py, os.path.join(HERE, "vector_room_face_extractor.py"), wall_graph, rooms,
         snap_tol, bridge_tol])
    run([py, os.path.join(HERE, "create_wall_mesh.py"), wall_graph, wall_segments, walls_obj,
         max_assign_dist])
    run([py, os.path.join(HERE, "door_window_mesh_generator.py"),
         os.path.join(meshes_dir, "wall_openings.json"), doors_windows_obj])
    run([py, os.path.join(HERE, "stair_mesh_generator.py"), wall_segments, stairs_obj])
    run([py, os.path.join(HERE, "create_room_floor_mesh.py"), rooms, floors_obj, wall_segments])
    run([py, os.path.join(HERE, "combine_final_house.py"), meshes_dir, combined_obj])
    run([py, os.path.join(HERE, "convert_to_glb.py"), meshes_dir, combined_glb])

    print(f"\n[run_pipeline] DONE. Final model: {combined_glb}")
    print(f"[run_pipeline] Copy/symlink this into your frontend's public/models/ "
          f"folder for ModelViewer.jsx to load it.")


if __name__ == "__main__":
    detections_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/v2_detections.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    snap_tol = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
    bridge_tol = float(sys.argv[4]) if len(sys.argv) > 4 else 90.0
    max_assign_dist = float(sys.argv[5]) if len(sys.argv) > 5 else 80.0
    main(detections_path, out_dir, snap_tol, bridge_tol, max_assign_dist)