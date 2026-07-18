import trimesh
import os


INPUT = "outputs/meshes/plan2scene_complete_house.obj"

OUTPUT = "outputs/meshes/plan2scene_complete_house.glb"



def main():

    mesh = trimesh.load(
        INPUT,
        force="mesh"
    )


    os.makedirs(
        "outputs/meshes",
        exist_ok=True
    )


    mesh.export(
        OUTPUT
    )


    print("Converted:")
    print(OUTPUT)



if __name__ == "__main__":
    main()