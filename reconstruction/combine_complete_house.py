import trimesh
import os


wall_file = "outputs/meshes/final_connected_walls.obj"
room_floor_file = "outputs/meshes/room_floors.obj"
base_floor_file = "outputs/meshes/base_floor.obj"


print("Loading meshes...")


walls = trimesh.load(wall_file)
rooms = trimesh.load(room_floor_file)
base = trimesh.load(base_floor_file)


combined = trimesh.util.concatenate(
    [
        walls,
        rooms,
        base
    ]
)


combined.remove_unreferenced_vertices()


output = "outputs/meshes/plan2scene_complete_house.obj"


combined.export(output)


print()
print("Final House Mesh")
print("----------------")
print("Vertices:", len(combined.vertices))
print("Faces:", len(combined.faces))
print("Components:", len(combined.split()))
print()
print("Saved:")
print(output)