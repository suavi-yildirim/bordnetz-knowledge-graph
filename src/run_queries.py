"""Competency questions on the harness graph (SPARQL).

Each question is one that is hard to answer from KBL or the E/E model alone,
because the answer needs both views.  Results go to the console and build/results.md.

Usage: python src/run_queries.py
"""
import difflib
from pathlib import Path

from rdflib import URIRef

from build_graph import BN, DATA, ROOT, build

PREFIXES = """
PREFIX bn:   <https://example.org/bordnetz#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

QUESTIONS = [
    # ---------------------------------------------------------------- 1
    ("1  Traceability: Über welche Leitungen und Kontakte läuft die Funktion »Fensterheber«?",
     """SELECT ?signal ?wire ?mm2 ?from ?to WHERE {
          ?fn bn:usesSignal ?s . ?s bn:signalName ?signal .
          OPTIONAL { ?c bn:carriesSignal ?s ; bn:realisedBy ?w ;
                        bn:fromContact ?a ; bn:toContact ?b .
                     ?w rdfs:label ?wire ; bn:crossSectionMm2 ?mm2 .
                     ?a rdfs:label ?from . ?b rdfs:label ?to . }
        } ORDER BY ?signal""",
     {"fn": DATA["function/F_FH"]}),
    # ---------------------------------------------------------------- 2
    ("2  Änderungsauswirkung: Stecker X4 (Außenspiegel) ändert sich. Was ist betroffen?",
     """SELECT DISTINCT ?wire ?signal ?function ?module WHERE {
          ?x bn:hasContactPoint ?cp .
          ?c bn:fromContact|bn:toContact ?cp ; bn:realisedBy ?w ; bn:carriesSignal ?s .
          ?w rdfs:label ?wire ; bn:belongsToModule/rdfs:label ?module .
          ?s bn:signalName ?signal .
          OPTIONAL { ?f bn:usesSignal ?s ; rdfs:label ?function . }
        } ORDER BY ?wire""",
     {"x": DATA["connector/X4"]}),
    # ---------------------------------------------------------------- 3a
    ("3a Varianten: Leitungen und Leitungslänge je Fahrzeugkonfiguration",
     """SELECT ?configuration (COUNT(DISTINCT ?w) AS ?wires) (SUM(?len) AS ?length_mm) WHERE {
          ?cfg a bn:Configuration ; rdfs:label ?configuration ; bn:includesModule ?m .
          ?w bn:belongsToModule ?m ; bn:lengthMm ?len .
        } GROUP BY ?configuration ORDER BY ?wires""",
     {}),
    # ---------------------------------------------------------------- 3b
    ("3b Varianten: Welche Funktion ist in welcher Konfiguration nicht vollständig verlegt?",
     """SELECT ?configuration ?function ?missing_signal WHERE {
          ?cfg a bn:Configuration ; rdfs:label ?configuration ; bn:includesModule ?m .
          ?f bn:requiresModule ?m ; rdfs:label ?function ; bn:usesSignal ?s .
          ?s bn:signalName ?missing_signal .
          FILTER NOT EXISTS { ?c bn:carriesSignal ?s ; bn:realisedBy/bn:belongsToModule ?m2 .
                              ?cfg bn:includesModule ?m2 . }
        } ORDER BY ?configuration ?function""",
     {}),
    # ---------------------------------------------------------------- 4a
    ("4a Konsistenz: Leitung dünner als vom Signal gefordert",
     """SELECT ?wire ?signal ?mm2 ?required_mm2 WHERE {
          ?c bn:carriesSignal ?s ; bn:realisedBy ?w .
          ?w rdfs:label ?wire ; bn:crossSectionMm2 ?mm2 .
          ?s bn:signalName ?signal ; bn:requiredCrossSectionMm2 ?required_mm2 .
          FILTER (?mm2 < ?required_mm2)
        }""",
     {}),
    # ---------------------------------------------------------------- 4b
    ("4b Konsistenz: Signal im E/E-Modell, aber im Leitungssatz nicht verlegt",
     """SELECT ?signal ?label ?function WHERE {
          ?s bn:sourceSystem "E/E" ; bn:signalName ?signal ; rdfs:label ?label .
          ?f bn:usesSignal ?s ; rdfs:label ?function .
          FILTER NOT EXISTS { ?c bn:carriesSignal ?s }
        }""",
     {}),
    # ---------------------------------------------------------------- 4c
    ("4c Konsistenz: Signalname im Leitungssatz, den das E/E-Modell nicht kennt",
     """SELECT ?connection ?signal WHERE {
          ?c bn:carriesSignal ?s ; rdfs:label ?connection .
          ?s bn:signalName ?signal .
          FILTER NOT EXISTS { ?s bn:sourceSystem "E/E" }
        }""",
     {}),
]


def table(result):
    cols = [str(v) for v in result.vars]
    rows = [[("–" if r[c] is None else str(r[c])) for c in cols] for r in result]
    md = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(r) + " |" for r in rows] or ["| (keine Treffer) |"]
    return md, rows


def main():
    g = build()
    known = sorted(str(o) for s, o in g.subject_objects(BN.signalName)
                   if (s, BN.sourceSystem, None) in g)
    out = [f"# Ergebnisse ({len(g)} Tripel)", ""]
    for title, query, bindings in QUESTIONS:
        res = g.query(PREFIXES + query, initBindings={k: URIRef(v) for k, v in bindings.items()})
        md, rows = table(res)
        out += [f"## {title}", "", *md, ""]
        if title.startswith("4c"):  # suggest the closest known signal name
            for _, name in rows:
                guess = difflib.get_close_matches(name, known, n=1)
                if guess:
                    out += [f"Vorschlag: `{name}` → `{guess[0]}`?", ""]
    text = "\n".join(out)
    print(text)
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/results.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
