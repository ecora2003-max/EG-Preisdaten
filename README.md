# Supermarkt-Angebote · API- und Filialgeltungstests

Unabhängiges Forschungs- und Testrepository für die Angebotsdaten-Anbindung von **Ernährungsgedächtnis**. Keine Änderungen an der eigentlichen Android-App.

## Wichtigste Ergebnisse (31.10.2026)

- **PENNY:** 193 normalisierte Angebotsobjekte aus 12 verifizierten Kategorien, offizielle Berliner Verkaufsregion zugeordnet.
- **Kaufland:** 511 gültige Angebotsobjekte für die konkret ausgewählte Filiale DE5220, offizielle Artikel-Gültigkeitsliste und Filial-Cookie kombiniert.
- **ALDI Nord:** 276 Produktangebote der nächsten Woche samt Preisen und Datumsangaben, **ohne** bestätigte Filialzuordnung.
- **Lidl:** 191 mit dem kommenden Prospekt verknüpfte Produktobjekte, **ohne** gesicherte Lebensmittel-/Filialgültigkeit.
- **EDEKA und Netto Marken-Discount:** Code-Dokumentation und Filialkonzepte recherchiert, aber noch kein für unseren Runner verifizierter, freigegebener vollständiger Angebotsfeed.

**[Vollständiger geprüfter Implementierungsstand](reports/implementierungsstand-2026-10-31.md)**

## Testcode

- [Datentypen und normalisierte Parser](adapters/retailer_offers.py)
- [Offline-Adaptertests](tests/test_retailer_offers.py)
- [Live-Integrationstest](tools/live_adapter_smoke.py)
- [Testübersicht auf GitHub Actions](https://github.com/ecora2003-max/Try/actions)

Manuell lokal mit Python 3.11+ (nur Standardbibliothek):

```bash
python3 -m unittest discover -s tests -v
python3 tools/live_adapter_smoke.py
```

Der zweite Befehl stellt wenige lesende Live-Anfragen; lokale Netzwerkzugänglichkeit und veröffentlichte Crawlerregeln müssen dies erlauben. **HTTP 200 bedeutet keine Nutzungs- oder Weiterverwertungsfreigabe.**

Das Ergebnis `scope` unterscheidet `STORE_CONFIRMED`, `REGION_CONFIRMED`, `CHAIN_WIDE_REPORTED` und `UNKNOWN`. Damit wird kein Angebot fälschlich als garantiert in einer konkreten Filiale gültig ausgegeben.
