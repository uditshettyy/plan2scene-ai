"""
build_connected_wall_graph.py

Stage: wall segments -> connected graph

Input:  outputs/wall_segments.json  (from extract_wall_segments.py)
Output: outputs/vector_wall_graph_v3.json
        {
          "nodes": [{"id": 0, "x": ..., "y": ...}, ...],
          "edges": [[u, v], ...],
          "edge_thickness": {"0-1": 12.0, ...}
        }

This turns each wall segment's two endpoints into graph nodes (deduping
endpoints shared between segments), then runs the same snap + bridge
repair used in vector_room_face_extractor.py so the graph is a single
connected component before room-face extraction runs.

Usage:
    python build_connected_wall_graph.py outputs/wall_segments.json outputs/vector_wall_graph_v3.json
"""

import json
import math
import sys
from collections import defaultdict

SNAP_TOL = 6.0
BRIDGE_TOL = 40.0


def segments_to_graph(walls):
    """Dedupe endpoints into nodes, build edge list, track thickness per edge."""
    node_id_of = {}
    nodes = {}
    next_id = 0

    def get_node(pt):
        nonlocal next_id
        # exact-key dedupe pass; fine-grained snapping happens next stage
        key = (round(pt[0], 1), round(pt[1], 1))
        if key not in node_id_of:
            node_id_of[key] = next_id
            nodes[next_id] = (pt[0], pt[1])
            next_id += 1
        return node_id_of[key]

    edges = []
    thickness = {}
    for w in walls:
        u = get_node(w["p1"])
        v = get_node(w["p2"])
        if u == v:
            continue
        e = (min(u, v), max(u, v))
        edges.append(e)
        thickness[e] = max(thickness.get(e, 0), w.get("thickness", 10.0))

    return nodes, sorted(set(edges)), thickness


def snap_and_bridge(nodes, edges, snap_tol=SNAP_TOL, bridge_tol=BRIDGE_TOL):
    """Same connectivity repair as used for room extraction: merge
    near-duplicate nodes, then greedily bridge disconnected components
    whose nearest endpoints are within bridge_tol."""
    ids = list(nodes.keys())
    parent = {i: i for i in ids}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if find(a) == find(b):
                continue
            ax, ay = nodes[a]
            bx, by = nodes[b]
            if math.hypot(ax - bx, ay - by) <= snap_tol:
                union(a, b)

    groups = defaultdict(list)
    for i in ids:
        groups[find(i)].append(i)

    remap = {}
    new_nodes = {}
    for rep, members in groups.items():
        xs = [nodes[m][0] for m in members]
        ys = [nodes[m][1] for m in members]
        new_nodes[rep] = (sum(xs) / len(xs), sum(ys) / len(ys))
        for m in members:
            remap[m] = rep

    new_edges = set()
    for u, v in edges:
        ru, rv = remap[u], remap[v]
        if ru != rv:
            new_edges.add((min(ru, rv), max(ru, rv)))

    adj = defaultdict(set)
    for u, v in new_edges:
        adj[u].add(v)
        adj[v].add(u)

    visited = set()
    components = []
    for n in new_nodes:
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

    def nearest_gap():
        best = None
        for ci in range(len(components)):
            for cj in range(ci + 1, len(components)):
                for ni in components[ci]:
                    xi, yi = new_nodes[ni]
                    for nj in components[cj]:
                        xj, yj = new_nodes[nj]
                        d = math.hypot(xi - xj, yi - yj)
                        if best is None or d < best:
                            best = d
        return best

    if len(components) > 1:
        gap = nearest_gap()
        print(f"[build_connected_wall_graph] {len(components)} components before "
              f"bridging; nearest gap = {gap:.1f}px (bridge_tol={bridge_tol})")

    while len(components) > 1:
        best = None
        for ci in range(len(components)):
            for cj in range(ci + 1, len(components)):
                for ni in components[ci]:
                    xi, yi = new_nodes[ni]
                    for nj in components[cj]:
                        xj, yj = new_nodes[nj]
                        d = math.hypot(xi - xj, yi - yj)
                        if best is None or d < best[0]:
                            best = (d, ci, cj, ni, nj)
        if best is None or best[0] > bridge_tol:
            break
        d, ci, cj, ni, nj = best
        new_edges.add((min(ni, nj), max(ni, nj)))
        merged = components[ci] + components[cj]
        components = [c for k, c in enumerate(components) if k not in (ci, cj)]
        components.append(merged)

    if len(components) > 1:
        gap = nearest_gap()
        print(f"[build_connected_wall_graph] STILL {len(components)} components "
              f"after bridging; nearest remaining gap = {gap:.1f}px. "
              f"Re-run with --bridge-tol {math.ceil(gap) + 5 if gap else bridge_tol * 2} "
              f"or higher to close it.")

    return new_nodes, sorted(new_edges), components, remap


def main(in_path, out_path, snap_tol=SNAP_TOL, bridge_tol=BRIDGE_TOL):
    with open(in_path) as f:
        data = json.load(f)
    walls = data["walls"]

    nodes, edges, thickness = segments_to_graph(walls)
    print(f"[build_connected_wall_graph] {len(nodes)} nodes, {len(edges)} edges "
          f"before connectivity repair")

    nodes, edges, components, remap = snap_and_bridge(nodes, edges, snap_tol, bridge_tol)
    print(f"[build_connected_wall_graph] {len(nodes)} nodes, {len(edges)} edges, "
          f"{len(components)} component(s) after repair")

    if len(components) > 1:
        print(f"[build_connected_wall_graph] WARNING: graph still has "
              f"{len(components)} components. Room extraction will still run, "
              f"but rooms spanning the gap will not close correctly. Consider "
              f"raising bridge_tol or checking source wall detections near the gap.")

    # remap thickness keys through the same node remapping
    new_thickness = {}
    for (u, v), th in thickness.items():
        ru, rv = remap.get(u, u), remap.get(v, v)
        if ru == rv:
            continue
        key = f"{min(ru, rv)}-{max(ru, rv)}"
        new_thickness[key] = max(new_thickness.get(key, 0), th)

    out = {
        "nodes": [{"id": nid, "x": x, "y": y} for nid, (x, y) in nodes.items()],
        "edges": [[u, v] for u, v in edges],
        "edge_thickness": new_thickness,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/wall_segments.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/vector_wall_graph_v3.json"
    snap_tol = float(sys.argv[3]) if len(sys.argv) > 3 else SNAP_TOL
    bridge_tol = float(sys.argv[4]) if len(sys.argv) > 4 else BRIDGE_TOL
    main(in_path, out_path, snap_tol, bridge_tol)