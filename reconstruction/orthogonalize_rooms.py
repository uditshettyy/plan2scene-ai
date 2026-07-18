import json
import os
import math


INPUT_PATH = "outputs/reconstruction/clean_rooms.json"

OUTPUT_PATH = "outputs/reconstruction/orthogonal_rooms.json"



def snap_value(value, tolerance=15):
    """
    Snap close values together
    """

    return round(value)



def is_horizontal(p1, p2, threshold=15):

    return abs(p1[1]-p2[1]) < threshold



def is_vertical(p1, p2, threshold=15):

    return abs(p1[0]-p2[0]) < threshold



def orthogonalize_polygon(points):

    result=[]

    n=len(points)


    for i in range(n):

        current = points[i]
        next_point = points[(i+1)%n]


        x1,y1=current
        x2,y2=next_point


        if is_horizontal(
            current,
            next_point
        ):

            y=(y1+y2)//2

            current=[
                x1,
                y
            ]


        elif is_vertical(
            current,
            next_point
        ):

            x=(x1+x2)//2

            current=[
                x,
                y1
            ]


        result.append(current)


    return result



def remove_duplicate_points(points):

    cleaned=[]

    for p in points:

        if not cleaned or p != cleaned[-1]:
            cleaned.append(p)


    # remove last point if same as first

    if len(cleaned)>1 and cleaned[0]==cleaned[-1]:
        cleaned.pop()


    return cleaned



def main():

    with open(INPUT_PATH) as f:
        rooms=json.load(f)


    output=[]


    for room in rooms:

        polygon = room["polygon"]


        polygon = orthogonalize_polygon(
            polygon
        )


        polygon = remove_duplicate_points(
            polygon
        )


        output.append(
            {
                "id": room["id"],
                "area": room["area"],
                "polygon": polygon
            }
        )


    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            output,
            f,
            indent=4
        )


    print("Rooms processed:",len(output))
    print("Saved:",OUTPUT_PATH)



if __name__=="__main__":
    main()