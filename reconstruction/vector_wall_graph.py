import json
import os
from shapely.geometry import LineString, Point


INPUT_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/vector_wall_graph.json"


INTERSECTION_THRESHOLD = 5



def load_walls():

    with open(INPUT_PATH) as f:
        return json.load(f)



def create_lines(walls):

    lines=[]

    for idx,w in enumerate(walls):

        line = LineString(
            [
                tuple(w["start"]),
                tuple(w["end"])
            ]
        )

        lines.append(
            {
                "id":idx,
                "line":line
            }
        )

    return lines



def snap_point(points, point):

    x,y = point


    for p in points:

        if (
            abs(p[0]-x)<INTERSECTION_THRESHOLD
            and
            abs(p[1]-y)<INTERSECTION_THRESHOLD
        ):
            return p


    points.append(
        [
            round(x),
            round(y)
        ]
    )

    return points[-1]



def main():

    walls = load_walls()

    lines=create_lines(walls)


    nodes=[]

    edges=[]


    # collect endpoints first

    for item in lines:

        coords=list(
            item["line"].coords
        )


        start=snap_point(
            nodes,
            coords[0]
        )

        end=snap_point(
            nodes,
            coords[-1]
        )


        edges.append(
            {
                "from":start,
                "to":end
            }
        )


    # intersections

    for i,l1 in enumerate(lines):

        for j,l2 in enumerate(lines[i+1:],i+1):


            if l1["line"].intersects(
                l2["line"]
            ):


                geom=l1["line"].intersection(
                    l2["line"]
                )


                if isinstance(
                    geom,
                    Point
                ):

                    snap_point(
                        nodes,
                        [
                            geom.x,
                            geom.y
                        ]
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


    print("Walls:",len(walls))
    print("Nodes:",len(nodes))
    print("Edges:",len(edges))

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()