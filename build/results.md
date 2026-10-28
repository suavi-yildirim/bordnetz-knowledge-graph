# Ergebnisse (520 Tripel)

## 1  Traceability: Über welche Leitungen und Kontakte läuft die Funktion »Fensterheber«?

| signal | wire | mm2 | from | to |
|---|---|---|---|---|
| FH_MOT_MINUS | W05 | 0.35 | X2.5 | X3.2 |
| FH_MOT_PLUS | W04 | 1.5 | X2.4 | X3.1 |
| KL30_TSG | W01 | 2.5 | X1.1 | X2.1 |
| LIN_TUER | W03 | 0.35 | X1.3 | X2.3 |

## 2  Änderungsauswirkung: Stecker X4 (Außenspiegel) ändert sich. Was ist betroffen?

| wire | signal | function | module |
|---|---|---|---|
| W06 | SP_VERST | Spiegelverstellung | Basis |
| W07 | KL31 | – | Basis |
| W12 | SP_POS | Spiegel-Memory | Komfort (Spiegel-Memory, Spiegelheizung) |

## 3a Varianten: Leitungen und Leitungslänge je Fahrzeugkonfiguration

| configuration | wires | length_mm |
|---|---|---|
| Basis | 9 | 7630 |
| Komfort | 10 | 8170 |
| Ambiente | 11 | 9430 |
| Vollausstattung | 12 | 9970 |

## 3b Varianten: Welche Funktion ist in welcher Konfiguration nicht vollständig verlegt?

| configuration | function | missing_signal |
|---|---|---|
| Ambiente | Ambientebeleuchtung | AMB_LED_PWM |
| Komfort | Spiegelheizung | SP_HEIZ |
| Vollausstattung | Ambientebeleuchtung | AMB_LED_PWM |
| Vollausstattung | Spiegelheizung | SP_HEIZ |

## 4a Konsistenz: Leitung dünner als vom Signal gefordert

| wire | signal | mm2 | required_mm2 |
|---|---|---|---|
| W05 | FH_MOT_MINUS | 0.35 | 1.5 |

## 4b Konsistenz: Signal im E/E-Modell, aber im Leitungssatz nicht verlegt

| signal | label | function |
|---|---|---|
| SP_HEIZ | Spiegelheizung | Spiegelheizung |
| AMB_LED_PWM | Ambiente-LED PWM | Ambientebeleuchtung |

## 4c Konsistenz: Signalname im Leitungssatz, den das E/E-Modell nicht kennt

| connection | signal |
|---|---|
| C10 | AMB_LED_PWN |

Vorschlag: `AMB_LED_PWN` → `AMB_LED_PWM`?

