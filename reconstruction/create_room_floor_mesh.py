import json
import trimesh
import os


INPUT = "outputs/reconstruction/valid_room_polygons.json"

OUTPUT = "outputs/meshes/room_floors.obj"


FLOOR_HEIGHT = 0



def polygon_to_mesh(points):

    vertices = []

    faces = []


    # create vertices
    for x,y in points:

        vertices.append(
            [
                x,
                FLOOR_HEIGHT,
                -y
            ]
        )


    # triangulate polygon using fan
    for i in range(1,len(points)-1):

        faces.append(
            [
                0,
                i,
                i+1
            ]
        )


    return vertices,faces



with open(INPUT) as f:
    rooms=json.load(f)



all_vertices=[]
all_faces=[]


offset=0


for room in rooms:

    points=[
        tuple(p)
        for p in room["polygon"]
    ]


    vertices,faces = polygon_to_mesh(points)


    all_vertices.extend(vertices)


    for face in faces:

        all_faces.append(
            [
                x+offset
                for x in face
            ]
        )


    offset += len(vertices)



mesh = trimesh.Trimesh(
    vertices=all_vertices,
    faces=all_faces,
    process=True
)


mesh.fix_normals()


os.makedirs(
    "outputs/meshes",
    exist_ok=True
)


mesh.export(
    OUTPUT
)


print("Rooms:",
      len(rooms))

print("Vertices:",
      len(mesh.vertices))

print("Faces:",
      len(mesh.faces))


print("Saved:")
print(OUTPUT)