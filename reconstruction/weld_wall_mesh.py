import trimesh


INPUT = "outputs/meshes/plan2scene_final.obj"
OUTPUT = "outputs/meshes/plan2scene_welded.obj"


print("Loading mesh...")

mesh = trimesh.load(INPUT)


print("Before")
print("Vertices:", len(mesh.vertices))
print("Faces:", len(mesh.faces))
print("Components:", len(mesh.split()))


# Weld nearby vertices
mesh.merge_vertices(
    digits_vertex=3
)


# Recalculate normals
mesh.fix_normals()


print("\nAfter welding")
print("Vertices:", len(mesh.vertices))
print("Faces:", len(mesh.faces))
print("Components:", len(mesh.split()))


mesh.export(OUTPUT)


print("\nSaved:")
print(OUTPUT)