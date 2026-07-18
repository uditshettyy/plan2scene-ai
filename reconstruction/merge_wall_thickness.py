import json
import math
import os


INPUT_PATH = "outputs/geometry/snapped_walls.json"

OUTPUT_PATH = "outputs/reconstruction/clean_vector_walls.json"


DIST_THRESHOLD = 25



def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )



def normalize_wall(w):

    x1,y1 = w["start"]
    x2,y2 = w["end"]

    return {
        "start":[x1,y1],
        "end":[x2,y2],
        "orientation":w["orientation"]
    }



def merge_horizontal(walls):

    result=[]

    used=set()


    for i,w1 in enumerate(walls):

        if i in used:
            continue


        x1,y1=w1["start"]
        x2,y2=w1["end"]


        merged=[x1,x2]

        for j,w2 in enumerate(walls[i+1:],i+1):

            if j in used:
                continue


            a1,b1=w2["start"]
            a2,b2=w2["end"]


            if abs(y1-b1)<DIST_THRESHOLD:

                if (
                    abs(x2-a1)<DIST_THRESHOLD or
                    abs(a2-x1)<DIST_THRESHOLD
                ):

                    merged.extend(
                        [a1,a2]
                    )

                    used.add(j)


        result.append(
            {
                "start":[min(merged),y1],
                "end":[max(merged),y1],
                "orientation":"horizontal"
            }
        )


    return result



def merge_vertical(walls):

    result=[]

    used=set()


    for i,w1 in enumerate(walls):

        if i in used:
            continue


        x1,y1=w1["start"]
        x2,y2=w1["end"]


        merged=[y1,y2]


        for j,w2 in enumerate(walls[i+1:],i+1):

            if j in used:
                continue


            a1,b1=w2["start"]
            a2,b2=w2["end"]


            if abs(x1-a1)<DIST_THRESHOLD:

                if (
                    abs(y2-b1)<DIST_THRESHOLD or
                    abs(b2-y1)<DIST_THRESHOLD
                ):

                    merged.extend(
                        [b1,b2]
                    )

                    used.add(j)


        result.append(
            {
                "start":[x1,min(merged)],
                "end":[x1,max(merged)],
                "orientation":"vertical"
            }
        )


    return result



def main():

    with open(INPUT_PATH) as f:
        walls=json.load(f)


    walls=[
        normalize_wall(w)
        for w in walls
    ]


    horizontal=[
        w for w in walls
        if w["orientation"]=="horizontal"
    ]


    vertical=[
        w for w in walls
        if w["orientation"]=="vertical"
    ]


    clean=[]

    clean.extend(
        merge_horizontal(horizontal)
    )

    clean.extend(
        merge_vertical(vertical)
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
            clean,
            f,
            indent=4
        )


    print("Original walls:",len(walls))
    print("Clean walls:",len(clean))
    print("Saved:",OUTPUT_PATH)



if __name__=="__main__":
    main()