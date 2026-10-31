# Angebote, die in einer ausgewählten Filiale gelten – Live-Prüfung am 31.10.2026

## Prüfgegenstand

Es wird **nicht** der aktuelle Lager-/Kassenbestand einer Filiale geprüft, sondern ob die offizielle Wochenaktion für eine konkrete Filiale bzw. deren zugeordnete Angebotsregion gilt.

Alle Anfragen wurden als schonende, lesende, nicht authentifizierte öffentliche HTTP-Abfragen über GitHub Actions durchgeführt. `robots.txt` wurde überprüft, soweit erreichbar; keine Schutzmechanismen wurden umgangen.

### Reproduzierbare Testläufe

- [PENNY/ALDI Nord/Kaufland/Lidl Store Scoping](https://github.com/ecora2003-max/Try/actions/runs/41181760686)
- [PENNY verschiedene Regionen + Kaufland Verfügbarkeits-IDs + Lidl zukünftige Prospekte](https://github.com/ecora2003-max/Try/actions/runs/41181857414)
- [Lidl Prospekt Produktfeldtest](https://github.com/ecora2003-max/Try/actions/runs/41182050226)

Testscripte: `tools/store_scoping_probe.py`, `tools/specific_applicability_probe.py`, `tools/lidl_kaufland_deep.py`, `tools/lidl_product_fields.py`. Jeder Lauf hat ein JSON-Artefakt mit Metadaten und Prüfergebnissen.

## 1. Kaufland: **Ja, konkrete Filialgültigkeit über offizielle Angebotsartikel-Liste**

Ein regulärer Filialwechsel setzt laut der untersuchten [Open-Source-Implementierung](https://github.com/lesecuritae/Korbunio/blob/main/src/supermarkt/sources/kaufland.py) den Cookie `x-aem-variant=DE5220`. Auf der offiziellen Kaufland-Webseite ändert sich damit die Angebotsergebnisantwort. Die **für die Filiale beworbenen Artikelkennungen** kommen separat aus:

`GET https://filiale.kaufland.de/.kloffers.storeName=DE5220.json`

Dort sind `klNr`, `dateFrom` und `dateTo` enthalten. `klNr` kann mit `offerData.cycles[].categories[].offers[].klNr` aus der Angebots-HTML-JSON kombiniert werden. Dies ist eine Aktionsgültigkeitsliste, **keine Echtzeit-Lagerbestandsprüfung**.

Live-Ergebnisse für Woche 02.–08.11.2026:

| Filiale | Artikelkennungen mit Gültigkeit in KW45 |
|---|---:|
| DE5220, Konstanz-Petershausen | 520 |
| DE1680, Konstanz-Industriegebiet | 520 |
| DE4620, Guben | 493 |
| DE4330 (weitere Region) | 513 |

Die beiden Konstanzer Filialen lieferten identische Kennungssets. Gegenüber DE4620 hatte DE5220 **70 zusätzliche Artikelkennungen**, DE4620 wiederum **43 zusätzliche**. Gegenüber DE4330 waren es **58** gegenüber **51** exklusive Kennungen. Damit ist nachgewiesen, dass tatsächlich unterschiedliche offizielle Filiallisten existieren.

**Empfohlene Logik:** Filiale anhand offizieller Kennung wählen → `.kloffers.storeName={kennung}.json` abrufen → Artikelkennung + Gültigkeitsdatum mit regionalem Angebotskatalog verknüpfen → nur passende Angebote ausgeben. Für den Preis den Filial-Cookie `x-aem-variant={kennung}` beachten. Bei Datumswidersprüchen keine unbestätigte Zuordnung vornehmen.

## 2. PENNY: **Ja, über zugeordnete Verkaufsregion, nicht individuelle Filialartikel-Liste**

`GET https://www.penny.de/.rest/market` lieferte 2.127 Filialen mit `wwIdent`, `sellingRegion`, `nextWeekSellingRegion`, `nextWeekFlippingBookURL` (HTTP 200). Das JSON ordnet Filialen eindeutig einer Angebotsregion zu. Unter 63 Berliner PENNY-Filialen gab es **eine gemeinsame Verkaufsregion `15A-01-56`**. Im gesamten geprüften Katalog gab es **44 unterschiedliche Regionskennungen**.

Angebote der Folgewoche:

`GET https://www.penny.de/.rest/offers/by-category/2026-45/top-angebote?region=15A-01-56`

HTTP 200, neun strukturierte Produkte in `offerTiles` (z.B. Leerdammer, 140 g, 1,49 €, gesonderter App-Preis 1,29 € mit Bedingungen).

Vergleich mit Region `15A-08-26` (Delmenhorst): Die geprüften **9 Top-Angebote** waren identisch und gleich teuer. Das widerlegt die regionale Zuordnung nicht: Andere Kategorien/Prospektseiten können differieren; eine vollständige filialgenaue Kontrolle wurde nicht durchgeführt.

**Empfohlene Logik:** Gewählte `wwIdent` → `nextWeekSellingRegion` oder `sellingRegion` → Angebots-Endpunkt mit `region=` → nur Katalog dieser Region. Region ist präziser als PLZ, aber kein Einzelmarkt-Lagerbestand.

## 3. ALDI Nord: **Bundesweiter Prospekt plausibel, keine individuelle Gültigkeits-API nachgewiesen**

`GET https://www.aldi-nord.de/angebote-vorschau.html` lieferte HTTP 200 mit `__NEXT_DATA__` und darin JSON-String `apiData`. Dessen `OFFER_GET`-Request ist `{"locale":"de","week":"next"}`, Antwort mit 276 strukturierten Produktobjekten in `algoliaDataMap`.

**Kein `marketId`, `storeId`, `region` oder `postalCode` im bewiesenen Request.** Unabhängig recherchierte [Prospektmethodik](https://radarsuper.com/de/aldi-nord/prospekt) beschreibt ALDI Nords Ausgabe als bundesweit. Das genügt für die **bundesweite Prospektzuordnung mit möglicher Ausnahme**, nicht für die Garantie jedes einzelnen Produkts in jedem Markt. Auf Filialhinweise/Ausnahmen achten.

## 4. Lidl: **öffentliche API für die Folgewoche gefunden, Filialgeltung nicht automatisch gesichert**

Über offizielle Lidl-Prospektseite sind veröffentlichte Prospektkennungen abrufbar. Diese öffentliche API antwortete mit HTTP 200:

`https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=aktionsprospekt-02-11-2026-07-11-2026-fbfd28&client=lidl`

Ergebnisse für den Prospekt **02.–07.11.2026**:
- `flyer.offerStartDate = 2026-11-02`, `flyer.offerEndDate = 2026-11-07`
- `flyer.regions = [{"code":"0"}]`, 75 Prospektseiten
- `flyer.products` als Objekt mit **191 Einträgen**. Beispiele enthalten `productId`, `title`, `brand`, `price`, `description` – **aber die ersten geprüften Produkte sind Onlineshop-/Nonfood-Artikel**, nicht nachgewiesener vollständiger Lebensmittelfilialkatalog. Nicht alle Einträge als in der gewählten Filiale geltend interpretieren.

Prospekt **09.–14.11.2026** ebenfalls HTTP 200; `offerStartDate=2026-11-09`, aber `flyer.products` war zum Testzeitpunkt leer, 29 Prospektseiten vorhanden.

Die dokumentierte Lidl-Plus-Angebots-API `offers.lidlplus.com/app/api/v4/DE/{storeKey}/offers` lieferte bei den vorherigen beiden schonenden Tests HTTP 400; der Filial-Katalog von Lidl war erreichbar. Die [offiziellen Lidl-Filialseiten](https://www.lidl.de/s/de-DE/filialen/berlin-charlottenburg-wilmersdorf/berliner-str-26-27/) weisen jeweils **„Aktuelle Aktionsprospekte in der Filiale“** aus. Diese Zuordnung der Filialseite zu einem Prospekt ist der nächste saubere Weg zur filialbezogenen Gültigkeitsprüfung.

## 5. EDEKA und Netto Marken-Discount: noch keine verifizierte Live-Anbindung

Für EDEKA existiert dokumentiert `/eh/service/eh/offers?marketId=...`. Für Netto Marken-Discount existiert eine Intershop-Filialsuche. Beim verwendeten GitHub-Runner lieferte `robots.txt` auf beiden offiziellen Domains HTTP 403. Die Angebots-APIs wurden daher **nicht** weiter abgefragt. Ein 403 bei `robots.txt` beweist keine ausdrückliche Ablehnung, ist aber keine Nutzungsfreigabe.

Die [EDEKA-Angebotsseite](https://www.edeka.de/angebote/) weist selbst aus, dass Angebote nur in gekennzeichneten Märkten bzw. bestimmten EDEKA-Regionen gelten und App-Preise gesonderten Bedingungen unterliegen. [Netto Marken-Discount](https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm/1013) verlangt ausdrücklich die Auswahl einer Filiale, da Angebote nach Region differieren. Drittseiten wie [Promotheus](https://promotheus.com.de/netto-marken-discount-prospekte/prospekt-3551301-0) listen bei bestimmten Netto-Prospekten gültige Filialen auf, sind aber **keine bestätigte lizenzfreie strukturierte Produkt-API**.

## Technische Empfehlung für Ernährungsgedächtnis

Speichere getrennt:
- `source_store_id`, `selling_region_id`, `offer_id`, `price_type`, `valid_from`, `valid_to`.
- `applicability_level`: `STORE_CONFIRMED`, `REGION_CONFIRMED`, `CHAIN_WIDE_REPORTED`, `UNKNOWN`.
- `applicability_source_url`, `checked_at`, `terms_text`.

Für Kaufland nur gekennzeichnete Artikel aus der Filial-Gültigkeitsliste anzeigen; bei PENNY per Filial-Verkaufsregion filtern; ALDI Nord als allgemeinen Prospekt mit gekennzeichneter Unsicherheit; Lidl nach offizieller Zuordnung eines konkreten Prospekts zur Filiale. **Nicht „bei der Filiale geltend“ mit „aktuell vorrätig“ gleichsetzen.**

Automatisierte Weiterverwendung von Händlerdaten erfordert eine gesonderte rechtliche Prüfung; technischer HTTP-Erfolg ist keine Datenlizenz.
