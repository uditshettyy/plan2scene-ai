import json
import os


INPUT = "outputs/geometry/merged_wall_graph.json"
OUTPUT = "outputs/geometry/room_polygons.json"


os.makedirs("outputs/geometry", exist_ok=True)


with open(INPUT) as f:
    graph = json.load(f)


nodes = graph["nodes"]
edges = graph["edges"]


# Build adjacency graph

adjacency = {}

for edge in edges:

    a = edge["from"]
    b = edge["to"]

    adjacency.setdefault(a, []).append(b)
    adjacency.setdefault(b, []).append(a)



rooms = []

visited_cycles = set()


def find_cycles(start, current, path):

    if len(path) > 3 and start in adjacency[current]:

        cycle = path.copy()

        key = tuple(sorted(cycle))

        if key not in visited_cycles:
            visited_cycles.add(key)

            rooms.append(
                [
                    nodes[i]
                    for i in cycle
                ]
            )

        return


    for nxt in adjacency.get(current, []):

        if nxt not in path:

            find_cycles(
                start,
                nxt,
                path+[nxt]
            )



for node in adjacency:

    find_cycles(
        node,
        node,
        [node]
    )



# remove very small duplicates

filtered=[]

for room in rooms:

    if len(room) >= 4:
        filtered.append(room)



with open(OUTPUT,"w") as f:

    json.dump(
        filtered,
        f,
        indent=4
    )


print("Detected rooms:",len(filtered))
print("Saved ->",OUTPUT)
