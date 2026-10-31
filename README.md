# Ernährungsgedächtnis – verifizierte Angebotsadapter

Dieses Repository enthält **Python-Referenzadapter**, Tests und Forschungsprotokolle für eine spätere Integration in die Android-App. Es ist **keine fertig veröffentlichbare Händlerdatenplattform**.

## Live-Ergebnisse vom 31. Oktober 2026

| Händler | Live-Testergebnis | Zuordnung | Status |
|---|---:|---|---|
| **PENNY** | 193 preislich auswertbare Angebotsdatensätze aus 12 Kategorien für KW 45 | Angebotsregion der konkreten Filiale | Schema + regionaler Adapter erfolgreich getestet |
| **Kaufland** | 511 Angebotsdatensätze für Filiale DE5220 und KW 45 | Offizielle `klNr`-Gültigkeitsliste der Filiale | Filialadapter erfolgreich getestet |
| **ALDI Nord** | 276 Aktionsdatensätze mit Preisen für die Folgewoche | Kettenweit; lokale Ausnahmen unbekannt | Kettenadapter erfolgreich getestet |
| **Lidl** | **Zusätzlich zum Angebotsfeed: echte Filial-Produktkatalog-API mit 18 Hauptkategorien, Produktsuche und aktuellen Preisfeldern bestätigt**; z. B. Berliner Milch 0,85 € | **Konkrete Filiale bestätigt** über `storeKey`; das Produktdetail antwortete für andere Filiale mit HTTP 204 | Preis-/Sortimentsadapter erfolgreich getestet, vollständige Sortimentserfassung noch offen |
| **EDEKA** | 256 Angebote Berlin, 40 Hamburg, 28 nationale Ersatzangebote | Offizielle Markt-ID und `national=false` | **Technisch getestet, automatisierte Nutzung bis zu Freigabe gesperrt** |
| **Netto Marken-Discount** | **Offizielle Filialprospekt-URLs für KW 45 bestätigt**; Berliner Prospekt als 72-seitige, 36,4-MB-PDF mit Text extrahierbar | **Prospekt konkreter Filiale bestätigt**, Artikelpreise noch nicht fehlerfrei zugeordnet | **Prospekt-Adapter getestet; vollautomatischer Produktadapter noch nicht produktionsfähig** |

**Kritisch:** Funktionierende HTTP-Endpunkte bzw. erfolgreiche Integrationstests sind **keine Lizenz**, Angebotsdaten automatisiert in einer eigenen App oder Datenbank zu verwenden. Ein API-Client muss die Nutzungsbedingungen und gegebenenfalls Lizenzvereinbarungen des jeweiligen Anbieters erfüllen.

**EDEKA:** [Aktuelle Website-Nutzungsbedingungen](https://www.edeka.de/services/nutzungsbedingungen/) verbieten ausdrücklich automatisierte Extraktion und Datenbankübernahme ohne vorherige Zustimmung. Alle drei EDEKA-Live-Forschungsskripte wurden daher mit einem `EDEKA_PERMISSION_CONFIRMED=1`-Gate gesichert. Ohne externe Freigabe wird **nicht** erneut automatisiert abgefragt. Dieser Gate ist nur ein technischer Schutz, nicht der Nachweis einer Erlaubnis.

**Netto:** Einzelne Filialseiten und `/filialangebote` wurden geblockt; dagegen funktioniert `GET https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm?stores_id=7679` mit regulärem HTTP 200 und liefert **die tatsächliche Filialadresse und den zugeordneten offiziellen Wochenprospekt**. Über `wochenprospekt.netto-online.de` ist die Filial-PDF regulär abrufbar; eine 72-seitige Berliner KW45-Ausgabe enthielt auf den ersten drei Seiten durchsuchbaren Text mit Produktnamen und Preisangaben. Ein belastbares Zuordnungsverfahren *Produkt ↔ Preis ↔ Seite* muss erst validiert werden; bis dahin werden keine aus der PDF geratenen Preise ausgegeben. Eine Genehmigung für systematische Datenübernahme ist unabhängig von technischem Zugriff zu prüfen.

## Projektdateien

- [Python-Parser, Angebotsmodell und Netto-Prospektzuordnung](adapters/retailer_offers.py) mit `STORE_CONFIRMED`, `REGION_CONFIRMED`, `CHAIN_WIDE_REPORTED`, `UNKNOWN`.
- [Offline-Vertragstests](tests/test_retailer_offers.py)
- [Live-Kompatibilitätstest für PENNY, Kaufland, ALDI Nord und Lidl](tools/live_adapter_smoke.py)
- [Erweiterte technische Bewertung](reports/implementierungsstand-2026-10-31.md)
- [Testübersicht mit JSON-Artefakten](https://github.com/ecora2003-max/Try/actions)

## Bestätigte automatisierte Tests

- [PENNY, Kaufland, ALDI Nord und **direktes Lidl** – Live ALL PASS](https://github.com/ecora2003-max/Try/actions/runs/41183799427)
- [EDEKA Berlin, Hamburg, national – historischer erfolgreich abgeschlossener Forschungslauf](https://github.com/ecora2003-max/Try/actions/runs/41183681778). **Nicht erneut ohne Freigabe ausführen.**
- [Lidl Berlin vs. Hannover – sechs abweichende Filialaktionen](https://github.com/ecora2003-max/Try/actions/runs/41183580801)
- **[Lidl aktuell angezeigte Produktpreise und 18 Kategorien – Live PASS](https://github.com/ecora2003-max/Try/actions/runs/41187206333)**
- **[Lidl derselbe Artikel in zwei konkreten Filialen – PASS](https://github.com/ecora2003-max/Try/actions/runs/41187388717)**
- [Forschungsbericht: tatsächliche Filialpreiskataloge](reports/tatsaechliche-filialpreiskataloge-2026-10-31.md)
- [Netto: offizielle Filialprospekt-Verknüpfung für zwei Filialen – PASS](https://github.com/ecora2003-max/Try/actions/runs/41184627158)
- [Netto: Filial-PDF 72 Seiten, textlesbar – PASS](https://github.com/ecora2003-max/Try/actions/runs/41184427978)
- [Netto: Filialproduktseite weiterhin geblockt](https://github.com/ecora2003-max/Try/actions/runs/41184674088)

Lokal nur mit Python-Standardbibliothek:

```bash
python3 -m unittest discover -s tests -v
```

Die eingebundenen Feldparsers sind Referenzcode. Die Original-Android-App im separaten Repository wurde nicht geändert. Alle Beispiele gelten für den jeweiligen Testzeitpunkt; Wochenend- und Vorschauangebote sind nicht identisch.

## Wichtige Händleridentität

**Netto Marken-Discount** (`netto-online.de`, EDEKA-Gruppe) ist **nicht** der gleichnamige Netto mit Scottie-Hund (`netto.de`, Salling Group). App-/Preisscanner-Daten und APIs dieser Ketten dürfen nicht vermischt werden. [Neue Recherche und EDEKA-Shop-Zugriffstest](reports/preiskatalog-recherche-2026-10-31-zusatz.md).

## Neue Scan&Go-Preisstruktur (31.10.2026)

[Untersuchung: PENNY/REWE teilen das shopreme-SDK, dessen DataHub marktbezogene Produkt- und Preisimporte umfasst; EDEKA bietet ein offizielles B2C-Gateway nur auf Zugangsanfrage.](reports/scan-go-gemeinsame-preis-infrastruktur-2026-10-31.md) **Wichtig:** Dies beweist die Existenz der Händlerpreis-Infrastruktur, nicht eine öffentlich nutzbare Vollpreis-API. [Öffentlicher Dokumentationstest](https://github.com/ecora2003-max/Try/actions/runs/41190033352).

## Eigene Android-APK-Analyse (31.10.2026)

[Fünf echte APK/XAPK-Dateien statisch untersucht und Kaufland/Netto gezielt mit JADX dekompiliert](reports/eigene-apk-binaeranalyse-2026-10-31.md). **Neue Kandidaten:** Kaufland-K-SCAN `GET v1/products/{countryId}/{storeId}`; Netto Marken-Discount `GET rest/api/v2/productSearch` und `GET api/v1/mpos/{storeId}/itemInfo`. Diese Methodensignaturen sind direkt aus den APKs nachgewiesen, aber vollständige Preisabdeckung, externe Erreichbarkeit und Nutzungsrechte sind noch nicht bestätigt. Keine Binärdateien, Tokens oder dekompilierten App-Quelltexte im Repository. [Binäranalyse](https://github.com/ecora2003-max/Try/actions/runs/41191014066) · [JADX-Live-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41191207477).

## Erweiterte APK-Recherche (31.10.2026)

**[Abschlussbericht: sieben vollständige DEX-Retrofit-Scans + Open-Source-Abgleich](reports/vollstaendige-retrofit-endpunktsuche-2026-10-31.md)** · [GitHub-Actions-Lauf: 7/7 erfolgreich](https://github.com/ecora2003-max/Try/actions/runs/41193283187). Die Auswertung extrahierte bisher übersehene ALDI-SÜD-Produktrouten, konkretisierte Nettos filialbezogene `productSearch(searchString, storeId)`, bestätigte Kauflands K-SCAN-Produktdownload und identifizierte über [`chukfinley/bismark`](https://github.com/chukfinley/bismark) eine REWE-Website-Schnittstelle für stationäre Filialpreise. **Alle Befunde sind statische bzw. fremddokumentierte Hinweise; keine neue Live-Preisvalidierung oder Nutzungsfreigabe.**

## Neu: eigene Live-Preisnachweise für REWE und ALDI Süd (31.10.2026)

[**Bericht mit drei realen, stark begrenzten GitHub-Actions-Tests**](reports/rewe-aldi-sued-echte-preisantworten-2026-10-31.md):

- **REWE stationär**: `www.rewe.de/api/stationary-product-search/products?query=Haferflocken&wwIdent=840174` lieferte HTTP 200 und 12 bepreiste Artikel. **Zwei-Markt-Test:** 11 gleiche Produkt-IDs; **5 davon mit unterschiedlichen Preisen** zwischen `wwIdent=840174` und `831002`. Damit sind reale Filialpreisunterschiede am Endpoint empirisch bestätigt. [Lauf](https://github.com/ecora2003-max/Try/actions/runs/41195181867).
- **ALDI Süd**: `api.aldi-sued.de/v3/product-search`, `servicePoint=B384`, `serviceType=walk-in` lieferte HTTP 200, Preisfelder in Cent. **Ungefilterte Einzelseite** mit `limit=12` meldete `totalCount=3538`, alle **12/12** Artikel auf Seite 1 mit numerischem Preis. Die übrigen 3.526 Artikel **wurden nicht abgerufen oder geprüft**. [Lauf](https://github.com/ecora2003-max/Try/actions/runs/41195314409).
- [Rein offline nutzbarer Preisnormalisierer](adapters/stationary_price_catalogues.py) mit [erfolgreichen Tests](https://github.com/ecora2003-max/Try/actions/runs/41195124182).

**Datenrechte und Abdeckung offen:** Kein Nachweis einer Lizenz für laufende systematische Datenbankübernahme, keine Vollsortimentabdeckung oder Kassenbon-Validierung, kein produktiver Adapter. Alle neuen Tests sind einmalige, robots-respektierende, anonyme GET-Abfragen ohne Schutzumgehung. Ausschließlich `Try` wurde geändert.
