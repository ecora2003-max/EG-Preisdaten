# Ernährungsgedächtnis: Implementierungsstand der Supermarkt-Angebotsquellen

**Live-Stichtag:** 31.10.2026 · **Testumgebung:** GitHub Actions Ubuntu-Runner · **Repository:** `ecora2003-max/Try`

## Zweck und Grenze

Gesucht ist, ob ein **beworbenes Angebot grundsätzlich für die ausgewählte Filiale gilt**. Es geht nicht um deren Echtzeit-Warenbestand. Eine HTTP-200-Antwort belegt technische Abrufbarkeit, **keine Erlaubnis zur automatisierten Weiterverwendung**. Es wurden weder Zugriffsbarrieren umgangen noch Händler-App-Credentials benutzt. Bei nicht abrufbarer `robots.txt` wurden direkte Abfragen vorsorglich ausgelassen.

## Ergebnis: Status pro Händler

| Händler | Datenquelle live verifiziert | Produktparser auf echten Daten getestet | Angebotsgeltung / Filiale | Entwicklungsstand |
|---|---|---|---|---|
| **PENNY** | Ja, `/.rest/market` und `/.rest/offers/by-category/{KW}/{slug}?region=...` | **193 gültige Preisobjekte** aus 12 Kategorien, 223 Rohkacheln | **Verkaufsregion bestätigt** durch offizielle `wwIdent`/ `nextWeekSellingRegion`; 63 Berliner Filialen im Test derselben Region | Implementierbarer Regionaladapter, keine Einzelmarkt-Ausnahmegarantie |
| **Kaufland** | Ja, `offerData` im HTML und `.kloffers.storeName={store}.json` | **511** Artikel mit Preis und gültiger Artikelkennung für DE5220 / KW45 | **Konkrete Filiale bestätigt** über `klNr` und Gültigkeitsintervalle; Cookie `x-aem-variant` für regionale Preise | Filialadapter als Prototyp einsatzbereit; Filialsuche/Mehrfachpreise weiter validieren |
| **ALDI Nord** | Ja, `__NEXT_DATA__` → `apiData` → `OFFER_GET`, `week=next` | **276** Preisobjekte mit Start-/Enddatum | **Kein Filialparameter** im beobachteten Request; nationale/kettenweite Vorschau, mögliche lokale Ausnahmen | Kettenweiter Adapter, Einschränkung sichtbar halten |
| **Lidl** | Ja, Prospekt `endpoints.leaflets.schwarz/v4/flyer` | **191** verlinkte Produktobjekte für 02.–07.11., teilweise Onlineshop/Nonfood | **Nicht bewiesen:** Filialseite zeigt Prospektbereich, aber es fehlt technisch verifizierte Verknüpfung zwischen StoreKey und regionalem Flyer; Lidl-Plus-Angebots-API gab HTTP 400 | Nur Prospekt-/Trenddaten als UNKNOWN, nicht als filialbestätigte Lebensmittelpreise |
| **EDEKA** | In Fremdprojekten als Filialsuche und `/eh/service/eh/offers?marketId` dokumentiert, **nicht im Runner live verifiziert** | Offline-Schemaadapter vorhanden, keine Live-Prüfung | Ein Markt-ID-Parameter ist dokumentiert; Bestätigung der konkreten Markt-Gültigkeit fehlt | **Blockiert** durch fehlende nachgewiesene öffentliche Abrufmöglichkeit / Freigabe |
| **Netto Marken-Discount** | In Fremdprojekt Filialfinder-API dokumentiert, offizieller Filialauftritt zeigt Angebote; keine strukturierte Produkt-API live verifiziert | **Kein** ehrlicherweise nutzbarer offizieller JSON-Angebotsadapter | Filialauswahl erforderlich und angebotsrelevant | **Blockiert**; Adapter verweigert unbestätigte Daten |

## Reproduzierbare Beweise und Dateien

- [Letzter bestandener Live-Integrationstest (PENNY/Kaufland/ALDI Nord/Lidl)](https://github.com/ecora2003-max/Try/actions/runs/41182962632), JSON-Artifact `retailer-adapter-live-compatibility`.
- [Bestandene Offline-Adaptertests](https://github.com/ecora2003-max/Try/actions/runs/41182891433).
- [PENNY weitere Kategorien, aktueller Test](https://github.com/ecora2003-max/Try/actions/runs/41182906512).
- [PENNY erste zusätzliche Kategorien](https://github.com/ecora2003-max/Try/actions/runs/41182827144).
- [Kaufland Region-/Filialgültigkeit und Lidl Prospekte](https://github.com/ecora2003-max/Try/actions/runs/41181939368).
- [Lidl: 191 Produktdatensätze auf 75 Prospektseiten verlinkt](https://github.com/ecora2003-max/Try/actions/runs/41182733785).
- [Lidl: drei konkrete Berliner Filialseiten](https://github.com/ecora2003-max/Try/actions/runs/41182671688), HTML abrufbar, aber keine eindeutigen Prospekt-IDs im statischen HTML.
- Quellcode: [Parser und Datentypen](../adapters/retailer_offers.py), [Offline-Tests](../tests/test_retailer_offers.py), [Live-Smoke](../tools/live_adapter_smoke.py).

## Angebotsmodell für die Android-App

Die einheitliche Python-Prototypstruktur `Offer` hat `retailer`, `product_id`, `title`, `price_eur`, `quantity`, `valid_from`, `valid_to`, `scope`, `scope_id`, `price_condition`, `note`; `Offer.to_dict()` ist für die JSON-Übertragung vorbereitet.

- **STORE_CONFIRMED:** Offizielle Angebotsartikel-ID für die explizit ausgewählte Filiale über Datumsfenster belegt (derzeit Kaufland).
- **REGION_CONFIRMED:** Offizieller Katalog der Region, der die ausgewählte Filiale angehört (derzeit PENNY).
- **CHAIN_WIDE_REPORTED:** Kettenweite Prospektdaten ohne individuellen Filialfilter (ALDI Nord); lokale Ausnahmen ausdrücklich möglich.
- **UNKNOWN:** Keine belastbare Filialgeltung (derzeit Lidl, EDEKA-Schema).
- Netto: fail-closed / keine erfundenen Treffer.

**Nicht alle Preise gleich behandeln:** Normale Angebotspreise und App-/Mitgliedspreise müssen getrennt bleiben, bei PENNY etwa 1,49 € versus 1,29 € mit Fußnoten. Keine Rabattpreis- oder Ausverkaufsannahme ohne ausreichenden Beleg.

## Details nach Anbieter

### PENNY: 12 bestätigte Kategorienslugs für KW45 / Berliner Region 15A-01-56

`top-angebote`, `kuehlregal`, `getraenke`, `weitere-angebote`, `obst-und-gemuese`, `fleisch-und-wurst`, `drogerie-und-haushalt`, `suessigkeiten-und-snacks`, `penny-ready`, `puda`, `best-moments`, `pflanzen`.

Die Filial-Metadaten enthalten `wwIdent`, `sellingRegion`, `nextWeekSellingRegion`, `nextWeekFlippingBookURL`. Für nächste Woche **`nextWeekSellingRegion` nicht durch `sellingRegion` ersetzen, wenn es abweicht**.

223 Rohkacheln wurden auf 193 eindeutige bepreiste Einträge normalisiert (andere Einträge waren unbepreist/ungeeignet oder redundant). Die Kategorieabdeckung ist **noch nicht als vollständig** nachgewiesen; andere Aktionskategorien könnten existieren. Ein `week`-Enddatum (Sonntag) ist **kein Beleg** für individuelle Gültigkeit bis Sonntag; deshalb setzt der Parser ohne Einzelquellendatum `valid_to=null`.

### Kaufland: genaue Filialgeltung und Preisquelle

`GET https://filiale.kaufland.de/.kloffers.storeName=DE5220.json` enthält `klNr`, `dateFrom`, `dateTo`; im Test 520 Aktionsartikelkennungen für KW45. Für die regionalen Preise wird `GET https://filiale.kaufland.de/angebote/uebersicht.html?kloffer-week=next` mit `Cookie: x-aem-variant=DE5220` verwendet; der Parser bildet den Schnitt der `klNr`-IDs und gültigen Zeitfenster. Das letzte Live-Ergebnis waren **511** passende Preisobjekte.

Gegenüber Filiale DE4620 unterschieden sich die offiziellen Artikel-ID-Sets für KW45: 70 IDs ausschließlich bei DE5220, 43 ausschließlich bei DE4620. So lässt sich die Filialgeltung **tatsächlich** unterscheiden. Ausnahmen und widersprüchliche Promo-/Verkaufsdatumsfelder werden konservativ behandelt. Ein vollständiger Filial-Resolver für freie Adresssuche und robustes Multibuy-/Card-XTRA-Parsing sind noch Integrationsaufgaben.

### ALDI Nord: korrektes verschachteltes Preisformat

`props.pageProps.apiData` ist zunächst eine als String kodierte JSON-Liste; Element `OFFER_GET` enthält `req={"locale":"de","week":"next"}` und `res.algoliaDataMap`. Jeder Artikel besitzt `name`, `objectID`, `currentPrice.priceValue` und teils `currentPrice.validFrom/validUntil` als Unix-Zeitstempel bzw. `promotionPrices`. Der Adapter wandelt Zeitstempel in **Europe/Berlin** um und gibt für Erdnüsse beispielsweise **1,39 € / 180-g-Dose / 02.–07.11.2026** zurück. Insgesamt 276 gültige Objekte.

Eine tatsächliche Filialzuordnung jenseits der allgemeinen Kettenwerbung ist **nicht nachgewiesen**. Das Produktfeld `isAvailable` allein ist keine Filial-Gültigkeitsbestätigung.

### Lidl: neue öffentlich erreichbare API, aber bislang keine marktsichere Lebensmittelliste

Die Prospektseite `https://www.lidl.de/c/online-prospekte/s10005610` verlinkt Prospektkennungen für die laufende und folgende Wochen. `GET https://endpoints.leaflets.schwarz/v4/flyer?flyer_identifier=aktionsprospekt-02-11-2026-07-11-2026-fbfd28&client=lidl` lieferte HTTP 200, Prospektseiten, 191 Produktkarten mit Preis, Bezeichnung und Link. Alle 191 waren mit Seitenlinks verknüpft; teils zeigen sie auf Lidl.de-Onlineshop-Produkte, daher keine belastbare Filialgültigkeit aus dieser Zuordnung allein.

Das ebenfalls verfügbare Prospektfenster 09.–14.11. war zum Testzeitpunkt als JSON mit 29 Seiten und **0** Produktobjekten vorhanden. Die Lidl-Plus-StoreKey-Angebots-API gab bei zwei unproblematischen Testvarianten HTTP 400. Drei konkrete Berliner Lidl-Filialseiten lieferten HTTP 200, aber keinen im getesteten statischen HTML identifizierbaren Prospekt-Slug. Die offizielle Lidl-Website bestätigt, dass Prospekte nach Filialauswahl erhältlich sind, was gerade gegen ein pauschales Verallgemeinern eines überregionalen Prospekts spricht.

### EDEKA

Quellcodebelege:
- [FaserF/ha-edeka – Filialsuche `/api/marketsearch/markets` und Angebote `/eh/service/eh/offers`](https://github.com/FaserF/ha-edeka/blob/main/custom_components/edeka/api.py)
- [ByteSizedMarius/edekompile – alternative App-REST-API](https://github.com/ByteSizedMarius/edekompile)

Der App-REST-Weg benötigt App-level OAuth; aus der Veröffentlichung der Clientdaten in einer fremden Software entsteht **keine Nutzungserlaubnis**. Diese Daten wurden nicht übernommen oder benutzt. Die Web-APIs wurden im GitHub-Runner nicht live bestätigt (`robots.txt` HTTP 403); technische Nutzbarkeit und Bedingungen bleiben offen.

### Netto Marken-Discount

Die offizielle Filialsuche ist aus [Korbunio `netto_marken.py`](https://github.com/lesecuritae/Korbunio/blob/main/src/supermarkt/sources/netto_marken.py) dokumentiert. [Offizielle Netto-Filialbeispielseite](https://www.netto-online.de/filialen/berlin-charlottenburg/wilmersdorfer-str-46/7679/?stores_id=7679) zeigt ausdrücklich aktuelle Filialangebote und den Prospekt der Folgewoche. Das ist ein Beleg, dass das **Angebotskonzept filialbezogen** ist; es ist kein nachgewiesener strukturierter Datenfeed. `robots.txt` von `www.netto-online.de` war vom GitHub-Runner mit HTTP 403 nicht abrufbar. Eine unlizenzierte Drittanbieter-Aggregation würde die Filialgeltung nicht automatisch absichern.

## Offene, nicht durch bloßes Programmieren behebbare Punkte

1. **EDEKA / Netto:** Autorisierter und technisch funktionierender Abruf inklusive expliziter Filialzuordnung. Ohne echte Zugriffsfreigabe kann keine belastbare Produktivabdeckung behauptet werden.
2. **Lidl:** Produktfilter Lebensmittel-vor-Ort vs. Onlineshop, Filialzuordnung des Prospekts oder legale Lidl-Plus-API-Nutzung. Andernfalls Kennzeichnung UNKNOWN.
3. **ALDI Nord:** Kettenweite Angebote dürfen nicht als garantiert in jedem Markt gelten, bis eine offizielle Ausnahmeregel bzw. lokaler Filter nachgewiesen ist.
4. **PENNY:** Zusätzliche Kategorien und produktspezifische Verkaufsintervalle erfassen. Die bisherigen 12 Kategorien sind empirisch verifiziert, nicht als vollständig nachgewiesen.
5. **Alle:** Nutzungsbedingungen, Drittverwertung und ggf. kommerzielle Weiterverwendung rechtlich klären; Ratenbegrenzungen, Caching, Fehlerfälle und Datenprovenienz definieren.

## Übergabe an Codex / Android-Implementierung

Die Python-Adapter sind **Referenzimplementierung**, keine bereits eingebauten Kotlin-Dateien. In die Android-App lassen sich Datentypen, Parser und scope-Klassen portieren. Für bestätigte Datensätze die ausgewählte Filiale bzw. Regionskennung zusammen mit dem Datenabrufzeitpunkt speichern. Für unbestätigte Märkte Treffer als `UNKNOWN` zeigen oder in der gefilterten Einkaufsempfehlung ausschließen.

Die Codebasis der Android-App im anderen Repository wurde bei diesen Tests **nicht** verändert.
