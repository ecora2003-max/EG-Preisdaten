# Vollsortiment + Normalpreise + Angebote – Machbarkeitsprüfung (31.10.2026)

**Ziel:** Produktbezogene aktuelle Normal-/Regalpreise und Werbepreise gemeinsam abfragen und **je Filiale bzw. Verkaufsregion** vergleichen. Eine beworbene Rabattaktion ist nur günstig, wenn ihr vergleichbarer Preis inklusive Mengenbasis, Coupon- und Filialbedingungen gegenüber Alternativprodukten tatsächlich konkurrenzfähig ist.

## Wichtigste Feststellung

Der bisherige Angebotsadapterdeckungsgrad ist **nicht** mit einem Vollsortiment-Preisfeed gleichzusetzen. Bei ALDI Nord konnte nun erstmals ein strukturierter **Sortiments-Preisfeed** auf Produktkategorie-Ebene durch echte Live-Anfragen und einen wiederverwendbaren Python-Parser bestätigt werden.

## Tabelle – sechs Händler

| Händler | Regulärer Sortimentskatalog | Aktuelle angezeigte Regalpreise | Angebote | Filialgenauigkeit |
|---|---|---|---|---|
| **ALDI Nord** | **Ja, zwei offizielle Produktkategorien als vollständige Algolia-JSON-Ergebnisse verifiziert** | **Ja, 82 von 82** geprüften Kategorieprodukten mit `currentPrice.priceValue` und meist Grundpreis | Ja, 276 Folgewoche-Angebote strukturiert getestet | **Noch nicht filialbezogen**; sowohl Sortiment als auch Vorschau ohne Markt-ID |
| **Lidl** | Dokumentierte `product-catalog.lidlplus.com/api/app/v1/DE/store/{id}/categories|search|products`-API | **Nicht nachgewiesen**: je zwei Varianten von Store-ID mit/ohne dokumentierte Client-Header ergaben durchgehend HTTP 400 | Ja, filialbezogene v4-API lieferte 65 einzeln normierbare Filialangebote für DE7434 | Filialbezogene **Angebote** bestätigt, Vollsortiment nicht |
| **PENNY** | Öffentliche Eigenmarken- und Sortimentsseiten, keine vollständige bepreiste API bestätigt | **Nicht nachgewiesen** | 193 bepreiste Aktionsobjekte aus 12 Kategorien für getestete Verkaufsregion | Angebote auf offizielle `sellingRegion` / `nextWeekSellingRegion` abgestimmt |
| **Kaufland** | Offizielle Werbung für über 30.000 Sortimentsprodukte, aber noch kein Gesamt-Katalog mit Filial-Normalpreisen gefunden | **Nicht nachgewiesen** | 511 echte marktgebundene Angebotsobjekte, DE5220 | Per `klNr`-Filialgültigkeitsliste nachgewiesen |
| **EDEKA** | Öffentliche Produktinformationsseiten / Eigenmarkensuche | **Flächendeckend marktbezogene Normalpreise nicht bestätigt** | Marktbezogene Angebots-API vorher technisch getestet | Markt-ID möglich; **automatisierte Verwendung nach EDEKA.de-Inhaltsbedingungen ohne ausdrückliche Freigabe gesperrt** |
| **Netto Marken-Discount** | Online-Shop-Katalog, aber nicht identisch mit Filialsortiment | **Nicht nachgewiesen**; Online- und Filialpreise können voneinander abweichen | Offizielle filialbezogene Wochenprospekt-PDF ist erreichbar und textlesbar, Preis-Produkt-Zuordnung noch unvalidiert | Zugehörigkeit des PDF-Prospekts zur konkreten Filiale nachgewiesen |

## ALDI Nord – Live-Nachweise, nicht nur öffentlich sichtbare Webseite

**Einheitliches Datenformat:** Öffentlich bereitgestellte Next.js-Daten unter `props.pageProps.algoliaState.initialResults.an_prd_de_de_products2.results[0]`.

Prüfungen:
- [Kategorieschema inkl. bepreister Algolia-Hits](https://github.com/ecora2003-max/Try/actions/runs/41186173269) – 50 Objekte mit `objectID`, `name`, `brandName`, `salesUnit`, `currentPrice.priceValue`, `basePrice`, `validFrom`, `validUntil`.
- [Zwei vollständige Produktkategorien + echter Parser und Offline-Tests – PASS](https://github.com/ecora2003-max/Try/actions/runs/41186298754): „Joghurt, Quark & Milchdesserts“ 50/50; „Milch & Milchgetränke“ 32/32. Beide Kategorien melden `nbPages=1`, `hitsPerPage=1000`; die beobachteten Antworten umfassen exakt `nbHits`.
- [Prüfung einer Produkt-ID-Zusammenführung mit Folgewoche-Angeboten](https://github.com/ecora2003-max/Try/actions/runs/41186340136): **0 Überschneidungen** zwischen 82 geprüften Normalpreisartikeln und 276 Folgewoche-Angeboten. Dies beweist **nicht**, dass eine ID-Verknüpfung generell scheitert, aber die Zuordnung von Normalpreis und Wochenangebot für denselben Artikel ist **noch nicht live belegt**.

Beispiele aus den offiziellen Produktkatalogdaten: **Bio-Quark 250 g: 0,99 € / 3,96 €/kg**, **Topi Maxi 4×100 g: 1,19 € / 2,98 €/kg**, **Schoko Drink 0,5 l: 0,85 € / 1,70 €/l**.

**Qualitätsgrenzen:** Die angezeigten `currentPrice`-Werte sind **nicht automatisch bewiesene, von Aktionen unabhängige Normalpreise**; möglich sind Sonder-/Regionalpreise. Ebenso ist kein vollständiger Kategoriebaum über das gesamte Sortiment enumeriert, kein Filialpreisfilter nachgewiesen und keine vertragliche Nutzungsfreigabe verifiziert.

Der implementierte [ALDI-Nord-Katalogparser](../catalogues/aldi_nord.py) gibt keine fälschliche Aussage „echter unveränderter Normalpreis“ aus, sondern markiert `DISPLAYED_CURRENT_NOT_PROVEN_REGULAR`. Bei unvollständiger Pagination verweigert er eine vollständige Kategorie. [Offline-Tests](../tests/test_catalogue.py).

## Lidl – tatsächlich getestete API-Varianten

Die öffentliche Drittprojekt-Endpunktliste [hakimarun/lidl-plus-api, webapp/endpoints.json](https://github.com/hakimarun/lidl-plus-api/blob/main/webapp/endpoints.json) dokumentiert einen separaten regulären Produktkatalog für `store/{storeId}/categories`, `/search`, `/products`.

Sowohl `DE7434` als auch `7434` ergaben bei je `/categories` und `/search?q=Milch` HTTP 400, und **erneut HTTP 400** mit öffentlichen Kompatibilitätsheadern. Daraus folgt **kein belastbarer Zugang** zum vollständigen Lidl-Sortiment. Die **getrennte** `offers.lidlplus.com/app/api/v4/DE/DE7434/offers`-API funktioniert und wurde als filialgebundene Angebotsquelle bestätigt. Die `clickandpick`-Quelle wurde bei nicht sicher abrufbarer `robots.txt` nicht ausprobiert.

[Feasibility-Test 1](https://github.com/ecora2003-max/Try/actions/runs/41185906846) · [Feasibility-Test 2](https://github.com/ecora2003-max/Try/actions/runs/41185956743).

## Warum „nur Sortiment“ trotzdem nützlich ist

Ein Produktstamm mit Namen, Marke, EAN/GTIN (falls verfügbar), Menge und Kategorie reicht als Ausgangspunkt für Produktabgleich, Nährwerte und eigene Preisbeobachtungen. **Keine EAN darf geraten werden.** Open Food Facts kann eventuell Produktdaten ergänzen, aber liefert **keine garantierten aktuellen Filialkassenpreise**.

## Saubere spätere Preisdatenarchitektur

Für jeden beobachteten Preis getrennt speichern:
- `retailer`, `store_id` oder `region_id`, `product_id` und falls verifiziert `gtin`;
- `pack_amount`, `amount_unit`, `drained_weight` (falls relevant), `unit_price`, `deposit`;
- `price_eur`, `price_kind` (`DISPLAYED_CURRENT`, `REGULAR_CONFIRMED`, `OFFER`, `LOYALTY_ONLY`, `UNKNOWN`), `valid_from`, `valid_to`;
- `source_url`, `checked_at`, `scope`, `confidence`, `conditions`.

Nur **denselben Artikel** (GTIN oder validierte Produktkennung) als exakt identisch vergleichen. Eigenmarken als **Alternativen** getrennt bewerten nach Produktgruppe, Packmenge, Ernährungs-/Qualitätskriterien und vergleichbarem Grundpreis. Auch mit perfektem Preisfeed werden in einem Mehrhändler-Warenkorb Wegeaufwand und Coupon-Bedingungen wichtig.

**Preisgeschichten** sollten ausschließlich aus tatsächlich nachgewiesenen Preisbeobachtungen entstehen. Der vorgebliche UVP-/Streichpreis ist kein verlässlicher Nachweis des realen früheren Marktpreises.

## Ergebnis

Aktuell **kein Händler-Vollsortiment einschließlich aller Filialnormalpreise und aktueller Angebote abschließend nachgewiesen**. **ALDI Nord** ist technisch der stärkste Kandidat für eine breite Kombination von Sortiments- und Aktionsdaten, **Lidl** für filialgenaue Aktionsdaten. Bei EDEKA und Netto bestehen darüber hinaus Zugang-/Rechte- und Datenqualitätsgrenzen.

**Wichtig:** Dieses Dokument und alle Skripte sind ausschließlich in `Try` gespeichert. Das Android-Repository `Ernaerungsgedaechnis` wurde nicht geändert.
