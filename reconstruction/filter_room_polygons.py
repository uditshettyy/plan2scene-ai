import json
import os


INPUT = "outputs/reconstruction/refined_room_polygons.json"

OUTPUT = "outputs/reconstruction/valid_room_polygons.json"


# Tune later if needed
MAX_AREA = 500000


def polygon_area(poly):

    area = 0

    n = len(poly)

    for i in range(n):
        x1,y1 = poly[i]
        x2,y2 = poly[(i+1)%n]

        area += (
            x1*y2 -
            x2*y1
        )

    return abs(area)/2



def bbox_size(poly):

    xs=[p[0] for p in poly]
    ys=[p[1] for p in poly]

    return (
        max(xs)-min(xs),
        max(ys)-min(ys)
    )



def contains(big, small):

    bx=[p[0] for p in big]
    by=[p[1] for p in big]

    sx=[p[0] for p in small]
    sy=[p[1] for p in small]


    return (
        min(sx)>=min(bx)
        and max(sx)<=max(bx)
        and min(sy)>=min(by)
        and max(sy)<=max(by)
    )



def main():

    with open(INPUT) as f:
        rooms=json.load(f)



    valid=[]

    removed=0


    for room in rooms:

        area=polygon_area(
            room["polygon"]
        )


        room["area"]=area


        if area > MAX_AREA:

            print(
                "Removed large room:",
                room["id"],
                area
            )

            removed+=1
            continue


        valid.append(room)



    # remove parent rooms
    final=[]


    for room in valid:

        parent=False


        for other in valid:

            if room["id"]==other["id"]:
                continue


            if other["area"] <= room["area"]:
                continue


            if contains(
                other["polygon"],
                room["polygon"]
            ):
                parent=True
                break



        if not parent:
            final.append(room)


    os.makedirs(
        "outputs/reconstruction",
        exist_ok=True
    )


    with open(
        OUTPUT,
        "w"
    ) as f:

        json.dump(
            final,
            f,
            indent=4
        )


    print()
    print("Original:",len(rooms))
    print("Removed:",removed)
    print("Final rooms:",len(final))
    print("Saved:",OUTPUT)



if __name__=="__main__":
    main()