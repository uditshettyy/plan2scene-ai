import json
import networkx as nx
import os


INPUT = "outputs/geometry/final_wall_segments.json"

OUTPUT = "outputs/geometry/clean_wall_segments.json"


MIN_COMPONENT_SIZE = 5



with open(INPUT) as f:
    walls=json.load(f)



G=nx.Graph()


for i,w in enumerate(walls):

    G.add_edge(
        tuple(w["start"]),
        tuple(w["end"]),
        index=i
    )



valid_edges=set()


components=list(
    nx.connected_components(G)
)


print("Components before:",len(components))


for comp in components:

    print(
        "component size:",
        len(comp)
    )

    if len(comp)>=MIN_COMPONENT_SIZE:

        for u,v,data in G.subgraph(comp).edges(data=True):

            valid_edges.add(
                data["index"]
            )



clean=[]


for i,w in enumerate(walls):

    if i in valid_edges:
        clean.append(w)



print("\nOriginal walls:",len(walls))
print("Clean walls:",len(clean))



os.makedirs(
    "outputs/geometry",
    exist_ok=True
)


with open(OUTPUT,"w") as f:

    json.dump(
        clean,
        f,
        indent=4
    )


print("Saved:",OUTPUT)