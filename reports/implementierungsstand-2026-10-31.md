# Technischer Test- und Implementierungsstand: Filialangebote

**Stand:** 31. Oktober 2026 (historischer Snapshot; keine Live-Zusage für spätere Wochen) · **Ausführung:** GitHub Actions (Linux, Python) · **Ziel:** Angebot *gilt grundsätzlich* im ausgewählten Markt, nicht Prüfung des Lagerbestands.

## 1. Verifizierte Datenquellen

| Händler | Verifizierter Zugriff | Ergebnis und Geltung | Implementierungsgrenze |
|---|---|---|---|
| **PENNY** | `/.rest/market`; `/.rest/offers/by-category/{KW}/{slug}?region={sellingRegion}` | 193 eindeutige preislich interpretierbare Artikel aus 223 Rohkacheln/12 Kategorien für KW45. Berliner Region `15A-01-56` gehört zu 63 getesteten Märkten. `REGION_CONFIRMED`. | Einzelne Filialausnahmen und produktgenaue Enddaten noch nicht bestätigt |
| **Kaufland** | `/.kloffers.storeName=DE5220.json` und Angebotsübersicht `offerData` mit `x-aem-variant=DE5220` | 511 bepreiste Aktionsartikel im offiziellen Filial-Angebotszeitraum (KW45). `STORE_CONFIRMED`. | Card-XTRA/Mehrfachpreise und freie Filialsuche weiter verbessern |
| **ALDI Nord** | `__NEXT_DATA__` → `apiData` → `OFFER_GET,week=next` | 276 bepreiste Angebote. `CHAIN_WIDE_REPORTED`. | Keine bestätigte Abbildung von lokalen Filialausnahmen |
| **Lidl** | `stores.lidlplus.com/api/v4/DE` und `offers.lidlplus.com/app/api/v4/DE/{storeKey}/offers` | Filiale DE7434: 78 Angebotsobjekte, davon 65 direkte `StoreSpecialPriceDiscount` mit Preis und Datum. `STORE_CONFIRMED`. Hannover DE7602 72 Objekte, sechs nur in Berlin. | Weitere Rabattmechaniken nicht als gewöhnliche Einzelpreise interpretieren; Vorschau der Folgewoche ggf. erst später verfügbar |
| **EDEKA** | `edeka.de/api/marketsearch/markets`; `edeka.de/eh/service/eh/offers?marketId=...` | Berlin-ID 10003451: 256 Angebote, Hamburg-ID 913988: 40, beide `national:false`. Fallback `marketId=1`: 28, `national:true`. Technisch `STORE_CONFIRMED` nur für `national:false`. | **Kein regulärer automatisierter Betrieb ohne ausdrückliche EDEKA-Zustimmung**; EDEKA.de-Nutzungsbedingungen untersagen automatisierte Datenübernahme |
| **Netto Marken-Discount** | **Offizielle Prospektübersicht mit `stores_id` und eigener Publitas-Prospekt-/PDF-Adresse pro Filiale** | Für Filiale `7679` und `8135` wird die tatsächliche Adresse und der individuelle KW45-Prospekt nachgewiesen. Berliner PDF: 72 Seiten/36,4 MB, Text extrahierbar. | Filialprospekt technisch implementiert, Produkt-Preis-Paare **nicht** validiert; automatischer Warenkorb-Feed noch offen |

Diese Ergebnisse belegen **technische Erreichbarkeit und Parserfunktion**, keine Nutzungsrechte. Ein Betrieb und insbesondere eine öffentliche Weiterverwertung sind separat mit den Händlern abzuklären.

## 2. Reproduzierbare Live-Tests

- **[Live-Adaptertest PASS für Penny/Kaufland/ALDI Nord/Lidl](https://github.com/ecora2003-max/Try/actions/runs/41183799427)**. [Code](../tools/live_adapter_smoke.py).
- **[Lidl DE7434 vs. DE7602 – Original-JSON-Schema, Filialdifferenz](https://github.com/ecora2003-max/Try/actions/runs/41183580801)**. [Code](../tools/lidl_stores_live.py).
- **[EDEKA Berlin/Hamburg und national fallback – abgeschlossener Forschungslauf](https://github.com/ecora2003-max/Try/actions/runs/41183681778)**. [Code](../tools/edeka_live_adapter.py). EDEKA-Code ist danach durch eine Freigabebedingung geschützt und darf nicht ohne Erlaubnis erneut ausgeführt werden.
- **[Kaufland konkrete Angebotskennungen je Filiale](https://github.com/ecora2003-max/Try/actions/runs/41181939368)**.
- **[PENNY 12 Kategorien als JSON](https://github.com/ecora2003-max/Try/actions/runs/41182906512)**.
- **[Netto ohne Umgehung in normalem Chrome geblockt](https://github.com/ecora2003-max/Try/actions/runs/41183768242)**.
- **[Offline-Unit-Tests](https://github.com/ecora2003-max/Try/actions)** [Quellcode](../tests/test_retailer_offers.py).

Die Tests wurden auf realen Daten durchgeführt und die Ergebnisse in GitHub Actions als JSON-Artefakte protokolliert. Skripte und Parser benötigen keine privaten Händler-Credentials. Einige unabhängige Bestands- und Prospektquellen wurden recherchiert, **aber nicht als freie Weiterverwendungslizenz anerkannt**.

## 3. Technische Details und Vorsichtsmaßnahmen

### PENNY

Offizieller Filialkatalog `GET https://www.penny.de/.rest/market` liefert `wwIdent`, `sellingRegion`, `nextWeekSellingRegion`. Für den nächsten Angebotszeitraum die **`nextWeekSellingRegion` der explizit ausgewählten Filiale** verwenden. Tests belegten 44 verschiedene Regionskennungen, jedoch nicht alle Kategorien vollständig. Verifizierte Slugs:

`top-angebote`, `kuehlregal`, `getraenke`, `weitere-angebote`, `obst-und-gemuese`, `fleisch-und-wurst`, `drogerie-und-haushalt`, `suessigkeiten-und-snacks`, `penny-ready`, `puda`, `best-moments`, `pflanzen`.

Alle Kacheln über eindeutige `uuid` zusammenführen und widersprüchliche Preisangaben abweisen. **Beispiel:** Leerdammer 140 g 1,49 €, möglicher App-Preis 1,29 € mit Fußnoten. Nicht als allgemein geltenden Kassenpreis behandeln. Die URL-Kalenderwoche liefert **kein garantiertes individuelles Enddatum**, darum `valid_to=null`, solange nicht gesondert belegt.

### Kaufland

Nur Artikel aus der aktiven filialbezogenen Liste `https://filiale.kaufland.de/.kloffers.storeName=DE5220.json` (jeweils `klNr`, `dateFrom`, `dateTo`) mit den Preis- und Produktobjekten aus `offerData` kombinieren. Für die Angebotspreise Filialauswahl `Cookie: x-aem-variant=DE5220`. Unterschiede zwischen Filialen explizit festgestellt (z. B. DE5220 vs. DE4620: 70 bzw. 43 exklusive Artikel-IDs für KW45).

### ALDI Nord

In `__NEXT_DATA__` liegt `apiData` als JSON-String vor. `OFFER_GET` mit `req={"locale":"de","week":"next"}` liefert `res.algoliaDataMap`, Preis `currentPrice.priceValue` und ggf. Promotion-Gültigkeitszeiten als Unix-Timestamps (Berlin-Zeitzone). Kein Marktfilter im beobachteten Request; entsprechende Artikel nur als allgemeine Vorschau kennzeichnen.

### Lidl

Der direkte Angebots-Endpoint liefert mit **öffentlicher** StoreKey aus dem Filialkatalog und den dokumentierten Kompatibilitäts-Headern `X-Client-Version: 17.0.5`, `X-Client-Platform: android`, `Accept-Language: de-DE,de;q=0.9`, `Accept: application/json` in zwei Tests HTTP 200. Keine Benutzeranmeldung oder OAuth im Test erforderlich.

StoreKeys DE7434 (Berlin) und DE7602 (Hannover) lieferten 78 bzw. 72 Aktionen. Angebotsobjekte haben `id`, `title`, `brand`, `offerType`, `category`, `redemptionChannel`, `priceBox.largePartNumeric`, `startValidityDate`, `endValidityDate`. Die ersten 65 Berliner Einträge vom Typ `StoreSpecialPriceDiscount` wurden normalisiert, Onlineaktionen und Rabattmechaniken ohne sicheren Einzelstückpreis werden ausgelassen. Beispielsweise 1,49 € statt 3,99 € für Mövenpick Eis; die Beispielaktion endet 31.10.2026. Die zusätzliche öffentliche Leaflet-API liefert 191 Produktlinks aus 75 Prospektseiten, aber ohne gesicherte individuelle Filialzuordnung; diese Quellen nicht vermischen.

### EDEKA: wichtiger rechtlicher Stopp

Die API ist technisch arbeitsfähig (Markt-ID, Preisfelder, `national:false`, Start-/Enddatumswerte in Unix-Millisekunden). **Aktuelle [EDEKA.de Website-Inhaltsbedingungen](https://www.edeka.de/services/nutzungsbedingungen/) verbieten jedoch automatisiertes Erfassen, Speichern, Zusammenführen und Wiederverwenden der Webseiteninhalte ohne ausdrückliche vorherige Zustimmung.** Aus HTTP 200 folgt keine Genehmigung. Deshalb sind `tools/edeka_live_adapter.py`, `tools/edeka_netto_basic_http.py` und `tools/edeka_netto_market_source.py` gegen unbeabsichtigte Aufrufe geschützt (ohne `EDEKA_PERMISSION_CONFIRMED=1` keine neue Anfrage). Ein produktiver Entwickler muss eine gültige Erlaubnis/vertragliche API-Nutzung klären.

### Netto Marken-Discount: Filialprospekt-Zuordnung **erfolgreich**, Preiszuordnung weiterhin offen

Die statischen Einzel-Filialseiten und `/filialangebote` liefern teilweise HTTP 403 bzw. in einem normalen Headless Chrome eine `Access Denied`-Seite. **Die offizielle Filialprospektübersicht ist dagegen direkt erreichbar**:

`GET https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm?stores_id=7679`

Die öffentliche Antwort (HTTP 200) enthält eine eindeutige Filialadresse und den regulären Filial-Wochenprospekt als Link:

`https://wochenprospekt.netto-online.de/hz45_besb/?storeid=7679`

Für Kaiserslautern mit ID `8135` lautet der nachgewiesene KW45-Prospekt-Link:

`https://wochenprospekt.netto-online.de/hz45_wrse/?storeid=8135`

Diese beiden Filialen benutzen unterschiedliche Prospektkennungen. Der Viewer gibt für jede Filiale eine **regulär abrufbare PDF von `view.publitas.com`** aus, ohne Login und ohne Browser-Stealth. Ein zeitlich und mengenmäßig begrenzter Test der Berliner PDF ergab:

- **72 Seiten**, **36.411.054 Byte**;
- `pdftotext -layout` konnte lesbaren Text extrahieren, darunter Angebotszeitraum 02.–07.11.2026 und Produktnamen;
- die ersten drei Seiten enthielten **80 preisähnliche Zahlenfolgen**, jedoch auch Streichpreise, Grundpreise und Mengeneinheiten;
- deshalb ist die fehlerfreie Verbindung *Produktname ↔ korrekter Aktionspreis ↔ Gültigkeit* **noch nicht erwiesen**.

**Neuer implementierter Parser:** `netto_store_prospects(page_html, store_id)` in [`adapters/retailer_offers.py`](../adapters/retailer_offers.py) prüft den ausgewählten Markt anhand der offiziellen Adresse und validiert eine Prospekt-URL nur, wenn die `storeid` im Link genau übereinstimmt und der Host `wochenprospekt.netto-online.de` ist. Er setzt explizit `offers_parsed=false`; keine fälschlich versprochenen Einzelpreise. [Offline-Test](../tests/test_retailer_offers.py) und [Live-Test für Berlin/Kaiserslautern – PASS](https://github.com/ecora2003-max/Try/actions/runs/41184627158). [PDF-Texttest – PASS](https://github.com/ecora2003-max/Try/actions/runs/41184427978). [Blockierter Filialproduktseiten-Check](https://github.com/ecora2003-max/Try/actions/runs/41184674088).

Die PDFs wurden nur im flüchtigen GitHub-Runner verarbeitet und nicht im öffentlichen Repository gespeichert. Rechte für eine reguläre automatisierte Übernahme der Prospektinhalte in die eigene App müssen vor Produktivbetrieb gesondert geklärt werden; Zugriffsmöglichkeiten alleine erteilen keine Lizenz.

## 4. Nächste Implementierungsschritte in der Android-App

[Parser und Angebotsdatentyp](../adapters/retailer_offers.py) und [Vertragstests](../tests/test_retailer_offers.py) sind in Python als Referenz implementiert, **noch nicht nach Kotlin portiert**. Zu implementieren bleiben: Nutzer-Filialauswahl und persistierte Store-/Regionskennungen, eine kontrollierte Abfrage-/Cache-Schicht, fehlertoleranter JSON-Import, Preis-/Packungsnormalisierung, Unterscheidung App-Preis/Kassenpreis und tagesgenauer Gültigkeit, UI für verbleibende Angebotsunsicherheit und Datenschutz/Lizenzen.

**EDEKA bleibt aus Nutzungsrechtsgründen gesperrt; Netto besitzt einen technisch verifizierten Filial-Prospektadapter, jedoch noch keinen verlässlichen Produkt-Preis-Parser.** Technisch erreichbare Daten sind nicht automatisch legal in eigene Produkte übertragbar. Eine vollständige, verlässliche Sechs-Händler-Produktion kann deshalb derzeit nicht seriös als abgeschlossen bezeichnet werden.
