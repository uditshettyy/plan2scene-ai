import json
import os
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import triangulate


INPUT = "outputs/reconstruction/valid_room_polygons.json"

OUTPUT_DIR = "outputs/meshes"

OUTPUT_OBJ = "outputs/meshes/floors.obj"


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    with open(INPUT) as f:
        rooms=json.load(f)


    vertices=[]
    faces=[]


    vertex_offset=0


    for room in rooms:

        polygon_points = room["polygon"]


        poly = Polygon(
            polygon_points
        )


        if not poly.is_valid:
            print(
                "Invalid polygon:",
                room["id"]
            )
            continue


        triangles = triangulate(
            poly
        )


        for tri in triangles:

            coords=list(
                tri.exterior.coords
            )[:-1]


            face=[]


            for x,y in coords:

                vertices.append(
                    [
                        x,
                        0,
                        -y
                    ]
                )


                face.append(
                    vertex_offset
                )


                vertex_offset += 1


            faces.append(
                face
            )


    with open(
        OUTPUT_OBJ,
        "w"
    ) as f:


        # vertices

        for v in vertices:

            f.write(
                f"v {v[0]} {v[1]} {v[2]}\n"
            )


        # faces

        for face in faces:

            # OBJ starts from 1

            f.write(
                "f "
                +
                " ".join(
                    str(i+1)
                    for i in face
                )
                +
                "\n"
            )


    print(
        "Vertices:",
        len(vertices)
    )

    print(
        "Faces:",
        len(faces)
    )

    print(
        "Saved:",
        OUTPUT_OBJ
    )



if __name__=="__main__":
    main()