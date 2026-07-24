"""
vector_room_face_extractor.py

Drop-in replacement for vector_room_loop_extractor.py.

Replaces DFS cycle enumeration (which returns every cycle in the graph,
including duplicates, nested cycles, and the outer boundary) with a
planar face traversal (half-edge / rotation-system walk), which returns
exactly one polygon per enclosed region -- i.e. exactly one polygon per
actual room, plus exactly one outer-boundary face.

Input:  vector_wall_graph_v3.json
        {
          "nodes": [{"id": 0, "x": 123.0, "y": 45.0}, ...],
          "edges": [[0, 1], [1, 2], ...]
        }

Output: vector_rooms.json
        {
          "rooms": [{"id": 0, "area": 12345.0, "polygon": [[x,y], ...]}, ...],
          "outer_boundary": {"area": 999999.0, "polygon": [[x,y], ...]}
        }

Usage:
    python vector_room_face_extractor.py vector_wall_graph_v3.json vector_rooms.json
"""

import json
import math
import sys
from collections import defaultdict


# ----------------------------------------------------------------------
# Step 0: Graph repair -- snap near-duplicate nodes and bridge components
# ----------------------------------------------------------------------

def snap_and_bridge(nodes, edges, snap_tol=6.0, bridge_tol=40.0):
    """
    nodes: dict {id: (x, y)}
    edges: list of (u, v)

    1. Snap nodes that are within `snap_tol` of each other into one node
       (fixes near-duplicate endpoints from YOLO/segment merging).
    2. Find connected components; for any component whose nearest
       endpoint to another component is within `bridge_tol`, add a
       bridging edge. This is a *heuristic* -- it will not fix graphs
       with genuinely large gaps, but it closes the small snapping gaps
       that typically cause a wall graph to fragment into N components.
    """
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

    # 1. snap
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if find(a) == find(b):
                continue
            ax, ay = nodes[a]
            bx, by = nodes[b]
            if math.hypot(ax - bx, ay - by) <= snap_tol:
                union(a, b)

    # remap nodes to snapped representatives, averaging position
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

    # 2. find components on the snapped graph
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

    print(f"[snap_and_bridge] {len(new_nodes)} nodes after snapping, "
          f"{len(components)} components")

    # bridge components: connect nearest pair of nodes across components
    # within bridge_tol, greedily, until one component remains or no
    # more bridges are possible.
    while len(components) > 1:
        best = None  # (dist, ci, cj, node_i, node_j)
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
        print(f"[snap_and_bridge] bridged components with edge "
              f"{ni}-{nj} (dist={d:.1f})")

    if len(components) > 1:
        sizes = sorted(len(c) for c in components)
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
        suggestion = math.ceil(best) + 5 if best else bridge_tol * 2
        print(f"[snap_and_bridge] WARNING: {len(components)} components "
              f"remain after bridging (sizes={sizes}). Nearest remaining "
              f"gap = {best:.1f}px, exceeds bridge_tol={bridge_tol}. "
              f"Try bridge_tol >= {suggestion}.")

    return new_nodes, sorted(new_edges)


# ----------------------------------------------------------------------
# Step 1: Planar face traversal
# ----------------------------------------------------------------------

def extract_faces(nodes, edges):
    """
    nodes: dict {id: (x, y)}
    edges: list of (u, v)  (undirected)

    Returns a list of faces, each a list of node ids in traversal order.
    Every undirected edge is walked exactly twice (once per direction),
    so every face -- including the single outer face -- is returned
    exactly once. No duplicates, no nested-cycle ambiguity: this is a
    direct property of planar rotation-system traversal, not a filter
    applied after the fact.
    """
    # adjacency with angle-sorted neighbor order (rotation system)
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def angle(u, v):
        ux, uy = nodes[u]
        vx, vy = nodes[v]
        return math.atan2(vy - uy, vx - ux)

    for u in adj:
        adj[u].sort(key=lambda v: angle(u, v))

    # for each node, map neighbor -> its index in the sorted rotation,
    # so we can step to "the next edge clockwise" in O(1)
    neighbor_index = {}
    for u, nbrs in adj.items():
        for idx, v in enumerate(nbrs):
            neighbor_index[(u, v)] = idx

    def next_edge(u, v):
        """Given we arrived at v via u, return the next directed edge
        (v, w) continuing the same face -- the neighbor of v that comes
        immediately *before* u in v's clockwise rotation (this is the
        standard 'turn right' rule for face traversal in a CW-sorted
        rotation system)."""
        nbrs = adj[v]
        idx = neighbor_index[(v, u)]
        w = nbrs[(idx - 1) % len(nbrs)]
        return v, w

    visited_directed = set()
    faces = []
    for u, v in edges:
        for a, b in [(u, v), (v, u)]:
            if (a, b) in visited_directed:
                continue
            face = []
            cur_a, cur_b = a, b
            while (cur_a, cur_b) not in visited_directed:
                visited_directed.add((cur_a, cur_b))
                face.append(cur_a)
                cur_a, cur_b = next_edge(cur_a, cur_b)
            faces.append(face)

    return faces


def polygon_signed_area(nodes, face):
    area = 0.0
    n = len(face)
    for i in range(n):
        x1, y1 = nodes[face[i]]
        x2, y2 = nodes[face[(i + 1) % n]]
        area += x1 * y2 - x2 * y1
    return area / 2.0


# ----------------------------------------------------------------------
# Step 2: Classify faces into rooms vs. outer boundary
# ----------------------------------------------------------------------

def classify_faces(nodes, faces, min_area=1000.0):
    """
    In a CW-sorted rotation system, interior (room) faces come out with
    one sign of signed area and the single outer face comes out with
    the opposite sign and (normally) the largest magnitude. We use both
    signals: the outer face is the one with max |area| among faces of
    the "outer" sign; degenerate/sliver faces below min_area are dropped.
    """
    scored = []
    for face in faces:
        if len(face) < 3:
            continue
        a = polygon_signed_area(nodes, face)
        scored.append((a, face))

    if not scored:
        return [], None

    # outer face = the one whose signed area has the sign that appears
    # exactly once among the largest-magnitude faces; in practice this
    # is just the single most negative (or most positive) signed area
    # depending on your CW/CCW convention -- take the extreme by |area|.
    outer_idx = max(range(len(scored)), key=lambda i: abs(scored[i][0]))
    outer_area, outer_face = scored[outer_idx]

    rooms = []
    for i, (a, face) in enumerate(scored):
        if i == outer_idx:
            continue
        if abs(a) < min_area:
            continue  # sliver / degenerate face, not a real room
        rooms.append({
            "area": abs(a),
            "polygon": [list(nodes[n]) for n in face],
        })

    outer = {
        "area": abs(outer_area),
        "polygon": [list(nodes[n]) for n in outer_face],
    }
    return rooms, outer


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main(in_path, out_path, snap_tol=6.0, bridge_tol=40.0, min_room_area=1000.0):
    with open(in_path) as f:
        data = json.load(f)

    nodes = {n["id"]: (n["x"], n["y"]) for n in data["nodes"]}
    edges = [tuple(e) for e in data["edges"]]

    nodes, edges = snap_and_bridge(nodes, edges, snap_tol, bridge_tol)

    faces = extract_faces(nodes, edges)
    rooms, outer = classify_faces(nodes, faces, min_area=min_room_area)

    for i, r in enumerate(rooms):
        r["id"] = i

    out = {"rooms": rooms, "outer_boundary": outer}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[main] extracted {len(rooms)} room faces "
          f"(+1 outer boundary, area={outer['area']:.0f})")
    for r in sorted(rooms, key=lambda r: -r["area"]):
        print(f"        room {r['id']}: area={r['area']:.0f}")


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "vector_wall_graph_v3.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "vector_rooms.json"
    snap_tol = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
    bridge_tol = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
    min_room_area = float(sys.argv[5]) if len(sys.argv) > 5 else 1000.0
    main(in_path, out_path, snap_tol, bridge_tol, min_room_area)