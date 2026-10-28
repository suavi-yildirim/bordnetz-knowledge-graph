"""Build one semantic graph from two separate sources:

  data/door_harness_kbl.xml   harness view   (KBL-like: connectors, wires, connections, modules)
  data/ee_architecture.json   E/E view       (functions, ECUs, signals, configurations)

The two sources only share *names* (signal names, connector IDs, module IDs).
The graph turns these names into explicit links, so questions across both views
(traceability, change impact, variants, consistency) become simple SPARQL queries.

Usage: python src/build_graph.py   ->  build/bordnetz.ttl
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parent.parent
BN = Namespace("https://example.org/bordnetz#")
DATA = Namespace("https://example.org/bordnetz/data/")


def uri(kind, ident):
    """Naming convention for instances: data:<kind>/<ID>, e.g. data:wire/W01."""
    return DATA[f"{kind}/{ident}"]


def add_harness(g, path):
    """KBL-like XML -> triples. Provenance of every element: sourceSystem 'KBL'."""
    harness = ET.parse(path).getroot().find("Harness")
    h = uri("harness", harness.get("id"))
    g.add((h, RDF.type, BN.Harness))
    g.add((h, RDFS.label, Literal(harness.get("description"), lang="de")))
    g.add((h, BN.partNumber, Literal(harness.get("part_number"))))

    for con in harness.iter("Connector_occurrence"):
        c = uri("connector", con.get("id"))
        g.add((c, RDF.type, BN.Connector))
        g.add((c, RDFS.label, Literal(f"{con.get('id')} {con.get('description')}", lang="de")))
        g.add((c, BN.partNumber, Literal(con.get("part_number"))))
        g.add((c, BN.sourceSystem, Literal("KBL")))
        g.add((h, BN.hasConnector, c))
        for cp in con.iter("Contact_point"):
            p = uri("contact", cp.get("id"))
            g.add((p, RDF.type, BN.ContactPoint))
            g.add((p, RDFS.label, Literal(cp.get("id"))))
            g.add((c, BN.hasContactPoint, p))

    for wire in harness.iter("Wire_occurrence"):
        w = uri("wire", wire.get("id"))
        g.add((w, RDF.type, BN.Wire))
        g.add((w, RDFS.label, Literal(wire.get("id"))))
        g.add((w, BN.crossSectionMm2, Literal(wire.get("cross_section_mm2"), datatype=XSD.decimal)))
        g.add((w, BN.lengthMm, Literal(int(wire.get("length_mm")))))
        g.add((w, BN.colour, Literal(wire.get("colour"))))
        g.add((w, BN.sourceSystem, Literal("KBL")))

    for conn in harness.iter("Connection"):
        c = uri("connection", conn.get("id"))
        a, b = (e.get("contact_point") for e in conn.iter("Extremity"))
        g.add((c, RDF.type, BN.Connection))
        g.add((c, RDFS.label, Literal(conn.get("id"))))
        g.add((c, BN.realisedBy, uri("wire", conn.get("wire"))))
        g.add((c, BN.fromContact, uri("contact", a)))
        g.add((c, BN.toContact, uri("contact", b)))
        # KBL only knows the signal *name*. Linking by name is the join between the views;
        # a name the E/E model does not know becomes a signal without E/E data (see query 4c).
        s = uri("signal", conn.get("signal_name"))
        g.add((c, BN.carriesSignal, s))
        g.add((s, RDF.type, BN.Signal))
        g.add((s, BN.signalName, Literal(conn.get("signal_name"))))

    for mod in harness.iter("Module"):
        m = uri("module", mod.get("id"))
        g.add((m, RDF.type, BN.Module))
        g.add((m, RDFS.label, Literal(mod.get("description"), lang="de")))
        for comp in mod.iter("Controlled_component"):
            g.add((uri("wire", comp.get("ref")), BN.belongsToModule, m))


def add_ee(g, path):
    """E/E architecture JSON -> triples. Provenance: sourceSystem 'E/E'."""
    ee = json.loads(Path(path).read_text(encoding="utf-8"))

    for d in ee["devices"]:
        dev = uri("device", d["id"])
        g.add((dev, RDF.type, BN[d["type"]]))
        g.add((dev, RDFS.label, Literal(d["label"], lang="de")))
        g.add((uri("connector", d["connector"]), BN.pluggedInto, dev))

    for s in ee["signals"]:
        sig = uri("signal", s["name"])
        g.add((sig, RDF.type, BN.Signal))
        g.add((sig, RDFS.label, Literal(s["label"], lang="de")))
        g.add((sig, BN.signalName, Literal(s["name"])))
        g.add((sig, BN.providedBy, uri("device", s["from"])))
        g.add((sig, BN.consumedBy, uri("device", s["to"])))
        g.add((sig, BN.requiredCrossSectionMm2,
               Literal(str(s["min_cross_section_mm2"]), datatype=XSD.decimal)))
        g.add((sig, BN.sourceSystem, Literal("E/E")))

    for f in ee["functions"]:
        fn = uri("function", f["id"])
        g.add((fn, RDF.type, BN.Function))
        g.add((fn, RDFS.label, Literal(f["label"], lang="de")))
        g.add((fn, BN.allocatedTo, uri("device", f["ecu"])))
        g.add((fn, BN.requiresModule, uri("module", f["module"])))
        for s in f["signals"]:
            g.add((fn, BN.usesSignal, uri("signal", s)))

    for c in ee["configurations"]:
        cfg = uri("configuration", c["id"])
        g.add((cfg, RDF.type, BN.Configuration))
        g.add((cfg, RDFS.label, Literal(c["label"], lang="de")))
        for m in c["modules"]:
            g.add((cfg, BN.includesModule, uri("module", m)))


def build():
    g = Graph()
    g.bind("bn", BN)
    g.bind("data", DATA)
    g.parse(ROOT / "ontology/bordnetz.ttl")
    add_harness(g, ROOT / "data/door_harness_kbl.xml")
    add_ee(g, ROOT / "data/ee_architecture.json")
    return g


if __name__ == "__main__":
    g = build()
    out = ROOT / "build/bordnetz.ttl"
    out.parent.mkdir(exist_ok=True)
    g.serialize(out, format="turtle")
    print(f"{len(g)} triples -> {out.relative_to(ROOT)}")
