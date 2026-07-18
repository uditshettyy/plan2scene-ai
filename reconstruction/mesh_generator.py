import json
import open3d as o3d

INPUT_FILE = "outputs/geometry/optimized_walls.json"

WALL_HEIGHT = 120
FLOOR_THICKNESS = 5

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

mesh = o3d.geometry.TriangleMesh()

min_x = float("inf")
min_y = float("inf")
max_x = float("-inf")
max_y = float("-inf")

for wall in walls:

    sx, sy = wall["start"]
    ex, ey = wall["end"]
    t = wall["thickness"]

    min_x = min(min_x, sx, ex)
    min_y = min(min_y, sy, ey)
    max_x = max(max_x, sx, ex)
    max_y = max(max_y, sy, ey)

    if wall["orientation"] == "horizontal":

        width = ex - sx

        box = o3d.geometry.TriangleMesh.create_box(
            width=width,
            height=t,
            depth=WALL_HEIGHT
        )

        box.translate((sx, sy - t / 2, 0))

    else:

        height = ey - sy

        box = o3d.geometry.TriangleMesh.create_box(
            width=t,
            height=height,
            depth=WALL_HEIGHT
        )

        box.translate((sx - t / 2, sy, 0))

    mesh += box


floor = o3d.geometry.TriangleMesh.create_box(
    width=max_x - min_x,
    height=max_y - min_y,
    depth=FLOOR_THICKNESS
)

floor.translate((min_x, min_y, -FLOOR_THICKNESS))

mesh += floor

mesh.compute_vertex_normals()

o3d.visualization.draw_geometries([mesh])