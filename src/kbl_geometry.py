"""KBL geometry -> 3D polylines for the viewer (the harness as it is routed in the car).

Segments carry their centre line as B-spline pieces (Center_curve: degree 6, 7 control
points, no knot vector).  Evaluated as *uniform, unclamped* B-splines on their one valid
knot span, the pieces join exactly and end on the segment's start and end nodes
(178 of 183 segments: <= 1 mm deviation, length = KBL Virtual_length within 0.2 %).
The other 5 miss their nodes by up to 0.5 m, an inconsistency in the source data:
they are drawn as straight lines and flagged ("suspect").

Also read: nodes with the connectors and special terminals placed on them, fixings (clips),
component boxes (relays, fuse holders) and the routing of every connection through segments.
"""
import math
import xml.etree.ElementTree as ET

from real_kbl import SRC, number


def point(byid, pid):
    return [float(c.text) for c in byid[pid].findall("Coordinates")]


def de_boor(t, ctrl, p):
    """Point at parameter t (p <= t <= p+1) of a uniform B-spline with knots 0, 1, 2, ..."""
    d = [list(c) for c in ctrl[: p + 1]]
    for r in range(1, p + 1):
        for j in range(p, r - 1, -1):
            a = (t - j) / (j + 1 + p - r - j)
            d[j] = [(1 - a) * d[j - 1][i] + a * d[j][i] for i in range(3)]
    return d[p]


def centre_line(byid, segment, samples=8):
    pts = []
    for curve in segment.findall("Center_curve"):
        ctrl = [point(byid, pid) for pid in curve.findtext("Control_points").split()]
        p = int(curve.findtext("Degree"))
        piece = [de_boor(p + i / samples, ctrl, p) for i in range(samples + 1)]
        pts += piece if not pts else piece[1:]  # consecutive pieces share their end point
    return pts


TOLERANCE_MM = 5  # curve end further than this from its node -> centre line does not fit


def geometry(path=SRC):
    root = ET.parse(path).getroot()
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}
    h = root.find("Harness")
    segments = root.findall("Segment")

    lines, suspect, ratios = {}, {}, []
    for s in segments:
        pts = centre_line(byid, s)
        a = point(byid, byid[s.findtext("Start_node")].findtext("Cartesian_point"))
        b = point(byid, byid[s.findtext("End_node")].findtext("Cartesian_point"))
        miss = max(math.dist(pts[0], a), math.dist(pts[-1], b))
        if miss > TOLERANCE_MM:
            suspect[s.get("id")] = round(miss)
            pts = [a, [(u + v) / 2 for u, v in zip(a, b)], b]  # straight between the nodes
        else:
            ratios.append(sum(math.dist(u, v) for u, v in zip(pts, pts[1:])) / number(s, "Virtual_length"))
        lines[s.get("id")] = pts
    every = [q for pts in lines.values() for q in pts]
    centre = [(min(q[i] for q in every) + max(q[i] for q in every)) / 2 for i in range(3)]

    def view(q):
        """Vehicle axes (x back, y left, z up) -> viewer axes (y up), centred, in mm."""
        x, y, z = (q[i] - centre[i] for i in range(3))
        return [round(x, 1), round(z, 1), round(-y, 1)]

    routes = {}
    for r in root.findall("Routing"):
        for seg in (r.findtext("Segments") or "").split():  # empty: both ends on the same node
            routes.setdefault(seg, []).append(r.findtext("Routed_wire"))

    seg_out = []
    for s in segments:
        area = number(s.find("Cross_section_area_information"), "Area") or 3.0
        seg_out.append({"id": s.get("id"), "pts": [view(q) for q in lines[s.get("id")]],
                        "r": round(math.sqrt(area / math.pi), 2), "length": round(number(s, "Virtual_length")),
                        "connections": routes.get(s.get("id"), []), "suspect": suspect.get(s.get("id"))})

    placed = []  # connectors and special terminals sit on nodes
    for n in root.findall("Node"):
        q = view(point(byid, n.findtext("Cartesian_point")))
        for ref in (n.findtext("Referenced_components") or "").split():
            e = byid.get(ref)
            if e is not None and e.tag in ("Connector_occurrence", "Special_terminal_occurrence"):
                placed.append({"id": ref, "label": e.findtext("Id"), "p": q,
                               "kind": "connector" if e.tag == "Connector_occurrence" else "terminal"})

    def at_placement(e):
        return view(point(byid, e.find("Placement").findtext("Cartesian_point")))

    fixings = [{"label": f.findtext("Id"), "p": at_placement(f)}
               for f in h.findall("Fixing_occurrence") if f.find("Placement") is not None]
    boxes = [{"label": b.findtext("Id"), "desc": b.findtext("Description") or "", "p": at_placement(b)}
             for b in h.findall("Component_box_occurrence") if b.find("Placement") is not None]

    ratio = sorted(ratios)[len(ratios) // 2]
    total = sum(number(s, "Virtual_length") for s in segments) / 1000
    return {"segments": seg_out, "placed": placed, "fixings": fixings, "boxes": boxes,
            "stats": {"de": f"{len(segments)} Segmente · {total:.0f} m Leitungsstrang · {len(fixings)} Clips · "
                            f"Mittellinien: {len(segments) - len(suspect)} von {len(segments)} passen exakt "
                            f"(Länge {ratio * 100:.1f} % der KBL-Länge), {len(suspect)} weichen ab (rot)",
                      "en": f"{len(segments)} segments · {total:.0f} m of bundles · {len(fixings)} clips · "
                            f"centre lines: {len(segments) - len(suspect)} of {len(segments)} fit exactly "
                            f"(length {ratio * 100:.1f} % of the KBL length), {len(suspect)} deviate (red)"},
            "suspect": [{"id": k, "miss_mm": v} for k, v in suspect.items()]}


if __name__ == "__main__":
    g = geometry()
    print(g["stats"], "|", len(g["placed"]), "placed,", len(g["boxes"]), "boxes")
