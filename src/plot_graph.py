"""Draw the graph as one picture: Function -> Signal -> Wire -> Connector -> Device.

Contact points and connections are folded into the wire edges so the picture stays
readable.  Elements that a consistency check flags (run_queries.py, 4a-4c) are red.

Usage: python src/plot_graph.py   ->  build/graph.png, build/graph.svg
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from rdflib import RDF

from build_graph import BN, ROOT, build

LAYERS = ["Funktion", "Signal", "Leitung", "Stecker", "Gerät"]
COLOURS = ["#1f4e79", "#2e86c1", "#17a589", "#7d8c99", "#34495e"]
ISSUE = "#c0392b"
# flagged by the consistency checks (see run_queries.py)
ISSUES = {"W05", "AMB_LED_PWN", "AMB_LED_PWM", "SP_HEIZ"}


def short(node):
    return str(node).rsplit("/", 1)[-1]


def view_graph(g):
    """Folded view of the RDF graph: one node per function, signal, wire, connector and
    device (attribute layer 0-4, uri = the RDF node); edge attribute kind = how they relate."""
    G = nx.Graph()

    def node(n, layer):
        G.add_node(short(n), layer=layer, uri=n)
        return short(n)

    for f, s in g.subject_objects(BN.usesSignal):
        G.add_edge(node(f, 0), node(s, 1), kind="usesSignal")
    for c in g.subjects(RDF.type, BN.Connection):
        s, w = g.value(c, BN.carriesSignal), g.value(c, BN.realisedBy)
        G.add_edge(node(s, 1), node(w, 2), kind="carriesSignal / realisedBy")
        for end in (BN.fromContact, BN.toContact):
            con = g.value(predicate=BN.hasContactPoint, object=g.value(c, end))
            G.add_edge(node(w, 2), node(con, 3), kind="fromContact / toContact")
    for con, dev in g.subject_objects(BN.pluggedInto):
        G.add_edge(node(con, 3), node(dev, 4), kind="pluggedInto")
    return G


def layered_layout(G, sweeps=6):
    """One column per layer; nodes in a column sorted by the mean rank of their
    neighbours (barycenter heuristic), sweeping left/right to cut edge crossings."""
    cols = [sorted(n for n, d in G.nodes(data=True) if d["layer"] == i) for i in range(len(LAYERS))]
    rank = {n: i for col in cols for i, n in enumerate(col)}
    for sweep in range(sweeps):
        order = range(1, len(cols)) if sweep % 2 == 0 else range(len(cols) - 2, -1, -1)
        for i in order:
            ref = i - 1 if sweep % 2 == 0 else i + 1
            def bary(n):
                nb = [rank[m] / max(len(cols[ref]) - 1, 1) for m in G[n] if G.nodes[m]["layer"] == ref]
                return sum(nb) / len(nb) if nb else rank[n] / max(len(cols[i]) - 1, 1)
            cols[i].sort(key=bary)
            rank.update({n: k for k, n in enumerate(cols[i])})
    pos = {}
    for i, col in enumerate(cols):
        for k, n in enumerate(col):
            pos[n] = (i / (len(cols) - 1) * 2 - 1, 1 - 2 * (k + 0.5) / len(col))
    return pos


def main():
    G = view_graph(build())
    pos = layered_layout(G)
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=150)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#b8c4ce", width=1.0)
    for i, colour in enumerate(COLOURS):
        nodes = [n for n, d in G.nodes(data=True) if d["layer"] == i]
        nx.draw_networkx_nodes(G, pos, nodelist=nodes, ax=ax, node_size=520,
                               node_color=[ISSUE if n in ISSUES else colour for n in nodes])
    for n, (x, y) in pos.items():
        ax.text(x + 0.035, y, n, fontsize=7.5, va="center", color=ISSUE if n in ISSUES else "#222",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    xs = sorted({round(x, 3) for x, _ in pos.values()})
    for x, name in zip(xs, LAYERS):
        ax.text(x, 1.08, name, ha="center", fontsize=11, fontweight="bold", color="#1f2d3a")
    ax.text(xs[0], -1.12, "rot = von den Konsistenzprüfungen gefunden", fontsize=8.5, color=ISSUE)
    ax.set_xlim(xs[0] - 0.12, xs[-1] + 0.25)
    ax.set_ylim(-1.18, 1.15)
    ax.axis("off")
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(ROOT / f"build/graph.{ext}", bbox_inches="tight")
    print("build/graph.png, build/graph.svg")


if __name__ == "__main__":
    main()
