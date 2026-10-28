"""Interactive 3D viewer: both graphs as one local HTML page (3d-force-graph / Three.js).

  demo   the fictitious door harness + E/E model, layers as planes in space
  real   the public VW "Old Beetle" main harness: connectors = nodes, connections = links
  geo    the same harness as routed in the car (KBL geometry, see kbl_geometry.py)

Scenario buttons replay the SPARQL questions visually; each shows the query behind it.
Usage: python src/export_viewer.py   ->  build/viewer.html
"""
import json
import textwrap
from collections import defaultdict

from rdflib import Literal, RDF, RDFS

from build_graph import ROOT, build
from kbl_geometry import geometry
from plot_graph import ISSUES, LAYERS, short, view_graph

# every text shown on the page exists in German and English: {"de": ..., "en": ...}
LAYERS_EN = ["Function", "Signal", "Wire", "Connector", "Device"]
FINDINGS_EN = ["Wire thinner than the signal requires", "Signal in the E/E model but not routed in the harness",
               "Signal name in the harness that the E/E model does not know"]
from real_kbl import QUESTIONS as REAL_Q, convert
from run_queries import PREFIXES, QUESTIONS as DEMO_Q


def local(term):
    return str(term).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def name(g, term):
    if isinstance(term, Literal):
        return str(term)
    return str(g.value(term, RDFS.label) or local(term))


def triples(g, n):
    """All triples around one RDF node, for the details panel ("this is what the graph knows")."""
    out = []
    for p, o in sorted(g.predicate_objects(n)):
        if p != RDFS.label:
            out.append(["→", local(p), local(o) if p == RDF.type else name(g, o)])
    for s, p in sorted(g.subject_predicates(n)):
        out.append(["←", local(p), name(g, s)])
    return out


def query_text(q):
    return textwrap.dedent(q).strip()


# ---------------------------------------------------------------- demo
def reach(G, start, step):
    """Follow edges layer by layer in one direction (+1 towards devices, -1 towards functions)."""
    seen, todo = {start}, [start]
    while todo:
        n = todo.pop()
        for m in G[n]:
            if G.nodes[m]["layer"] == G.nodes[n]["layer"] + step and m not in seen:
                seen.add(m)
                todo.append(m)
    return seen


def summary(G, nodes, layers):
    by_layer = defaultdict(list)
    for n in sorted(nodes):
        by_layer[G.nodes[n]["layer"]].append(n)
    return " · ".join(f"{layers[l]}: {', '.join(by_layer[l])}" for l in sorted(by_layer))


def both(de, en):
    return {"de": de, "en": en}


def demo_data():
    g = build()
    G = view_graph(g)
    nodes = [{"id": n, "layer": d["layer"], "issue": n in ISSUES,
              "title": name(g, d["uri"]), "triples": triples(g, d["uri"])}
             for n, d in G.nodes(data=True)]
    links = []
    for a, b, d in G.edges(data=True):
        if G.nodes[a]["layer"] > G.nodes[b]["layer"]:
            a, b = b, a
        links.append({"source": a, "target": b, "kind": d["kind"]})

    trace = reach(G, "F_FH", +1)
    impact = reach(G, "X4", -1) | reach(G, "X4", +1)
    issues = set(ISSUES) | {m for n in ISSUES for m in G[n]}
    findings_de, findings_en = [], []
    for (title, q, _), title_en in zip(DEMO_Q[4:7], FINDINGS_EN):
        rows = "; ".join(" / ".join(str(v) for v in r) for r in g.query(PREFIXES + q))
        findings_de.append(f"{title.split(':', 1)[1].strip()}: {rows}")
        findings_en.append(f"{title_en}: {rows}")
    scenarios = [
        {"title": both("Traceability: Fensterheber", "Traceability: window lifter"),
         "text": both("Von der Funktion über ihre Signale und Leitungen bis zu Steckern und Geräten. " + summary(G, trace, LAYERS),
                      "From the function via its signals and wires to connectors and devices. " + summary(G, trace, LAYERS_EN)),
         "nodes": sorted(trace), "query": query_text(DEMO_Q[0][1])},
        {"title": both("Änderung an Stecker X4", "Change to connector X4"),
         "text": both("Rückwärts zu Leitungen, Signalen und Funktionen, vorwärts zum Gerät. " + summary(G, impact, LAYERS),
                      "Backwards to wires, signals and functions, forwards to the device. " + summary(G, impact, LAYERS_EN)),
         "nodes": sorted(impact), "query": query_text(DEMO_Q[1][1])},
        {"title": both("Konsistenzfehler", "Consistency errors"),
         "text": both(" · ".join(findings_de), " · ".join(findings_en)),
         "nodes": sorted(issues), "query": "\n\n".join(query_text(q) for _, q, _ in DEMO_Q[4:7])},
    ]
    return {"nodes": nodes, "links": links, "layers": both(LAYERS, LAYERS_EN), "scenarios": scenarios,
            "stats": both(f"{len(g)} Tripel · {len(nodes)} Knoten · {len(links)} Kanten (Kontakte und Verbindungen zusammengefasst)",
                          f"{len(g)} triples · {len(nodes)} nodes · {len(links)} edges (contacts and connections merged)")}


# ---------------------------------------------------------------- real
def real_data():
    g = convert()
    q = lambda text: g.query(PREFIXES + text)

    connectors = {}
    for x, label, desc in q("""SELECT ?x ?label ?desc WHERE { ?x a bn:Connector ; rdfs:label ?label .
                                OPTIONAL { ?x rdfs:comment ?desc } }"""):
        connectors[short(x)] = {"id": short(x), "label": str(label), "desc": str(desc or "")}

    modules = {short(m): {"id": short(m), "label": str(label), "code": str(code), "links": 0, "configs": []}
               for m, label, code in q("SELECT ?m ?label ?code WHERE { ?m a bn:Module ; rdfs:label ?label ; bn:optionCode ?code }")}
    configs = defaultdict(list)
    for cfg, label, m in q("""SELECT ?cfg ?label ?m WHERE { ?cfg a bn:Configuration ; rdfs:label ?label .
                              OPTIONAL { ?cfg bn:includesModule ?m } }"""):
        configs[str(label)]
        if m is not None:
            configs[str(label)].append(short(m))
            modules[short(m)]["configs"].append(str(label))
    mini = set(configs.get("Kombination_MINI", []))

    member = defaultdict(list)
    for c, m in q("SELECT ?c ?m WHERE { ?c a bn:Connection ; bn:belongsToModule ?m }"):
        member[short(c)].append(short(m))

    every = []  # all connections; only those with both ends on a connector are drawn
    for c, label, signal, wire, mm2, length, a, b in q("""
        SELECT ?c ?label ?signal ?wire ?mm2 ?len ?a ?b WHERE {
          ?c a bn:Connection ; rdfs:label ?label .
          OPTIONAL { ?c bn:carriesSignal/bn:signalName ?signal }
          OPTIONAL { ?c bn:realisedBy ?w . ?w rdfs:label ?wire .
                     OPTIONAL { ?w bn:crossSectionMm2 ?mm2 } OPTIONAL { ?w bn:lengthMm ?len } }
          OPTIONAL { ?c bn:fromContact ?ca . ?a bn:hasContactPoint ?ca }
          OPTIONAL { ?c bn:toContact ?cb . ?b bn:hasContactPoint ?cb } }"""):
        mods = member[short(c)]
        for m in mods:
            modules[m]["links"] += 1
        every.append({"id": short(c), "source": short(a) if a else None, "target": short(b) if b else None,
                      "label": str(label),
                      "signal": str(signal or ""), "wire": str(wire or ""),
                      "mm2": float(mm2) if mm2 is not None else None,
                      "length": int(length) if length is not None else None,
                      "modules": mods, "inMini": bool(mini & set(mods))})
    # an end on a special contact outside a connector is not drawn (see README)
    links = [l for l in every if l["source"] and l["target"]]
    unmapped = len(every) - len(links)

    degree = defaultdict(int)
    for link in links:
        degree[link["source"]] += 1
        degree[link["target"]] += 1
    for cid, c in connectors.items():
        c["degree"] = degree[cid]

    # scenarios, derived from the data (same questions as real_kbl.py)
    by_signal = defaultdict(list)
    for link in every:
        by_signal[link["signal"]].append(link)
    top_signal = max(by_signal, key=lambda s: len(by_signal[s]))
    ts = by_signal[top_signal]
    top_con = max(connectors, key=lambda c: degree[c])
    tc = [l for l in links if top_con in (l["source"], l["target"])]
    maxi_only = [l for l in every if not l["inMini"]]
    has_member = {short(m) for (m,) in q("SELECT DISTINCT ?m WHERE { ?x bn:belongsToModule ?m }")}
    empty = [m for m in modules.values() if m["id"] not in has_member]
    lengths = " vs. ".join(f"{cfg_label.split('_')[-1]} {m} m" for cfg_label, _, m in q(REAL_Q[2][1]))
    sections = " / ".join(sorted({f"{l['mm2']:g}" for l in ts if l["mm2"]}))
    via = ", ".join(sorted({connectors[x]["label"] for l in ts for x in (l["source"], l["target"]) if x}))
    con = connectors[top_con]["label"]
    n_sig, n_mod = len({l["signal"] for l in tc}), len({m for l in tc for m in l["modules"]})
    codes = ", ".join(sorted({modules[m]["code"] for l in tc for m in l["modules"]}))
    scenarios = [
        {"title": both(f"Signal {top_signal}", f"Signal {top_signal}"),
         "text": both(f"Meistgenutztes Signal: {len(ts)} Verbindungen mit {sections} mm², über die Stecker {via}.",
                      f"Most-used signal: {len(ts)} connections with {sections} mm², via the connectors {via}."),
         "links": [l["id"] for l in ts], "query": query_text(REAL_Q[4][1])},
        {"title": both(f"Änderung an Stecker {con}", f"Change to connector {con}"),
         "text": both(f"Der Stecker mit den meisten Verbindungen: {len(tc)} Verbindungen, {n_sig} Signale, {n_mod} Module ({codes}).",
                      f"The connector with the most connections: {len(tc)} connections, {n_sig} signals, {n_mod} modules ({codes})."),
         "links": [l["id"] for l in tc], "nodes": [top_con], "query": query_text(REAL_Q[5][1])},
        {"title": both("Nur in MAXI", "Only in MAXI"),
         "text": both(f"{len(maxi_only)} von {len(every)} Verbindungen gibt es nur in der Konfiguration MAXI (Leitungslänge: {lengths}).",
                      f"{len(maxi_only)} of {len(every)} connections exist only in the MAXI configuration (wire length: {lengths})."),
         "links": [l["id"] for l in maxi_only], "query": query_text(REAL_Q[3][1])},
        {"title": both("Modul ohne Inhalt", "Empty module"),
         "text": both(" ".join(f"Modul {m['label']} hat die Ausstattungsregel {m['code']}, aber keine Bauteile." for m in empty)
                      + " Im Graphen ist das eine einzige Abfrage.",
                      " ".join(f"Module {m['label']} has the option rule {m['code']} but no parts." for m in empty)
                      + " In the graph this is a single query."),
         "links": [], "query": query_text(REAL_Q[6][1])},
    ]
    return {"nodes": list(connectors.values()), "links": links,
            # every connection (also those ending on a special contact), for the geometry view
            "all": [{k: l[k] for k in ("id", "label", "signal", "wire", "mm2", "modules", "inMini", "source", "target")}
                    for l in every],
            "modules": sorted(modules.values(), key=lambda m: -m["links"]),
            "configs": {k: v for k, v in configs.items() if v}, "scenarios": scenarios,
            "stats": both(f"{len(g)} Tripel · {len(connectors)} Stecker · {len(links)} Verbindungen "
                          f"({unmapped} mit Sonderkontakt nicht dargestellt) · {len(modules)} Module",
                          f"{len(g)} triples · {len(connectors)} connectors · {len(links)} connections "
                          f"({unmapped} ending on a special contact not drawn) · {len(modules)} modules")}


def main():
    data = {"demo": demo_data(), "real": real_data(), "geo": geometry()}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (ROOT / "src/viewer_template.html").read_text(encoding="utf-8").replace("/*DATA*/null", payload)
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/viewer.html").write_text(html, encoding="utf-8")
    print("build/viewer.html")


if __name__ == "__main__":
    main()
