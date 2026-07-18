import json
import open3d as o3d

INPUT_FILE = "outputs/geometry/optimized_walls.json"

with open(INPUT_FILE, "r") as f:
    walls = json.load(f)

min_x = float("inf")
min_y = float("inf")
max_x = float("-inf")
max_y = float("-inf")

for wall in walls:

    sx, sy = wall["start"]
    ex, ey = wall["end"]

    min_x = min(min_x, sx, ex)
    min_y = min(min_y, sy, ey)

    max_x = max(max_x, sx, ex)
    max_y = max(max_y, sy, ey)

FLOOR_THICKNESS = 5

floor = o3d.geometry.TriangleMesh.create_box(
    width=max_x - min_x,
    height=max_y - min_y,
    depth=FLOOR_THICKNESS
)

floor.translate((min_x, min_y, -FLOOR_THICKNESS))

floor.compute_vertex_normals()

o3d.visualization.draw_geometries([floor])