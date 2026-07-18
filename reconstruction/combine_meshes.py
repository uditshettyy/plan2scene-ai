import os


FLOOR_FILE = "outputs/meshes/floors.obj"
WALL_FILE = "outputs/meshes/walls.obj"

OUTPUT = "outputs/meshes/plan2scene_house.obj"



def read_obj(path):

    vertices=[]
    faces=[]


    with open(path) as f:

        for line in f:

            if line.startswith("v "):

                parts=line.strip().split()

                vertices.append(
                    [
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3])
                    ]
                )


            elif line.startswith("f "):

                parts=line.strip().split()[1:]

                faces.append(
                    [
                        int(p)
                        for p in parts
                    ]
                )


    return vertices,faces



def main():

    vertices=[]
    faces=[]


    offset=0


    for file in [
        FLOOR_FILE,
        WALL_FILE
    ]:

        v,f=read_obj(file)


        vertices.extend(v)


        for face in f:

            faces.append(
                [
                    x+offset
                    for x in face
                ]
            )


        offset += len(v)



    os.makedirs(
        "outputs/meshes",
        exist_ok=True
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


    print("Total vertices:",len(vertices))
    print("Total faces:",len(faces))
    print("Saved:",OUTPUT)



if __name__=="__main__":
    main()