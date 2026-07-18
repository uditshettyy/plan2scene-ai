import json
import os


INPUT = "outputs/geometry/snapped_walls.json"

OUTPUT = "outputs/meshes/walls.obj"


WALL_HEIGHT = 300


def add_vertex(vertices, v):
    vertices.append(v)
    return len(vertices)


def main():

    os.makedirs(
        "outputs/meshes",
        exist_ok=True
    )


    with open(INPUT) as f:
        walls=json.load(f)


    vertices=[]
    faces=[]


    for wall in walls:

        x1,y1 = wall["start"]
        x2,y2 = wall["end"]


        # bottom vertices

        b1=add_vertex(
            vertices,
            [x1,0,-y1]
        )

        b2=add_vertex(
            vertices,
            [x2,0,-y2]
        )


        # top vertices

        t1=add_vertex(
            vertices,
            [x1,WALL_HEIGHT,-y1]
        )

        t2=add_vertex(
            vertices,
            [x2,WALL_HEIGHT,-y2]
        )


        # wall face

        faces.append(
            [
                b1,
                b2,
                t2,
                t1
            ]
        )


    with open(
        OUTPUT,
        "w"
    ) as f:


        for v in vertices:

            f.write(
                f"v {v[0]} {v[1]} {v[2]}\n"
            )


        for face in faces:

            f.write(
                "f "
                +
                " ".join(
                    str(i)
                    for i in face
                )
                +
                "\n"
            )


    print("Walls:",len(walls))
    print("Vertices:",len(vertices))
    print("Faces:",len(faces))
    print("Saved:",OUTPUT)



if __name__=="__main__":
    main()