import json
import os
import math


INPUT_PATH = "outputs/reconstruction/vector_wall_graph_v2.json"

OUTPUT_PATH = "outputs/reconstruction/clean_planar_graph.json"


NODE_DISTANCE = 25



def distance(a,b):

    return math.sqrt(
        (a[0]-b[0])**2 +
        (a[1]-b[1])**2
    )



def merge_nodes(nodes):

    mapping={}
    new_nodes=[]


    for i,node in enumerate(nodes):

        found=None

        for j,new in enumerate(new_nodes):

            if distance(node,new) < NODE_DISTANCE:

                found=j
                break


        if found is None:

            mapping[i]=len(new_nodes)

            new_nodes.append(node)

        else:

            mapping[i]=found



    return new_nodes,mapping



def main():

    with open(INPUT_PATH) as f:
        graph=json.load(f)



    nodes=graph["nodes"]
    edges=graph["edges"]



    new_nodes,mapping = merge_nodes(nodes)


    new_edges=[]

    seen=set()


    for e in edges:

        a=mapping[e["from"]]
        b=mapping[e["to"]]


        if a==b:
            continue


        key=tuple(
            sorted(
                [a,b]
            )
        )


        if key in seen:
            continue


        seen.add(key)


        new_edges.append(
            {
                "from":a,
                "to":b
            }
        )



    output={

        "nodes":new_nodes,

        "edges":new_edges

    }


    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )


    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            output,
            f,
            indent=4
        )


    print("Original nodes:",len(nodes))
    print("New nodes:",len(new_nodes))

    print("Original edges:",len(edges))
    print("New edges:",len(new_edges))

    print(
        "Saved:",
        OUTPUT_PATH
    )



if __name__=="__main__":
    main()