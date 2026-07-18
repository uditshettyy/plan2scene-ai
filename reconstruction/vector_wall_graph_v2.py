import json
import os
import math
from shapely.geometry import LineString, Point


INPUT_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/vector_wall_graph_v2.json"


NODE_TOLERANCE = 8



def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )



def add_node(nodes, point):

    x,y = point


    for i,n in enumerate(nodes):

        if distance(n,[x,y]) < NODE_TOLERANCE:
            return i


    nodes.append(
        [
            round(x),
            round(y)
        ]
    )

    return len(nodes)-1



def load_walls():

    with open(INPUT_PATH) as f:
        return json.load(f)



def main():

    walls = load_walls()


    lines=[]

    for w in walls:

        lines.append(
            LineString(
                [
                    w["start"],
                    w["end"]
                ]
            )
        )


    nodes=[]

    wall_points=[]


    # Store endpoints + intersections

    for i,line in enumerate(lines):

        points=[
            Point(line.coords[0]),
            Point(line.coords[-1])
        ]


        for j,other in enumerate(lines):

            if i==j:
                continue


            intersection=line.intersection(other)


            if isinstance(intersection,Point):

                points.append(intersection)


        wall_points.append(points)



    edges=[]


    # Split each wall

    for line,points in zip(lines,wall_points):


        unique=[]


        for p in points:

            idx=add_node(
                nodes,
                [
                    p.x,
                    p.y
                ]
            )


            unique.append(
                (
                    line.project(p),
                    idx
                )
            )


        # remove duplicates

        unique=list(
            set(unique)
        )


        # sort along wall

        unique.sort(
            key=lambda x:x[0]
        )


        # create edges

        for i in range(len(unique)-1):

            a=unique[i][1]
            b=unique[i+1][1]


            if a!=b:

                edges.append(
                    {
                        "from":a,
                        "to":b
                    }
                )



    graph={

        "nodes":nodes,

        "edges":edges

    }


    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            graph,
            f,
            indent=4
        )


    print("Original walls:",len(walls))
    print("Nodes:",len(nodes))
    print("Edges:",len(edges))

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()