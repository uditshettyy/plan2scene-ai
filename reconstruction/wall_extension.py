import json
import os
import copy


INPUT_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/completed_vector_walls.json"


EXTENSION_LIMIT = 80



def is_close(a,b):

    return abs(a-b) < EXTENSION_LIMIT



def extend_horizontal(wall, verticals):

    x1,y = wall["start"]
    x2,_ = wall["end"]


    new_start=x1
    new_end=x2


    for v in verticals:

        vx,vy1=v["start"]
        _,vy2=v["end"]


        if min(vy1,vy2)-EXTENSION_LIMIT <= y <= max(vy1,vy2)+EXTENSION_LIMIT:

            if is_close(vx,x1):
                new_start=vx


            if is_close(vx,x2):
                new_end=vx


    wall["start"]=[
        new_start,
        y
    ]

    wall["end"]=[
        new_end,
        y
    ]

    return wall



def extend_vertical(wall, horizontals):

    x,y1=wall["start"]
    _,y2=wall["end"]


    new_start=y1
    new_end=y2


    for h in horizontals:

        hx1,hy=h["start"]
        hx2,_=h["end"]


        if min(hx1,hx2)-EXTENSION_LIMIT <= x <= max(hx1,hx2)+EXTENSION_LIMIT:


            if is_close(hy,y1):
                new_start=hy


            if is_close(hy,y2):
                new_end=hy



    wall["start"]=[
        x,
        new_start
    ]

    wall["end"]=[
        x,
        new_end
    ]


    return wall



def main():

    with open(INPUT_PATH) as f:
        walls=json.load(f)


    horizontals=[
        w for w in walls
        if w["orientation"]=="horizontal"
    ]


    verticals=[
        w for w in walls
        if w["orientation"]=="vertical"
    ]


    completed=[]


    for w in horizontals:

        completed.append(
            extend_horizontal(
                copy.deepcopy(w),
                verticals
            )
        )


    for w in verticals:

        completed.append(
            extend_vertical(
                copy.deepcopy(w),
                horizontals
            )
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
            completed,
            f,
            indent=4
        )


    print("Original walls:",len(walls))
    print("Completed walls:",len(completed))
    print("Saved:",OUTPUT_PATH)



if __name__=="__main__":
    main()