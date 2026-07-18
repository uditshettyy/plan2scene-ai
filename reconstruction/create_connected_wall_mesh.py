import json
import os
import trimesh
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.geometry import Polygon
from shapely.ops import triangulate


INPUT = "outputs/geometry/clean_wall_segments.json"

OUTPUT = "outputs/meshes/connected_walls.obj"


WALL_HEIGHT = 300


from shapely.ops import triangulate


def polygon_to_mesh(poly, height):

    vertices=[]
    faces=[]

    triangles = triangulate(poly)


    vertex_map={}


    def get_vertex(coord):

        key=(round(coord[0],3),round(coord[1],3))

        if key not in vertex_map:

            vertex_map[key]=len(vertices)

            vertices.append(
                [
                    coord[0],
                    0,
                    -coord[1]
                ]
            )


        return vertex_map[key]


    # create bottom and top triangles

    for tri in triangles:

        coords=list(tri.exterior.coords)[:3]


        bottom=[]
        top=[]


        for c in coords:

            idx=get_vertex(c)

            bottom.append(idx)


            vertices.append(
                [
                    c[0],
                    height,
                    -c[1]
                ]
            )

            top.append(
                len(vertices)-1
            )


        # bottom
        faces.append(
            [
                bottom[0],
                bottom[2],
                bottom[1]
            ]
        )


        # top
        faces.append(
            [
                top[0],
                top[1],
                top[2]
            ]
        )


        # walls around triangle

        for i in range(3):

            faces.append(
                [
                    bottom[i],
                    bottom[(i+1)%3],
                    top[(i+1)%3]
                ]
            )

            faces.append(
                [
                    bottom[i],
                    top[(i+1)%3],
                    top[i]
                ]
            )


    return vertices,faces



with open(INPUT) as f:
    walls=json.load(f)



wall_polygons=[]


for w in walls:


    line=LineString(
        [
            w["start"],
            w["end"]
        ]
    )


    thickness=w["thickness"]


    poly=line.buffer(
        thickness/2,
        cap_style=2
    )


    wall_polygons.append(poly)



print("Wall polygons:",len(wall_polygons))


# merge touching walls

merged=unary_union(
    wall_polygons
)


if merged.geom_type=="Polygon":

    polygons=[merged]

else:

    polygons=list(merged.geoms)



print("Merged wall regions:",len(polygons))



vertices=[]
faces=[]


for poly in polygons:

    v,f=polygon_to_mesh(
        poly,
        WALL_HEIGHT
    )


    offset=len(vertices)

    vertices.extend(v)


    for face in f:
        faces.append(
            [
                x+offset
                for x in face
            ]
        )



mesh=trimesh.Trimesh(
    vertices=vertices,
    faces=faces
)


mesh.fix_normals()


os.makedirs(
    "outputs/meshes",
    exist_ok=True
)


mesh.export(OUTPUT)


print("Vertices:",len(mesh.vertices))
print("Faces:",len(mesh.faces))

print("Components:",
      len(mesh.split()))


print("Saved:")
print(OUTPUT)