import json
import trimesh
import os
from shapely.geometry import LineString


INPUT = "outputs/geometry/clean_wall_segments.json"

OUTPUT = "outputs/meshes/final_connected_walls.obj"

HEIGHT = 300


def create_wall_mesh(poly, height):

    coords=list(poly.exterior.coords)[:-1]

    vertices=[]
    faces=[]

    n=len(coords)


    # bottom vertices
    for x,y in coords:
        vertices.append(
            [x,0,-y]
        )


    # top vertices
    for x,y in coords:
        vertices.append(
            [x,height,-y]
        )


    # side faces
    for i in range(n):

        j=(i+1)%n

        faces.append(
            [
                i,
                j,
                n+j
            ]
        )

        faces.append(
            [
                i,
                n+j,
                n+i
            ]
        )


    # triangulate top and bottom using fan method

    for i in range(1,n-1):

        # bottom
        faces.append(
            [
                0,
                i+1,
                i
            ]
        )


        # top
        faces.append(
            [
                n,
                n+i,
                n+i+1
            ]
        )


    return trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=True
    )



with open(INPUT) as f:
    walls=json.load(f)



meshes=[]


for w in walls:

    line=LineString(
        [
            w["start"],
            w["end"]
        ]
    )


    wall_poly=line.buffer(
        w["thickness"]/2,
        cap_style=2
    )


    mesh=create_wall_mesh(
        wall_poly,
        HEIGHT
    )


    meshes.append(mesh)



print("Wall meshes:",len(meshes))


combined=trimesh.util.concatenate(
    meshes
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

print("Saved:")
print(OUTPUT)