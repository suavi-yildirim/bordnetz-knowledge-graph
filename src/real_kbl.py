"""Real KBL (VDA 4964) -> the same ontology, then variant and consistency questions.

Input:  data/real/ (public Volkswagen VOBES "Old Beetle" sample, prostep ivip ECAD wiki,
        CC BY-SA 4.0).  KBL has no E/E data (functions, ECUs), so this graph covers the
        harness and the variant view: connectors, contacts, wires and cores, connections
        with signal names, modules with option codes, harness configurations.

Usage:  python src/real_kbl.py   ->  build/oldbeetle.ttl, build/results_oldbeetle.md
"""
import xml.etree.ElementTree as ET
from collections import Counter
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD

from build_graph import BN, ROOT
from run_queries import PREFIXES, table

SRC = ROOT / "data/real/kblxml_2.4sr-1_tab016120_modulare_ltgs._160718.kbl"
OB = Namespace("https://example.org/bordnetz/oldbeetle/")
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"
# KBL tag of a controlled component -> instance kind in the graph
MODULE_MEMBERS = {"Connection": "connection", "General_wire_occurrence": "wire",
                  "Connector_occurrence": "connector"}


def uri(kind, ident):
    return OB[f"{kind}/{quote(ident, safe='')}"]


def number(el, path):
    """KBL numerical value: <path><Unit_component/><Value_component>1.5</Value_component></path>."""
    v = el.findtext(f"{path}/Value_component") if el is not None else None
    return float(v) if v else None


def convert(path=SRC):
    root = ET.parse(path).getroot()
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}  # KBL links by XML id
    h = root.find("Harness")
    g = Graph()
    g.bind("bn", BN)
    g.bind("ob", OB)
    g.parse(ROOT / "ontology/bordnetz.ttl")

    hn = uri("harness", h.get("id"))
    g.add((hn, RDF.type, BN.Harness))
    g.add((hn, RDFS.label, Literal(h.findtext("Description"))))
    g.add((hn, BN.partNumber, Literal(h.findtext("Part_number"))))

    for co in h.findall("Connector_occurrence"):
        c = uri("connector", co.get("id"))
        g.add((c, RDF.type, BN.Connector))
        g.add((c, RDFS.label, Literal(co.findtext("Id"))))
        housing = byid.get(co.findtext("Part"))
        if housing is not None:
            g.add((c, RDFS.comment, Literal(housing.findtext("Description"))))
        g.add((hn, BN.hasConnector, c))
        for cp in co.findall("Contact_points"):
            p = uri("contact", cp.get("id"))
            g.add((p, RDF.type, BN.ContactPoint))
            g.add((p, RDFS.label, Literal(cp.findtext("Id"))))
            g.add((c, BN.hasContactPoint, p))

    def add_wire(xid, label, part, length):
        w = uri("wire", xid)
        g.add((w, RDF.type, BN.Wire))
        g.add((w, RDFS.label, Literal(label)))
        g.add((w, BN.sourceSystem, Literal("KBL")))
        cs = number(part, "Cross_section_area")
        if cs is not None:
            g.add((w, BN.crossSectionMm2, Literal(str(cs), datatype=XSD.decimal)))
        if length is not None:
            g.add((w, BN.lengthMm, Literal(round(length))))
        return w

    for wo in h.findall("General_wire_occurrence"):
        part = byid.get(wo.findtext("Part"))
        length = number(wo, "Length_information/Length_value")
        label = wo.findtext("Wire_number") or wo.findtext("Special_wire_id") or wo.get("id")
        w = add_wire(wo.get("id"), label, part, length)
        g.add((w, RDFS.comment, Literal(wo.get(XSI_TYPE, "").replace("kbl:", ""))))
        # multicore cable: every core is a wire of its own (a connection can run on a core)
        for core in wo.findall("Core_occurrence"):
            cl = number(core, "Length_information/Length_value")
            cw = add_wire(core.get("id"), core.findtext("Wire_number") or core.get("id"),
                          byid.get(core.findtext("Part")), cl if cl is not None else length)
            g.add((cw, BN.coreOf, w))

    for cn in h.findall("Connection"):
        c = uri("connection", cn.get("id"))
        g.add((c, RDF.type, BN.Connection))
        g.add((c, RDFS.label, Literal(cn.findtext("Id"))))
        if cn.findtext("Wire"):
            g.add((c, BN.realisedBy, uri("wire", cn.findtext("Wire"))))
        name = cn.findtext("Signal_name")
        if name:
            s = uri("signal", name)
            g.add((s, RDF.type, BN.Signal))
            g.add((s, BN.signalName, Literal(name)))
            g.add((c, BN.carriesSignal, s))
        ends = [e.findtext("Contact_point") for e in cn.findall("Extremities")]
        for prop, cp in zip((BN.fromContact, BN.toContact), ends):
            if cp:
                g.add((c, prop, uri("contact", cp)))

    for m in h.findall("Module"):
        mod = uri("module", m.get("id"))
        mc = m.find("Module_configuration")
        g.add((mod, RDF.type, BN.Module))
        g.add((mod, RDFS.label, Literal(m.findtext("Part_number"))))
        g.add((mod, BN.optionCode, Literal(mc.findtext("Logistic_control_information") or "")))
        for ref in (mc.findtext("Controlled_components") or "").split():
            kind = MODULE_MEMBERS.get(byid[ref].tag) if ref in byid else None
            if kind:
                g.add((uri(kind, ref), BN.belongsToModule, mod))

    for hc in h.findall("Harness_configuration"):
        cfg = uri("configuration", hc.get("id"))
        g.add((cfg, RDF.type, BN.Configuration))
        g.add((cfg, RDFS.label, Literal(hc.findtext("Car_classification_level_4") or hc.get("id"))))
        for ref in (hc.findtext("Modules") or "").split():
            g.add((cfg, BN.includesModule, uri("module", ref)))
    return g


QUESTIONS = [
    ("0  Überblick: Instanzen je Klasse",
     """SELECT ?class (COUNT(?x) AS ?count) WHERE {
          ?x a ?c . ?c rdfs:label ?class . FILTER (lang(?class) = "de") }
        GROUP BY ?class ORDER BY DESC(?count)"""),
    ("1  Varianten: Umfang je Leitungssatz-Konfiguration",
     """SELECT ?configuration (COUNT(DISTINCT ?m) AS ?modules) (COUNT(DISTINCT ?c) AS ?connections)
               (COUNT(DISTINCT ?s) AS ?signals) WHERE {
          ?cfg a bn:Configuration ; rdfs:label ?configuration .
          OPTIONAL { ?cfg bn:includesModule ?m .
                     OPTIONAL { ?c a bn:Connection ; bn:belongsToModule ?m . OPTIONAL { ?c bn:carriesSignal ?s } } }
        } GROUP BY ?configuration ORDER BY DESC(?connections)"""),
    ("2  Varianten: Leitungslänge je Konfiguration (ohne Adern, die zu einem Kabel gehören)",
     """SELECT ?configuration (COUNT(?w) AS ?wires) (ROUND(SUM(?len) / 1000) AS ?length_m) WHERE {
          SELECT DISTINCT ?configuration ?w ?len WHERE {
            ?cfg a bn:Configuration ; rdfs:label ?configuration ; bn:includesModule ?m .
            ?w a bn:Wire ; bn:belongsToModule ?m ; bn:lengthMm ?len .
            FILTER NOT EXISTS { ?w bn:coreOf ?cable } } }
        GROUP BY ?configuration ORDER BY DESC(?length_m)"""),
    ("3  Varianten: Größte Module, die nur in MAX und nicht in MINI stecken",
     """SELECT ?module ?option_code (COUNT(DISTINCT ?c) AS ?connections) WHERE {
          ?max rdfs:label "Kombination_MAXI" ; bn:includesModule ?m .
          ?min rdfs:label "Kombination_MINI" .
          FILTER NOT EXISTS { ?min bn:includesModule ?m }
          ?m rdfs:label ?module ; bn:optionCode ?option_code .
          OPTIONAL { ?c a bn:Connection ; bn:belongsToModule ?m }
        } GROUP BY ?module ?option_code ORDER BY DESC(?connections) LIMIT 8"""),
    ("4  Traceability: Wohin läuft das Signal mit den meisten Verbindungen?",
     """SELECT ?connection ?wire ?mm2 ?from_connector ?to_connector WHERE {
          { SELECT ?s WHERE { ?c bn:carriesSignal ?s } GROUP BY ?s ORDER BY DESC(COUNT(?c)) LIMIT 1 }
          ?c bn:carriesSignal ?s ; rdfs:label ?connection ; bn:realisedBy ?w .
          ?w rdfs:label ?wire . OPTIONAL { ?w bn:crossSectionMm2 ?mm2 }
          OPTIONAL { ?c bn:fromContact ?a . ?x1 bn:hasContactPoint ?a ; rdfs:label ?from_connector }
          OPTIONAL { ?c bn:toContact ?b . ?x2 bn:hasContactPoint ?b ; rdfs:label ?to_connector }
        } ORDER BY ?connection"""),
    ("5  Änderungsauswirkung: Stecker mit den meisten Verbindungen ändert sich",
     """SELECT ?connector (COUNT(DISTINCT ?c) AS ?connections) (COUNT(DISTINCT ?s) AS ?signals)
               (COUNT(DISTINCT ?m) AS ?modules) (COUNT(DISTINCT ?cfg) AS ?configurations) WHERE {
          ?x bn:hasContactPoint ?cp ; rdfs:label ?connector .
          ?c bn:fromContact|bn:toContact ?cp .
          OPTIONAL { ?c bn:carriesSignal ?s }
          OPTIONAL { ?c bn:belongsToModule ?m . OPTIONAL { ?cfg bn:includesModule ?m } }
        } GROUP BY ?connector ORDER BY DESC(?connections) LIMIT 5"""),
    ("6a Konsistenz: Module ohne zugeordnete Leitungen, Verbindungen oder Stecker",
     """SELECT ?module ?option_code WHERE {
          ?m a bn:Module ; rdfs:label ?module ; bn:optionCode ?option_code .
          FILTER NOT EXISTS { ?x bn:belongsToModule ?m } }"""),
    ("6b Konsistenz: Verbindungen, die keinem Modul zugeordnet sind",
     """SELECT (COUNT(?c) AS ?connections_without_module) WHERE {
          ?c a bn:Connection . FILTER NOT EXISTS { ?c bn:belongsToModule ?m } }"""),
    ("6c Konsistenz: Verbindungen mit weniger als zwei Kontaktstellen",
     """SELECT ?connection ?signal WHERE {
          ?c a bn:Connection ; rdfs:label ?connection . OPTIONAL { ?c bn:carriesSignal/bn:signalName ?signal }
          FILTER NOT EXISTS { ?c bn:fromContact ?a ; bn:toContact ?b } } LIMIT 10"""),
    ("6d Prüfliste: gleiches Signal, unterschiedliche Querschnitte (oft gewollt, z. B. Verzweigung eines Versorgungsnetzes)",
     """SELECT ?signal (GROUP_CONCAT(DISTINCT STR(?mm2); separator=" / ") AS ?cross_sections_mm2)
               (COUNT(DISTINCT ?c) AS ?connections) WHERE {
          ?c bn:carriesSignal/bn:signalName ?signal ; bn:realisedBy/bn:crossSectionMm2 ?mm2 .
        } GROUP BY ?signal HAVING (COUNT(DISTINCT ?mm2) > 1) ORDER BY DESC(?connections) LIMIT 10"""),
]


def main():
    g = convert()
    (ROOT / "build").mkdir(exist_ok=True)
    g.serialize(ROOT / "build/oldbeetle.ttl", format="turtle")
    out = [f"# Ergebnisse: VW »Old Beetle« Hauptleitungssatz ({len(g)} Tripel)", "",
           "Quelle: Volkswagen VOBES-Beispieldaten, prostep ivip ECAD-Wiki, CC BY-SA 4.0.", ""]
    for title, query in QUESTIONS:
        md, _ = table(g.query(PREFIXES + query))
        out += [f"## {title}", "", *md, ""]
    text = "\n".join(out)
    print(text)
    (ROOT / "build/results_oldbeetle.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
