import json
import math
import os
import networkx as nx


INPUT = "outputs/geometry/wall_segments.json"

OUTPUT = "outputs/geometry/connected_wall_graph.json"


SNAP_DISTANCE = 35


def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )



def snap_point(point,nodes):

    for n in nodes:

        if distance(point,n) < SNAP_DISTANCE:
            return n

    nodes.append(point)

    return point



def main():


    with open(INPUT) as f:
        walls=json.load(f)



    nodes=[]

    edges=[]


    for w in walls:


        start=snap_point(
            w["start"],
            nodes
        )


        end=snap_point(
            w["end"],
            nodes
        )


        edges.append(
            {
                "start":start,
                "end":end,
                "orientation":w["orientation"],
                "thickness":w["thickness"]
            }
        )



    # build graph

    G=nx.Graph()


    for e in edges:

        G.add_edge(
            tuple(e["start"]),
            tuple(e["end"])
        )



    print("Nodes:",G.number_of_nodes())

    print("Edges:",G.number_of_edges())

    print(
        "Components:",
        nx.number_connected_components(G)
    )


    output={

        "nodes":[
            list(n)
            for n in G.nodes
        ],


        "edges":edges

    }


    os.makedirs(
        "outputs/geometry",
        exist_ok=True
    )


    with open(
        OUTPUT,
        "w"
    ) as f:

        json.dump(
            output,
            f,
            indent=4
        )


    print(
        "Saved:",
        OUTPUT
    )



if __name__=="__main__":
    main()