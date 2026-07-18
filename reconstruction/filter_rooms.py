import json
import os


INPUT_PATH = "outputs/reconstruction/final_rooms.json"

OUTPUT_PATH = "outputs/reconstruction/valid_rooms.json"


# Original image size
IMAGE_WIDTH = 4200
IMAGE_HEIGHT = 2481


# Filtering parameters

MIN_AREA = 10000

BORDER_MARGIN = 100

MIN_WIDTH = 40
MIN_HEIGHT = 40



def polygon_bounds(points):

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return (
        min(xs),
        min(ys),
        max(xs),
        max(ys)
    )



def polygon_area(points):

    area = 0

    n = len(points)

    for i in range(n):

        x1,y1 = points[i]

        x2,y2 = points[(i+1)%n]

        area += (
            x1*y2 -
            x2*y1
        )

    return abs(area)/2



def touches_border(points):

    for x,y in points:

        if (
            x < BORDER_MARGIN or
            y < BORDER_MARGIN or
            x > IMAGE_WIDTH-BORDER_MARGIN or
            y > IMAGE_HEIGHT-BORDER_MARGIN
        ):
            return True

    return False



def main():

    with open(INPUT_PATH) as f:
        rooms=json.load(f)


    valid=[]


    removed=0


    for room in rooms:

        polygon = room["polygon"]


        area = polygon_area(
            polygon
        )


        x1,y1,x2,y2 = polygon_bounds(
            polygon
        )


        width = x2-x1
        height = y2-y1


        reason=None


        if area < MIN_AREA:
            reason="small area"


        elif touches_border(polygon) and (
            width < 100 or height < 100
             ):  
            reason="border artifact"


        elif width < MIN_WIDTH or height < MIN_HEIGHT:
            reason="thin region"



        if reason:

            print(
                f"Removed room {room['id']}: {reason}"
            )

            removed += 1
            continue



        valid.append(
            {
                "id": room["id"],
                "area": int(area),
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
            valid,
            f,
            indent=4
        )


    print("\nOriginal rooms:",len(rooms))
    print("Removed:",removed)
    print("Valid rooms:",len(valid))

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()