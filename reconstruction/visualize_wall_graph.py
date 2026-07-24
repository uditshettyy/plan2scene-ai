"""
visualize_wall_graph.py

Diagnostic tool -- NOT part of the main pipeline.

Draws the wall graph (before or after connectivity repair), coloring
each disconnected component a different color, with node ids labeled.
This lets you see exactly *where* the graph is broken, instead of
guessing from a "component sizes" list.

How to use this:
    1. Run it on your current vector_wall_graph_v3.json.
    2. Open the output PNG side by side with your original floor plan
       image (or the v2_detections.json overlay if you have one).
    3. Each color is a separate disconnected piece. Find the two
       colored clusters that are geographically close in the real
       floor plan but NOT connected here -- that's your missing wall.
       It's either a wall YOLO didn't detect at all, or a wall that
       was detected but is short/misplaced enough that it didn't reach
       the corner.

Output:
    outputs/wall_graph_debug.png

Usage:
    python visualize_wall_graph.py outputs/vector_wall_graph_v3.json outputs/wall_graph_debug.png
"""

import json
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def find_components(nodes, edges):
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    visited = set()
    components = []
    for n in nodes:
        if n in visited:
            continue
        stack, comp = [n], []
        visited.add(n)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in adj[cur]:
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        components.append(comp)
    return components


def main(graph_path, out_path):
    with open(graph_path) as f:
        graph = json.load(f)

    nodes = {n["id"]: (n["x"], n["y"]) for n in graph["nodes"]}
    edges = [tuple(e) for e in graph["edges"]]

    components = find_components(nodes, edges)
    node_component = {}
    for i, comp in enumerate(components):
        for n in comp:
            node_component[n] = i

    fig, ax = plt.subplots(figsize=(14, 14))
    colors = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(components), 1))

    for u, v in edges:
        ci = node_component[u]
        ax.plot([nodes[u][0], nodes[v][0]], [nodes[u][1], nodes[v][1]],
                color=colors(ci), linewidth=3, solid_capstyle="round")

    for nid, (x, y) in nodes.items():
        ci = node_component[nid]
        ax.scatter([x], [y], color=colors(ci), s=40, zorder=3, edgecolors="black", linewidths=0.5)
        ax.annotate(str(nid), (x, y), fontsize=7, xytext=(4, 4), textcoords="offset points")

    ax.set_title(f"Wall graph: {len(nodes)} nodes, {len(edges)} edges, "
                 f"{len(components)} component(s) -- each color = one disconnected piece")
    ax.invert_yaxis()   # image/plan coordinates: y grows downward
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"[visualize_wall_graph] {len(components)} components -> {out_path}")

    sizes = sorted(((len(c), i) for i, c in enumerate(components)), reverse=True)
    print("[visualize_wall_graph] component sizes (largest first):")
    for size, i in sizes:
        node_ids = components[i]
        xs = [nodes[n][0] for n in node_ids]
        ys = [nodes[n][1] for n in node_ids]
        print(f"    component {i}: {size} nodes, "
              f"bbox=({min(xs):.0f},{min(ys):.0f})-({max(xs):.0f},{max(ys):.0f})")


if __name__ == "__main__":
    graph_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/vector_wall_graph_v3.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/wall_graph_debug.png"
    main(graph_path, out_path)