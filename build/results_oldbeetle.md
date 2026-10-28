# Ergebnisse: VW »Old Beetle« Hauptleitungssatz (5957 Tripel)

Quelle: Volkswagen VOBES-Beispieldaten, prostep ivip ECAD-Wiki, CC BY-SA 4.0.

## 0  Überblick: Instanzen je Klasse

| class | count |
|---|---|
| Kontaktstelle | 372 |
| Leitung | 286 |
| Verbindung | 254 |
| Stecker | 141 |
| Signal | 108 |
| Modul | 34 |
| Fahrzeugkonfiguration | 3 |
| Leitungssatz | 1 |

## 1  Varianten: Umfang je Leitungssatz-Konfiguration

| configuration | modules | connections | signals |
|---|---|---|---|
| Kombination_MAXI | 34 | 254 | 108 |
| Kombination_MINI | 7 | 165 | 74 |
| Freie Kombination | 0 | 0 | 0 |

## 2  Varianten: Leitungslänge je Konfiguration (ohne Adern, die zu einem Kabel gehören)

| configuration | wires | length_m |
|---|---|---|
| Kombination_MAXI | 191 | 278 |
| Kombination_MINI | 153 | 218 |

## 3  Varianten: Größte Module, die nur in MAX und nicht in MINI stecken

| module | option_code | connections |
|---|---|---|
| aaa108a1aa61D | L0L+K8S+1ZQ+8Q3 | 10 |
| aaa108a13201B | L0L+4GK | 10 |
| aaa108a1aa61B | L0L+K8D+1LC/1LJ/1LK/1LM/1LN/1LU/1LV+8Q0 | 8 |
| aaa108a12241C | L0L+QQ2 | 7 |
| aaa108a1aa61E | L0L+K8S+1LC/1LJ/1LK/1LM/1LN/1LU/1LV+8Q5 | 6 |
| aaa108a1aa61F | L0L+K8S+1ZQ+8Q0/8Q1 | 6 |
| aaa108a1aa61G | L0L+K8D+1LC/1LJ/1LK/1LM/1LN/1LU/1LV+8Q1 | 6 |
| aaa108a1aa61I | L0L+K8D+1LC/1LJ/1LK/1LM/1LN/1LU/1LV+8Q5 | 6 |

## 4  Traceability: Wohin läuft das Signal mit den meisten Verbindungen?

| connection | wire | mm2 | from_connector | to_connector |
|---|---|---|---|---|
| X.30rfg.SZS1035.1C2981111 | 30 | 4.0 | B298 | B272 |
| X.30rfg.SZS1035.1C2981112 | 31 | 6.0 | B298 | TMM.1A1 |
| X.30rfg.SZS1035.1XB.B.1.KPQ1111 | 63 | 6.0 | XA.A.1.REF | B298 |
| X.30rfg.SZS1035.1XB.F.11111 | 33 | 4.0 | XA.D.1 | B298 |
| X.30rfg.SZS1035.1XB.O533.11211 | 24 | 1.0 | XA.J533.1 | B298 |
| X.30rfg.SZS1035.1XB.P1.111111 | 27 | 2.5 | XA.E1.1 | B272 |
| X.30rfg.SZS1035.1XB.S41.11211 | 219007 | 4.0 | – | B298 |
| X.30rfg.SZS1035.1XB.SB.118B11 | 28 | 4.0 | – | B272 |
| X.30rfg.SZS1035.1XB.SB.119B11 | 29 | 4.0 | – | B298 |
| X.30rfg.SZS1035.1XC.O533.11111 | 26 | 4.0 | XB.J533.1 | B298 |

## 5  Änderungsauswirkung: Stecker mit den meisten Verbindungen ändert sich

| connector | connections | signals | modules | configurations |
|---|---|---|---|---|
| TCPL.1D1 | 25 | 11 | 6 | 1 |
| TCPL.1C1 | 22 | 10 | 3 | 2 |
| TCPL.1B1 | 17 | 10 | 3 | 1 |
| XA.J533.1 | 11 | 10 | 3 | 2 |
| XA.E1.1 | 10 | 6 | 5 | 2 |

## 6a Konsistenz: Module ohne zugeordnete Leitungen, Verbindungen oder Stecker

| module | option_code |
|---|---|
| aaa108a1a4a1C | L0L+0Y1/0Y3//L0L+VC1/VC2 |

## 6b Konsistenz: Verbindungen, die keinem Modul zugeordnet sind

| connections_without_module |
|---|
| 0 |

## 6c Konsistenz: Verbindungen mit weniger als zwei Kontaktstellen

| connection | signal |
|---|---|
| (keine Treffer) |

## 6d Prüfliste: gleiches Signal, unterschiedliche Querschnitte (oft gewollt, z. B. Verzweigung eines Versorgungsnetzes)

| signal | cross_sections_mm2 | connections |
|---|---|---|
| X.30rfg.SZS1035. | 1.0 / 4.0 / 2.5 / 6.0 | 10 |
| V.15B.SZS1090.Q12111B12C | 0.5 / 2.5 / 1.5 | 8 |
| M.31.SZS1033.MI45111H1 | 0.5 / 4.0 | 8 |
| M.31.SZS1033.MI45111F1 | 1.0 / 0.5 | 8 |
| V.54.SZS1090. | 1.5 / 0.5 / 1.0 | 7 |
| S.KFaoj.SZS1047.2 | 0.75 / 0.35 / 0.5 | 6 |
| V.15B.SZS1090.Q11111B11C | 2.5 / 1.5 / 1.0 / 0.5 | 6 |
| V.58.SZS1034.Q2111B2C | 0.5 / 2.5 / 1.0 | 6 |
| V.T.SZS1035. | 1.0 / 0.5 / 1.5 | 6 |
| V.K.SZS1035. | 1.0 / 0.5 / 1.5 | 6 |

