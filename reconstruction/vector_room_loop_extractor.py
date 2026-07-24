import json
import os
from collections import defaultdict


INPUT_PATH = "outputs/reconstruction/vector_wall_graph_v3.json"
OUTPUT_PATH = "outputs/reconstruction/vector_rooms.json"


MIN_AREA = 5000


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



def build_adjacency(graph):

    adj = defaultdict(list)

    for edge in graph["edges"]:

        a=edge["from"]
        b=edge["to"]

        adj[a].append(b)
        adj[b].append(a)

    return adj



def normalize_cycle(cycle):

    """
    Remove duplicate cycles
    """

    smallest=min(cycle)

    idx=cycle.index(
        smallest
    )

    return (
        cycle[idx:]
        +
        cycle[:idx]
    )



def find_cycles(nodes, adj):

    cycles=[]

    visited=set()


    def dfs(start,current,path):

        for nxt in adj[current]:

            if nxt==start and len(path)>=3:

                cycle=normalize_cycle(
                    path.copy()
                )

                if cycle not in cycles:
                    cycles.append(
                        cycle
                    )

                continue


            if nxt in path:
                continue


            if len(path)>20:
                continue


            dfs(
                start,
                nxt,
                path+[nxt]
            )


    for node in nodes:

        dfs(
            node,
            node,
            [node]
        )


    return cycles



def main():

    with open(INPUT_PATH) as f:
        graph=json.load(f)



    nodes=graph["nodes"]


    adj=build_adjacency(
        graph
    )


    print(
        "Finding cycles..."
    )


    cycles=find_cycles(
        range(len(nodes)),
        adj
    )


    rooms=[]


    for cycle in cycles:

        polygon=[
            nodes[i]
            for i in cycle
        ]


        area=polygon_area(
            polygon
        )


        if area < MIN_AREA:
            continue


        rooms.append(
            {
                "area":int(area),
                "polygon":polygon
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
            rooms,
            f,
            indent=4
        )


    print(
        "Cycles found:",
        len(cycles)
    )

    print(
        "Rooms saved:",
        len(rooms)
    )

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()