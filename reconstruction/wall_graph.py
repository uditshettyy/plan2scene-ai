import json
import os
import math


INPUT = "outputs/geometry/snapped_walls.json"
OUTPUT = "outputs/geometry/wall_graph.json"


os.makedirs("outputs/geometry", exist_ok=True)


with open(INPUT) as f:
    walls = json.load(f)


nodes = []
edges = []


THRESHOLD = 20


def find_node(point):

    for i, node in enumerate(nodes):

        distance = math.sqrt(
            (node[0]-point[0])**2 +
            (node[1]-point[1])**2
        )

        if distance < THRESHOLD:
            return i

    nodes.append(point)
    return len(nodes)-1



for wall in walls:

    start = wall["start"]
    end = wall["end"]


    start_id = find_node(start)
    end_id = find_node(end)


    edges.append(
        {
            "from": start_id,
            "to": end_id
        }
    )


graph = {
    "nodes": nodes,
    "edges": edges
}


with open(OUTPUT,"w") as f:
    json.dump(
        graph,
        f,
        indent=4
    )


print("Nodes :",len(nodes))
print("Edges :",len(edges))
print("Saved ->",OUTPUT)