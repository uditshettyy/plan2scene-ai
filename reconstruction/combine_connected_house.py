import trimesh
import os


WALLS = "outputs/meshes/final_connected_walls.obj"
FLOOR = "outputs/meshes/floors.obj"

OUTPUT = "outputs/meshes/plan2scene_connected_house.obj"


print("Loading meshes...")


walls = trimesh.load(WALLS)
floor = trimesh.load(FLOOR)


combined = trimesh.util.concatenate(
    [
        walls,
        floor
    ]
)


combined.fix_normals()


os.makedirs(
    "outputs/meshes",
    exist_ok=True
)


combined.export(
    OUTPUT
)


print("Vertices:",
      len(combined.vertices))

print("Faces:",
      len(combined.faces))


print(
    "Components:",
    len(combined.split())
)


print("Saved:")
print(OUTPUT)