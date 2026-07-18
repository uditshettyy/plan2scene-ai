import json
import os
from shapely.geometry import LineString, Point


INPUT = "outputs/geometry/merged_wall_segments.json"

OUTPUT = "outputs/geometry/split_wall_segments.json"


def main():

    with open(INPUT) as f:
        walls=json.load(f)


    lines=[]

    for w in walls:

        lines.append(
            {
                "line":LineString(
                    [
                        w["start"],
                        w["end"]
                    ]
                ),
                "data":w
            }
        )


    split_points=[[] for _ in walls]


    # find intersections

    for i,a in enumerate(lines):

        for j,b in enumerate(lines):

            if i>=j:
                continue


            inter=a["line"].intersection(
                b["line"]
            )


            if isinstance(inter, Point):

                p=[
                    inter.x,
                    inter.y
                ]

                split_points[i].append(p)
                split_points[j].append(p)



    new_walls=[]


    for i,item in enumerate(lines):

        points=[
            item["data"]["start"],
            item["data"]["end"]
        ]


        points.extend(
            split_points[i]
        )


        # remove duplicates

        unique=[]

        for p in points:

            if p not in unique:
                unique.append(p)


        # sort along wall

        if item["data"]["orientation"]=="horizontal":

            unique.sort(
                key=lambda x:x[0]
            )

        else:

            unique.sort(
                key=lambda x:x[1]
            )


        # create segments

        for a,b in zip(
            unique[:-1],
            unique[1:]
        ):

            if a!=b:

                new_walls.append(
                    {
                        "orientation":
                        item["data"]["orientation"],

                        "start":a,

                        "end":b,

                        "thickness":
                        item["data"]["thickness"]
                    }
                )



    print(
        "Original walls:",
        len(walls)
    )

    print(
        "Split walls:",
        len(new_walls)
    )


    os.makedirs(
        "outputs/geometry",
        exist_ok=True
    )


    with open(
        OUTPUT,
        "w"
    ) as f:

        json.dump(
            new_walls,
            f,
            indent=4
        )


    print(
        "Saved:",
        OUTPUT
    )



if __name__=="__main__":
    main()