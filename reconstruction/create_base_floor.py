import trimesh
import os


OUTPUT = "outputs/meshes/base_floor.obj"


# building bounds from walls

x1 = 267
x2 = 3825

z1 = -2187
z2 = -637


vertices = [
    [x1,0,z1],
    [x2,0,z1],
    [x2,0,z2],
    [x1,0,z2],
]


faces=[
    [0,1,2],
    [0,2,3]
]


mesh=trimesh.Trimesh(
    vertices=vertices,
    faces=faces
)


mesh.fix_normals()


os.makedirs(
    "outputs/meshes",
    exist_ok=True
)


mesh.export(
    OUTPUT
)


print("Saved:")
print(OUTPUT)