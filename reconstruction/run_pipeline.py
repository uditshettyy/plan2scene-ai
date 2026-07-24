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

import json
import os
import shutil
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


def filter_left_detections(in_path, out_path):
    """Filters YOLO detections to only keep elements in the left half (x < 2000)."""
    with open(in_path, "r") as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        detections = data.get("detections", data.get("boxes", []))
    else:
        detections = data

    filtered = []
    for d in detections:
        bbox = d.get("bbox", d)
        if isinstance(bbox, dict):
            x2 = float(bbox.get("x2", bbox.get("xmax", 0)))
        else:
            x2 = float(bbox[2])
        
        if x2 < 2000:
            filtered.append(d)

    with open(out_path, "w") as f:
        json.dump(filtered, f, indent=4)
    print(f"[run_pipeline] Filtered {len(detections)} detections -> {len(filtered)} in floor plan (left) region.")


def main(detections_path, out_dir, snap_tol=6.0, bridge_tol=40.0, max_assign_dist=30.0):
    meshes_dir = os.path.join(out_dir, "meshes")
    os.makedirs(meshes_dir, exist_ok=True)

    filtered_detections = os.path.join(out_dir, "filtered_v2_detections.json")
    filter_left_detections(detections_path, filtered_detections)

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

    run([py, os.path.join(HERE, "extract_wall_segments.py"), filtered_detections, wall_segments])
    run([py, os.path.join(HERE, "build_connected_wall_graph.py"), wall_segments, wall_graph,
         snap_tol, bridge_tol])
    run([py, os.path.join(HERE, "vector_room_face_extractor.py"), wall_graph, rooms,
         snap_tol, bridge_tol])
    run([py, os.path.join(HERE, "create_wall_mesh.py"), wall_graph, wall_segments, walls_obj,
         max_assign_dist])
    run([py, os.path.join(HERE, "door_window_mesh_generator.py"),
         os.path.join(meshes_dir, "wall_openings.json"), doors_windows_obj])
    run([py, os.path.join(HERE, "stair_mesh_generator.py"), wall_segments, stairs_obj])
    run([py, os.path.join(HERE, "create_room_floor_mesh.py"), rooms, floors_obj])
    run([py, os.path.join(HERE, "combine_final_house.py"), meshes_dir, combined_obj])
    run([py, os.path.join(HERE, "convert_to_glb.py"), meshes_dir, combined_glb])

    print(f"\n[run_pipeline] DONE. Final model: {combined_glb}")
    
    # Auto-copy final GLB to frontend assets
    frontend_glb = os.path.join(HERE, "..", "frontend", "public", "models", "plan2scene_vector_house.glb")
    os.makedirs(os.path.dirname(frontend_glb), exist_ok=True)
    try:
        shutil.copy(combined_glb, frontend_glb)
        print(f"[run_pipeline] Automatically copied final GLB to frontend assets: {frontend_glb}")
    except Exception as e:
        print(f"[run_pipeline] WARNING: Failed to copy GLB to frontend: {e}")


if __name__ == "__main__":
    detections_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/v2_detections.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    snap_tol = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
    bridge_tol = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
    max_assign_dist = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
    main(detections_path, out_dir, snap_tol, bridge_tol, max_assign_dist)