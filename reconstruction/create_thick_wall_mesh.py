import json
import os


INPUT = "outputs/geometry/snapped_walls.json"

OUTPUT = "outputs/meshes/thick_walls.obj"


WALL_HEIGHT = 300
WALL_THICKNESS = 20



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


        if wall["orientation"]=="horizontal":

            y_top = y1 - WALL_THICKNESS/2
            y_bottom = y1 + WALL_THICKNESS/2


            points=[
                [x1,y_top],
                [x2,y_top],
                [x2,y_bottom],
                [x1,y_bottom]
            ]


        else:

            x_left = x1 - WALL_THICKNESS/2
            x_right = x1 + WALL_THICKNESS/2


            points=[
                [x_left,y1],
                [x_right,y1],
                [x_right,y2],
                [x_left,y2]
            ]



        base=len(vertices)+1


        for x,y in points:

            vertices.append(
                [
                    x,
                    0,
                    -y
                ]
            )


        for x,y in points:

            vertices.append(
                [
                    x,
                    WALL_HEIGHT,
                    -y
                ]
            )


        # bottom
        faces.append(
            [
                base,
                base+1,
                base+2,
                base+3
            ]
        )


        # top
        faces.append(
            [
                base+4,
                base+7,
                base+6,
                base+5
            ]
        )


        # sides
        faces.append(
            [
                base,
                base+4,
                base+5,
                base+1
            ]
        )


        faces.append(
            [
                base+1,
                base+5,
                base+6,
                base+2
            ]
        )


        faces.append(
            [
                base+2,
                base+6,
                base+7,
                base+3
            ]
        )


        faces.append(
            [
                base+3,
                base+7,
                base+4,
                base
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
                    map(str,face)
                )
                +
                "\n"
            )



    print("Walls processed:",len(walls))
    print("Vertices:",len(vertices))
    print("Faces:",len(faces))
    print("Saved:",OUTPUT)



if __name__=="__main__":
    main()