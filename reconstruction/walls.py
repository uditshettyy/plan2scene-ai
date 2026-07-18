import json
import open3d as o3d

INPUT_FILE = "outputs/geometry/wall_segments.json"

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

mesh = o3d.geometry.TriangleMesh()

WALL_HEIGHT = 300  # pixels for now

for wall in walls:

    start = wall["start"]
    end = wall["end"]
    thickness = wall["thickness"]

    x1, y1 = start
    x2, y2 = end

    if wall["orientation"] == "horizontal":

        box = o3d.geometry.TriangleMesh.create_box(
            width=x2 - x1,
            height=thickness,
            depth=WALL_HEIGHT
        )

        box.translate((x1, y1, 0))

    else:

        box = o3d.geometry.TriangleMesh.create_box(
            width=thickness,
            height=y2 - y1,
            depth=WALL_HEIGHT
        )

        box.translate((x1, y1, 0))

    mesh += box

mesh.compute_vertex_normals()

o3d.visualization.draw_geometries([mesh])