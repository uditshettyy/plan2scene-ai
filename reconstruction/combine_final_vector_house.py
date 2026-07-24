import trimesh
import os


WALLS = "outputs/meshes/vector_walls.obj"

FLOORS = "outputs/meshes/vector_room_floors.obj"

OUTPUT = "outputs/meshes/plan2scene_vector_house.obj"



def main():

    wall_mesh = trimesh.load(
        WALLS,
        force="mesh"
    )


    floor_mesh = trimesh.load(
        FLOORS,
        force="mesh"
    )


    combined = trimesh.util.concatenate(
        [
            wall_mesh,
            floor_mesh
        ]
    )


    os.makedirs(
        "outputs/meshes",
        exist_ok=True
    )


    combined.export(
        OUTPUT
    )


    print("Wall vertices:",len(wall_mesh.vertices))
    print("Floor vertices:",len(floor_mesh.vertices))

    print("Combined vertices:",len(combined.vertices))
    print("Combined faces:",len(combined.faces))

    print("Saved:")
    print(OUTPUT)



if __name__=="__main__":
    main()