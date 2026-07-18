import json
import os


ROOM_BOX_PATH = "outputs/geometry/rooms.json"

FACE_PATH = "outputs/reconstruction/final_room_faces.json"

OUTPUT_PATH = "outputs/reconstruction/fused_rooms.json"


CONF_THRESHOLD = 0.5


def bbox_center(bbox):

    return (
        (bbox["x1"] + bbox["x2"]) / 2,
        (bbox["y1"] + bbox["y2"]) / 2
    )


def point_in_polygon(point, polygon):

    x, y = point

    inside = False

    j = len(polygon)-1

    for i in range(len(polygon)):

        xi, yi = polygon[i]
        xj, yj = polygon[j]

        intersect = (
            ((yi > y) != (yj > y))
            and
            (
                x <
                (xj-xi)*(y-yi)/(yj-yi+1e-9)+xi
            )
        )

        if intersect:
            inside = not inside

        j=i

    return inside



def load_data():

    with open(ROOM_BOX_PATH) as f:
        yolo_rooms=json.load(f)


    with open(FACE_PATH) as f:
        faces=json.load(f)


    return yolo_rooms,faces



def filter_yolo_rooms(rooms):

    filtered=[]

    for r in rooms:

        if r["confidence"] >= CONF_THRESHOLD:

            filtered.append(r)


    return filtered



def match_rooms(yolo_rooms, faces):

    fused=[]


    for yolo in yolo_rooms:


        center=bbox_center(
            yolo["bbox"]
        )


        best=None


        for face in faces:

            if point_in_polygon(
                center,
                face["polygon"]
            ):

                best=face
                break


        if best:

            fused.append(
                {
                    "id":len(fused)+1,

                    "source":"yolo+geometry",

                    "confidence":
                        yolo["confidence"],

                    "polygon":
                        best["polygon"],

                    "yolo_bbox":
                        yolo["bbox"]
                }
            )


    return fused



def main():

    yolo_rooms,faces=load_data()


    print(
        "YOLO rooms:",
        len(yolo_rooms)
    )

    print(
        "Geometry faces:",
        len(faces)
    )


    yolo_rooms=filter_yolo_rooms(
        yolo_rooms
    )


    print(
        "Filtered YOLO rooms:",
        len(yolo_rooms)
    )


    fused=match_rooms(
        yolo_rooms,
        faces
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
            fused,
            f,
            indent=4
        )


    print(
        "Fused rooms:",
        len(fused)
    )

    print(
        "Saved:",
        OUTPUT_PATH
    )


if __name__=="__main__":
    main()