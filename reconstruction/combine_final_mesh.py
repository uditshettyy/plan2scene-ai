import os


FILES = [
    "outputs/meshes/floors.obj",
    "outputs/meshes/thick_walls.obj"
]

OUTPUT = "outputs/meshes/plan2scene_final.obj"



def read_obj(path):

    vertices=[]
    faces=[]

    with open(path) as f:

        for line in f:

            if line.startswith("v "):

                p=line.split()

                vertices.append(
                    [
                        float(p[1]),
                        float(p[2]),
                        float(p[3])
                    ]
                )


            elif line.startswith("f "):

                p=line.split()[1:]

                faces.append(
                    [
                        int(x)
                        for x in p
                    ]
                )

    return vertices,faces



def main():

    vertices=[]
    faces=[]

    offset=0


    for file in FILES:

        v,f=read_obj(file)


        vertices.extend(v)


        for face in f:

            faces.append(
                [
                    i+offset
                    for i in face
                ]
            )


        offset += len(v)



    os.makedirs(
        "outputs/meshes",
        exist_ok=True
    )


    with open(OUTPUT,"w") as f:

        for v in vertices:

            f.write(
                f"v {v[0]} {v[1]} {v[2]}\n"
            )


        for face in faces:

            f.write(
                "f "
                +
                " ".join(map(str,face))
                +
                "\n"
            )


    print("Vertices:",len(vertices))
    print("Faces:",len(faces))
    print("Saved:",OUTPUT)



if __name__=="__main__":
    main()