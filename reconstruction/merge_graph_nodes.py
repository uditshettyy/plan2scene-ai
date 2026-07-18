import json
import os
import math


INPUT = "outputs/geometry/wall_graph.json"
OUTPUT = "outputs/geometry/merged_wall_graph.json"


os.makedirs("outputs/geometry", exist_ok=True)


with open(INPUT) as f:
    graph = json.load(f)


nodes = graph["nodes"]
edges = graph["edges"]


DISTANCE_THRESHOLD = 30


def distance(a, b):
    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )


# Map old nodes to new nodes

mapping = {}
new_nodes = []


for i, node in enumerate(nodes):

    found = False

    for j, new_node in enumerate(new_nodes):

        if distance(node, new_node) < DISTANCE_THRESHOLD:

            mapping[i] = j
            found = True
            break


    if not found:

        mapping[i] = len(new_nodes)
        new_nodes.append(node)



# Rebuild edges

new_edges = []

for edge in edges:

    a = mapping[edge["from"]]
    b = mapping[edge["to"]]


    if a != b:

        new_edges.append(
            {
                "from":a,
                "to":b
            }
        )



merged_graph = {
    "nodes": new_nodes,
    "edges": new_edges
}



with open(OUTPUT,"w") as f:
    json.dump(
        merged_graph,
        f,
        indent=4
    )


print("Original nodes:",len(nodes))
print("Merged nodes:",len(new_nodes))
print("Edges:",len(new_edges))
print("Saved ->",OUTPUT)