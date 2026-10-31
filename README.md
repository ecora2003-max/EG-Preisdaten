# Ernährungsgedächtnis – verifizierte Angebotsadapter

> **Verbindliche Einweisung für den zuständigen Entwicklungs-Chat:** [AGENTS.md](AGENTS.md) · [Entwicklungsauftrag](docs/DEVELOPMENT_MANDATE.md) · [Abnahmetests und Fertigstellung](docs/ACCEPTANCE.md) · [Integrationsschnittstellen](docs/INTEGRATION.md) · [Status](docs/STATUS.md). Gemeinsame Verträge: [EG-Architecture](https://github.com/ecora2003-max/EG-Architecture). **Nur dieses Modulrepo bearbeiten; Architektur und private Haupt-App ausschließlich lesen. Tests nach jeder fachlichen Änderung verpflichtend.**


## Aktueller Referenzkern (31.10.2026)

[Pure Python Preis-Snapshot-API](price_module/service.py) · [synthetische CLI-Eingabe](examples/synthetic-price-query.json) · [Codex-Integrationsanleitung](docs/INTEGRATION.md) · [Abnahmestand](docs/STATUS.md).

```sh
python3 -m pip install -r requirements-dev.lock
python3 -m unittest discover -s tests -v
python3 -m price_module < examples/synthetic-price-query.json
```

**CI [74/74 Offline-Tests erfolgreich](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220671906), zuletzt geprüfter Code `8e935b4844d5`.** Der Kern ist unabhängig ausführbar und schemavalidiert. Externe Händlerdaten werden ohne dokumentierte Rechte **nicht** zur produktiven App-Anzeige freigegeben; wissenschaftliche Live-Einzelnachweise bleiben von dauerhaft zulässiger Nutzung getrennt. Kein Gesamt-Vollsortiment und keine Android-Integration behauptet.

Dieses Repository enthält **Python-Referenzadapter**, Tests und Forschungsprotokolle für eine spätere Integration in die Android-App. Es ist **keine fertig veröffentlichbare Händlerdatenplattform**.

## Live-Ergebnisse vom 31. Oktober 2026

| Händler | Live-Testergebnis | Zuordnung | Status |
|---|---:|---|---|
| **PENNY** | 193 preislich auswertbare Angebotsdatensätze aus 12 Kategorien für KW 45 | Angebotsregion der konkreten Filiale | Schema + regionaler Adapter erfolgreich getestet |
| **Kaufland** | 511 Angebotsdatensätze für Filiale DE5220 und KW 45 | Offizielle `klNr`-Gültigkeitsliste der Filiale | Filialadapter erfolgreich getestet |
| **ALDI Nord** | 276 Aktionsdatensätze mit Preisen für die Folgewoche | Kettenweit; lokale Ausnahmen unbekannt | Kettenadapter erfolgreich getestet |
| **Lidl** | **Zusätzlich zum Angebotsfeed: echte Filial-Produktkatalog-API mit 18 Hauptkategorien, Produktsuche und aktuellen Preisfeldern bestätigt**; z. B. Berliner Milch 0,85 € | **Konkrete Filiale bestätigt** über `storeKey`; das Produktdetail antwortete für andere Filiale mit HTTP 204 | Preis-/Sortimentsadapter erfolgreich getestet, vollständige Sortimentserfassung noch offen |
| **EDEKA** | 256 Angebote Berlin, 40 Hamburg, 28 nationale Ersatzangebote | Offizielle Markt-ID und `national=false` | **Technisch getestet, automatisierte Nutzung zugelassen** |
| **Netto Marken-Discount** | **Offizielle Filialprospekt-URLs für KW 45 bestätigt**; Berliner Prospekt als 72-seitige, 36,4-MB-PDF mit Text extrahierbar | **Prospekt konkreter Filiale bestätigt**, Artikelpreise noch nicht fehlerfrei zugeordnet | **Prospekt-Adapter getestet; vollautomatischer Produktadapter noch nicht produktionsfähig** |


**Netto:** Einzelne Filialseiten und `/filialangebote` wurden geblockt; dagegen funktioniert `GET https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm?stores_id=7679` mit regulärem HTTP 200 und liefert **die tatsächliche Filialadresse und den zugeordneten offiziellen Wochenprospekt**. Über `wochenprospekt.netto-online.de` ist die Filial-PDF regulär abrufbar; eine 72-seitige Berliner KW45-Ausgabe enthielt auf den ersten drei Seiten durchsuchbaren Text mit Produktnamen und Preisangaben. Ein belastbares Zuordnungsverfahren *Produkt ↔ Preis ↔ Seite* muss erst validiert werden; bis dahin werden keine aus der PDF geratenen Preise ausgegeben. Eine Genehmigung für systematische Datenübernahme ist unabhängig von technischem Zugriff zu prüfen.

## Projektdateien

- [Python-Parser, Angebotsmodell und Netto-Prospektzuordnung](adapters/retailer_offers.py) mit `STORE_CONFIRMED`, `REGION_CONFIRMED`, `CHAIN_WIDE_REPORTED`, `UNKNOWN`.
- [Offline-Vertragstests](tests/test_retailer_offers.py)
- [Live-Kompatibilitätstest für PENNY, Kaufland, ALDI Nord und Lidl](tools/live_adapter_smoke.py)
- [Erweiterte technische Bewertung](reports/implementierungsstand-2026-10-31.md)
- [Testübersicht mit JSON-Artefakten](https://github.com/ecora2003-max/Try/actions)

## Bestätigte automatisierte Tests

- [PENNY, Kaufland, ALDI Nord und **direktes Lidl** – Live ALL PASS](https://github.com/ecora2003-max/Try/actions/runs/41183799427)
- [EDEKA Berlin, Hamburg, national – historischer erfolgreich abgeschlossener Forschungslauf](https://github.com/ecora2003-max/Try/actions/runs/41183681778).
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

## Geprüfte Vollständigkeit und Aktualität (31.10.2026)

[**Messbericht für Lidl, ALDI Nord, REWE und ALDI Süd**](reports/umfang-und-aktualitaet-preisdaten-2026-10-31.md): Lidl 69/69 vollständig paginierte Kategorien mit 2.005/2.005 Preisfeldern; ALDI Nord 82/82 Preise in zwei vollständigen Kategorien; REWE 72/72 Preise in sechs Suchantworten, aber Pagination `limit`/`offset` in der Probe ohne Wirkung; ALDI Süd meldet 3.538 Artikel, komplette Abfrage jedoch an HTTP 403 gescheitert. Kein Händler hat im Test eine verifizierte Garantie für die zeitliche Übereinstimmung mit dem Kassenpreis oder eine dokumentierte Preisänderungs-Latenz geliefert.

## 31.10.2026 – Gesamter Preiskatalog: ALDI Nord, REWE, ALDI Süd

[**Messbericht mit Live-Tests, Lücken und echten Pagination-Gegenproben**](reports/gesamter-preiskatalog-aldi-nord-rewe-aldi-sued-2026-10-31.md). **ALDI Nord:** 174 vollständig geladene Sortimentslisten, 1.781 verschiedene IDs; 8 von 3.706 Listeneinträgen ohne Preis, 2.307 Produktseiten in offizieller Sitemap. **REWE stationär:** stets 12 identische IDs pro Suchbegriff; getestete Pagination keine Sortimentsiteration. **ALDI Süd:** 3.537 bepreiste IDs in 60er-Seiten und 3.549 in 48er-Seiten bei gemeldetem `totalCount=3.538`; API-Seiten abrufbar, strenge 100%-Vollständigkeit nicht gesichert. Alle Änderungen ausschließlich in `Try`.

## Netto: gezielte Produktsuche mit EAN und POS-Preismodell (31.10.2026)

[**Statische API-/Live-Test-Dokumentation**](reports/netto-produktsuche-filialpreise-status-2026-10-31.md). Netto-Marken-Discount-APK: `GET rest/api/v2/productSearch?searchString&storeId` → `Product[]` mit Name/EAN/Artikel-ID **ohne Preis**. Separat `GET api/v1/mpos/{storeId}/itemInfo?itemEAN` → Antworttyp `ItemInfo[]` mit `ValidPrice.Amount` und `ValidPrice.Currency`. Der echte Server-Host und ein erfolgreicher Filialpreis-Abruf sind weiterhin nicht nachgewiesen; öffentliche Host-Kandidaten lieferten bisher nur HTML oder wurden technisch nicht angefragt. **Kein produktiver Preisadapter**, nur Testrepository `Try` verändert.

## Netto: erster echt verifizierter Onlinepreis (31.10.2026)

[**Erfolgreicher Onlinepreis-Test und Adapter**](reports/netto-onlineproduktpreis-erfolgreich-2026-10-31.md) · [Bestandener GitHub-Actions-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41205995579). Netto-Produktseite „Kölln Haferflocken kernig 500 g, 10er-Pack“: **16,90 € für 5 kg**, SKU `2162281000`, GTIN `4000540200300`, offiziell eingebettete `Product`-/`Offer`-JSON-LD-Daten. [Parser](catalogues/netto_online.py) erfolgreich gegen echte Seite geprüft. **Onlinepreis, kein Filialkassenpreis.** Der separate mobile `mpos/.../itemInfo`-Endpunkt enthält im App-Code zwar ein `ValidPrice`-Feld, antwortete aber live auf dem bisher getesteten Host nicht mit Preis-JSON; Host noch unbekannt. Produktsuche aus freien Suchbegriffen und Versandkosten fehlen noch.

## Netto: Filialangebotspreise live geprüft (31.10.2026)

[**24/24 aktuelle Netto-Filial-Angebotskacheln mit Preis, Artikelkennung und Gültigkeitsdaten verifiziert**](reports/netto-filialangebote-produkte-preise-api-pruefung-2026-10-31.md) · [GitHub-Actions-Lauf PASS](https://github.com/ecora2003-max/Try/actions/runs/41207688887). Die direkte Seite `/filialangebote` war im GitHub-Runner mit HTTP 403 nicht lesbar; dieselben Angebotskacheln sind auf der öffentlichen Kategorie-HTML-Seite `/angebote/c-N07` eingebettet. [Parser](catalogues/netto_branch_offers.py) liest nur HTML und gleicht sichtbaren Aktionspreis mit `Price` aus dem eingebetteten **nicht aufgerufenen** Wunschlistenlink ab. Vier zusätzliche App-Preise getrennt. **Nur Wochenangebote (26.–31.10.2026), keine verifizierte normale Filialpreissuche oder öffentliche Produktpreis-JSON-API.**

## Netto – weitere Preisquellen und echte Produktsuche (31.10.2026)

[**Verifizierte Freitextsuche → Netto-Onlinepreise, Methodenvergleich**](reports/netto-weitere-preisquellen-und-freitextsuche-2026-10-31.md) · [Live-Test](https://github.com/ecora2003-max/Try/actions/runs/41208278315). Der offizielle Intershop-Suchformular-Endpunkt `ViewMMPParametricSearch-SimpleOfferSearch?SearchTerm=...` funktioniert direkt; ein [Read-only-Testskript](tools/netto_search_to_online_price.py) suchte `Haferflocken`, `Mandeln`, `Reis`, fand 22 Links, prüfte 12 Produktseiten und gewann 9 numerische Onlinepreis-Datensätze. **Kein Filialkassenpreis.** Andere Quellen: dauerhafte Preissenkungen (nicht strukturiert bepreist), Filialangebote (beworbene Artikel mit Preis), Netto+ `mpos.itemInfo` (Preisfelder nur statisch, öffentliche Abrufbarkeit unbewiesen). Alle Änderungen nur in `Try`.

## EDEKA – gespeicherter Datenstand (31.10.2026)

[**Verifizierter Downloadbericht**](reports/edeka-katalog-snapshot-status-2026-10-31.md) · [Datenordner](data/edeka/2026-10-31/). Unter der vom Nutzer berichteten Freigabe wurden **256 Berliner plus 40 Hamburger Angebots-/Preisobjekte** aus offiziellen EDEKA-API-Antworten und zusätzlich **240 Produkte von öffentlichen EDEKA-Produktseiten** gespeichert. Die API-Angebotswerte beziehen sich auf den offiziell angegebenen Zeitraum 26.–31.10.2026 (UTC); die 240 Produktstammdaten besitzen **keine verifizierten Normalpreise**. Ein vollständiger offizieller Produkt-/Filialnormalpreis-Katalog wurde **nicht** erschlossen; Sortimentsuche/Sitemap HTTP 403 im Runner, Partner-Gateway verlangt einen spezifischen Zugang. Die Produktnamen wurden nach Rücklesung bereinigt und 240/240 kontrolliert. Speicherung ausschließlich im selben Repository (vorher `Try`, jetzt `EG-Preisdaten`), Hauptrepository unverändert.
