import json
import os
import math
from collections import defaultdict


INPUT_PATH = "outputs/reconstruction/clean_planar_graph.json"

OUTPUT_PATH = "outputs/reconstruction/final_room_faces.json"


MIN_ROOM_AREA = 8000
MAX_ROOM_AREA = 1000000



def polygon_area(points):

    area = 0

    for i in range(len(points)):

        x1,y1 = points[i]

        x2,y2 = points[
            (i+1)%len(points)
        ]

        area += (
            x1*y2 -
            x2*y1
        )

    return abs(area)/2



def polygon_centroid(points):

    x=sum(
        p[0] for p in points
    )/len(points)

    y=sum(
        p[1] for p in points
    )/len(points)

    return [x,y]



def build_graph(graph):

    adj=defaultdict(list)


    for e in graph["edges"]:

        a=e["from"]
        b=e["to"]

        adj[a].append(b)
        adj[b].append(a)


    return adj



def angle(center,point):

    return math.atan2(
        point[1]-center[1],
        point[0]-center[0]
    )



def sort_neighbors(nodes,adj):

    sorted_adj={}


    for node,neighbors in adj.items():

        center=nodes[node]


        sorted_adj[node]=sorted(
            neighbors,
            key=lambda n:
            angle(
                center,
                nodes[n]
            )
        )


    return sorted_adj



def extract_faces(nodes,adj):

    visited=set()

    faces=[]


    for start in adj:


        for nxt in adj[start]:


            edge=(start,nxt)


            if edge in visited:
                continue


            face=[]

            current=start
            previous=nxt


            while True:

                visited.add(
                    (current,previous)
                )


                face.append(
                    current
                )


                neighbors=adj[previous]


                # choose next edge

                idx=neighbors.index(
                    current
                )


                next_node = neighbors[
                    (idx-1)%len(neighbors)
                ]


                current,previous = previous,next_node


                if current==start and previous==nxt:
                    break


                if len(face)>200:
                    break


            if len(face)>=3:
                faces.append(face)


    return faces



def main():

    with open(INPUT_PATH) as f:

        graph=json.load(f)


    nodes=graph["nodes"]


    adj=build_graph(
        graph
    )


    adj=sort_neighbors(
        nodes,
        adj
    )


    faces=extract_faces(
        nodes,
        adj
    )


    rooms=[]


    areas=[]


    for face in faces:

        polygon=[
            nodes[i]
            for i in face
        ]


        area=polygon_area(
            polygon
        )


        areas.append(area)


        if (
            MIN_ROOM_AREA
            <
            area
            <
            MAX_ROOM_AREA
        ):

            rooms.append(
                {
                    "id":len(rooms)+1,

                    "area":int(area),

                    "polygon":polygon
                }
            )


    # remove biggest outside face automatically


    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            rooms,
            f,
            indent=4
        )


    print(
        "Total faces:",
        len(faces)
    )

    print(
        "Largest face:",
        int(max(areas))
        if areas else 0
    )

    print(
        "Rooms extracted:",
        len(rooms)
    )

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()