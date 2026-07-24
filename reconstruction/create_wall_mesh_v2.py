import json
import os
import trimesh
from shapely.geometry import LineString


INPUT = "outputs/reconstruction/vector_wall_graph_v3.json"

OUTPUT = "outputs/meshes/vector_walls.obj"


WALL_HEIGHT = 300
DEFAULT_THICKNESS = 35


vertices = []
faces = []


def add_wall(p1, p2, thickness):

    line = LineString(
        [
            p1,
            p2
        ]
    )


    poly = line.buffer(
        thickness / 2,
        cap_style=2
    )


    coords = list(
        poly.exterior.coords
    )[:-1]


    start = len(vertices)


    # bottom

    for x,y in coords:

        vertices.append(
            [
                x,
                0,
                -y
            ]
        )


    # top

    for x,y in coords:

        vertices.append(
            [
                x,
                WALL_HEIGHT,
                -y
            ]
        )


    n=len(coords)


    for i in range(n):

        faces.append(
            [
                start+i,
                start+(i+1)%n,
                start+n+(i+1)%n,
                start+n+i
            ]
        )



def main():

    with open(INPUT) as f:

        graph=json.load(f)


    nodes=graph["nodes"]
    edges=graph["edges"]


    for e in edges:

        p1=nodes[e["from"]]
        p2=nodes[e["to"]]


        add_wall(
            p1,
            p2,
            e.get(
                "thickness",
                DEFAULT_THICKNESS
            )
        )


    mesh=trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
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


    print("Edges:",len(edges))
    print("Vertices:",len(mesh.vertices))
    print("Faces:",len(mesh.faces))
    print("Saved:")
    print(OUTPUT)



if __name__=="__main__":
    main()