# Ernährungsgedächtnis – verifizierte Angebotsadapter

Dieses Repository enthält **Python-Referenzadapter**, Tests und Forschungsprotokolle für eine spätere Integration in die Android-App. Es ist **keine fertig veröffentlichbare Händlerdatenplattform**.

## Live-Ergebnisse vom 31. Oktober 2026

| Händler | Live-Testergebnis | Zuordnung | Status |
|---|---:|---|---|
| **PENNY** | 193 preislich auswertbare Angebotsdatensätze aus 12 Kategorien für KW 45 | Angebotsregion der konkreten Filiale | Schema + regionaler Adapter erfolgreich getestet |
| **Kaufland** | 511 Angebotsdatensätze für Filiale DE5220 und KW 45 | Offizielle `klNr`-Gültigkeitsliste der Filiale | Filialadapter erfolgreich getestet |
| **ALDI Nord** | 276 Aktionsdatensätze mit Preisen für die Folgewoche | Kettenweit; lokale Ausnahmen unbekannt | Kettenadapter erfolgreich getestet |
| **Lidl** | 65 Einzel-Aktionspreise aus 78 Angeboten der Filiale DE7434 | **Konkrete Filiale bestätigt** über `storeKey` | Filialadapter erfolgreich getestet |
| **EDEKA** | 256 Angebote Berlin, 40 Hamburg, 28 nationale Ersatzangebote | Offizielle Markt-ID und `national=false` | **Technisch getestet, automatisierte Nutzung bis zu Freigabe gesperrt** |
| **Netto Marken-Discount** | Allgemeine Prospektseite erreichbar; Filialseite 403 / gewöhnlicher Chrome „Access Denied“ | Filiale nicht maschinenlesbar bestätigt | **Nicht produktionsfähig; keine Schutzumgehung** |

**Kritisch:** Funktionierende HTTP-Endpunkte bzw. erfolgreiche Integrationstests sind **keine Lizenz**, Angebotsdaten automatisiert in einer eigenen App oder Datenbank zu verwenden. Ein API-Client muss die Nutzungsbedingungen und gegebenenfalls Lizenzvereinbarungen des jeweiligen Anbieters erfüllen.

**EDEKA:** [Aktuelle Website-Nutzungsbedingungen](https://www.edeka.de/services/nutzungsbedingungen/) verbieten ausdrücklich automatisierte Extraktion und Datenbankübernahme ohne vorherige Zustimmung. Alle drei EDEKA-Live-Forschungsskripte wurden daher mit einem `EDEKA_PERMISSION_CONFIRMED=1`-Gate gesichert. Ohne externe Freigabe wird **nicht** erneut automatisiert abgefragt. Dieser Gate ist nur ein technischer Schutz, nicht der Nachweis einer Erlaubnis.

**Netto:** Ein Filialseitenabruf aus GitHub Actions wurde blockiert; eine normale Browseransicht bestätigte die Sperre. Keine Benutzeragent-Vortäuschung, Sessionübernahme, Browser-Stealth oder Umgehung implementieren. Für automatisierten Betrieb ist eine freigegebene Datenquelle nötig; alternativ nur vom Nutzer bereitgestellte Informationen mit kenntlich gemachter Unsicherheit importieren.

## Projektdateien

- [Python-Parser und Angebotsmodell](adapters/retailer_offers.py) mit `STORE_CONFIRMED`, `REGION_CONFIRMED`, `CHAIN_WIDE_REPORTED`, `UNKNOWN`.
- [Offline-Vertragstests](tests/test_retailer_offers.py)
- [Live-Kompatibilitätstest für PENNY, Kaufland, ALDI Nord und Lidl](tools/live_adapter_smoke.py)
- [Erweiterte technische Bewertung](reports/implementierungsstand-2026-10-31.md)
- [Testübersicht mit JSON-Artefakten](https://github.com/ecora2003-max/Try/actions)

## Bestätigte automatisierte Tests

- [PENNY, Kaufland, ALDI Nord und **direktes Lidl** – Live ALL PASS](https://github.com/ecora2003-max/Try/actions/runs/41183799427)
- [EDEKA Berlin, Hamburg, national – historischer erfolgreich abgeschlossener Forschungslauf](https://github.com/ecora2003-max/Try/actions/runs/41183681778). **Nicht erneut ohne Freigabe ausführen.**
- [Lidl Berlin vs. Hannover – sechs abweichende Filialaktionen](https://github.com/ecora2003-max/Try/actions/runs/41183580801)
- [Netto ohne Browser-Bypass – offizielle Filialseite zeigt Access Denied](https://github.com/ecora2003-max/Try/actions/runs/41183768242)

Lokal nur mit Python-Standardbibliothek:

```bash
python3 -m unittest discover -s tests -v
```

Die eingebundenen Feldparsers sind Referenzcode. Die Original-Android-App im separaten Repository wurde nicht geändert. Alle Beispiele gelten für den jeweiligen Testzeitpunkt; Wochenend- und Vorschauangebote sind nicht identisch.
