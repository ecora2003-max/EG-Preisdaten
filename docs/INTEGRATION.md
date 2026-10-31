# Codex-Integrationsleitfaden – Preisdatenmodul

Stand 31.10.2026 · **Fachvertrag `1.0.0-draft`**, Architekturcommit `d22862739bd0e3ef8451ce029e54f7c33ee53e40`. Python-Fachkern `price_module` 0.1.0; keine Android-, Room-, Sheets- oder Serverpflicht.

## Schnittstellen

```python
from price_module import PriceService, provider_registry, resolve_stores
p = PriceService()
output = p.search(request, datasets, kind="BOTH")  # SALE/REGULAR/BOTH
sales = p.search_offers(request, datasets)
catalog = p.search_catalog_prices(request, datasets)
one = p.lookup_price(request, datasets, "SUPPLIER-ARTICLE-ID")
coverage = p.get_coverage(request, datasets)
stores = resolve_stores("LIDL", exact_official_records, "DE7434")
```

**Synthetisches Kommando:** `python3 -m price_module < examples/synthetic-price-query.json`.

`request`:
```json
{"retailerIds":["LIDL","REWE"],"shoppingDate":"2026-10-31","windowStart":"2026-10-31","windowEnd":"2026-11-07","maxResults":100,"query":"Milch","usageMode":"RESEARCH_ONLY"}
```

`retailerIds`: ALDI_NORD, ALDI_SUED, LIDL, REWE, EDEKA, NETTO_MD, PENNY, KAUFLAND. `shoppingDate` erforderlich; Zeitfenster inklusive, `query` optional, Limit 1–1000. `usageMode=APP_DISPLAY` verweigert externe Händler-Snapshots mit ungeklärten Nutzungsrechten; `RESEARCH_ONLY` dient rein lesender technischer Prüfung und erlaubt keine produktive Darstellung.

Ein `dataset` liefert **vorher berechtigt erworbene** offizielle Rohdaten, nie einen automatischen GET:
```json
{"retailerId":"REWE","channel":"REGULAR","origin":"official-retailer",
 "sourceUrl":"https://www.rewe.de/api/stationary-product-search/products",
 "observedAt":"2026-10-31T12:00:00+01:00","httpStatus":200,
 "contentType":"application/json","storeId":"840174",
 "scopeProof":{"storeId":"840174","sourceRef":"documented-official-store-selection"},
 "body":{"products":[]}}
```
Die Beispielantwort ist synthetisch leer. `scopeProof` ist **kein kryptografischer Nachweis**; Codex darf es nur bei nachgewiesener exakter Filial-/Regionszuordnung setzen. Ohne oder bei widersprüchlichem Beleg wird der Ergebnis-Scope UNKNOWN. Filial-IDs sind nur zusammen mit Händler-ID gültig. `resolve_stores` macht keine Netzwerk-Filialsuche, sondern löst bereits belegte genaue Store-IDs auf.

Unterstützte `channel=SALE`: PENNY `offerTiles` mit `regionId,weekStart`; Kaufland `body.page,body.availability,storeId,firstDay,lastDay`; ALDI Nord `OFFER_GET`; Lidl `offers,storeId`; EDEKA `docs,marketId=storeId`; Netto HTML-Angebotskacheln (`contentType=text/html`) ohne bestätigte Einzelmarkt-Geltung. REWE/ALDI-Süd eigene Aktionsfeeds fehlen noch. `channel=REGULAR`: REWE stationäre `products/pricing`; ALDI Süd `data/price.amountRelevant` Cent; Lidl `mode=search`, `mode=category` (offset/limit) oder `mode=category-pages` mit fortlaufender Liste `[{payload,offset,limit}]`; ALDI Nord `__NEXT_DATA__`-HTML; Netto offizielles Shop-Produkt-JSON-LD (`ONLINE_LISTED`). Penny, Kaufland, EDEKA besitzen bislang keinen bestätigten kompletten regulären Filialpreisadapter.

`format=synthetic-fixture`, `fixture=true` und eine synthetische `body`-Zeilenliste sind allein für Offline-Demo-/Vertragstests vorgesehen. Andere Händler-HTML/API-Snapshots werden über die vorhandenen Legacy-Parser normalisiert.

## Ergebnis und Fehlervertrag

`output` = `{contractVersion,observations,coverage,errors,warnings}`. Jede Beobachtung ist ein eigenständiger JSON-Vertragsumschlag `price.observation` mit `contractVersion=1.0.0-draft` nach `EG-Architecture/contracts/v1/contract.schema.json` (lokal in `tests/fixtures` gespiegelt und gegen das Schema getestet). `coverage` und `errors` sind modulinterne Antwortdatentypen, keine vom Architekturvertrag vorgetäuschten neuen Nachrichtentypen.

Einzeln benannte Felder: `payload.article` (Name, Händler-SKU, gültig geprüfte GTIN, Bio=null falls unbekannt, Mengen), `payload.scope` (STORE_CONFIRMED/REGION_CONFIRMED/CHAIN_WIDE_REPORTED/ONLINE/UNKNOWN), `priceCents` integer/null, `priceKind` (SALE/CURRENT_DISPLAYED/LISTED_REGULAR/ONLINE_LISTED), `validFrom/validUntil`, `depositCents` integer/null, `conditional`, `source.observedAt,source.url,source.rightsStatus,source.dataQuality,source.parserVersion`. `eg-preisdaten:targetDateStatus` beschreibt ausdrücklich nicht belegte Zukunftsgültigkeit: `PUBLISHED_WINDOW` / `PARTIAL_VALIDITY_UNKNOWN` / `OBSERVED_ONLY_NO_VALIDITY_PROOF`; ein heutiger Preis wird **nicht** rückwirkend als Preis an einem früheren Datum oder ohne Beleg als zukünftiger Kaufpreis bewertet. `oldPrice` wird nie als vorheriger bezahlter Preis behandelt.

Bei vollständiger geprüfter **einer** Lidl-Kategorie kann `coverage.complete=true` sein; dies behauptet niemals vollständiges Filialsortiment. Partiell gelieferte Kategorien, Daten-Scopes, Rechte und fehlende Preise bleiben offen. Dataset-Parsing ist atomar; ein defekter Datensatz führt zu vollständigem Rollback der betreffenden Quelle, nicht zu Teilannahme. `errors`: SOURCE_BLOCKED (403), RATE_LIMITED (429), NO_CONTENT (204), UPSTREAM_ERROR, INVALID_SOURCE, INVALID_CONTENT_TYPE, INVALID_TIMESTAMP, SCHEMA_CHANGED, INVALID_CURRENCY, INVALID_DATE, INVALID_PRICE, INVALID_CONDITION, INVALID_PAGINATION, RIGHTS_NOT_CLEARED, UNSUPPORTED_SOURCE.

## Android-Pfad / Codex

1. Architektur-Vertrag vom aktuellen Commit lesen und Version gegen lokale Fixture-Hashes kontrollieren.
2. Reinen `price_module/service.py`-Snapshot-Transformationskern und erforderliche Parser als pure Kotlin-Funktionen portieren (`BigDecimal` oder exakte integer Cents, `LocalDate`, Offset-Zeitstempel, JSON-Schema-kompatible DTOs). **Kein Python, kein Server, keine Bezahl-API auf Android notwendig.**
3. Berechtigter Netz-/Cache-Adapter bleibt getrennt und standardmäßig deaktiviert, bis konkrete Quellenrechte geprüft wurden. Er liefert marktgebundene Snapshots; `APP_DISPLAY` bleibt bis zur Rechteklärung geschlossen. Kein Import privater Google-Sheets-Daten.
4. Canonical-DTOs nur in **lesende** Preis- und Einkaufsansichten überführen. Haupt-App `data/local/FoodStore.kt` ist Eigentümer bestehender Room-/Buchungslogik. Keine Bestands-, Kauf-, Bon-, Budget- oder Verzehrbuchungen durch Preisabfragen. Android-Erkennung/OCR unverändert wiederverwenden.
5. Identische positive/negative Fixtures nach Kotlin portieren, App JVM-/Migrations-/Regressions- und echte Gerätetests absolvieren. `INTEGRATED` erst durch Codex nach Prüfung.

**Präziser Ist-Stand:** Python-Referenz und Offline-CLI funktionieren und wurden in [CI](TEST_REPORT.md) nachgewiesen, keine direkte Android-Bibliothek und kein für produktive Nutzung freigegebener Live-Feed. [Quellenrechte](SOURCES.md) und [Status](STATUS.md) sind explizite Freigabegates.

## Erweiterte Port- und Qualitätsangaben (Code `b201eed8cd9b5ab5de0db54cfa1cefd43727f234`)

`request.storeSelections` ist eine optional pro Händler gebundene Map, z. B.
```json
{"LIDL":{"storeId":"DE7434"},"PENNY":{"storeId":"MARKET-1","regionId":"R1"}}
```
Ein fehlender Zusammenhang zwischen Filiale und regionalem Feed führt zu `OUT_OF_SCOPE` bzw. `NO_MATCHING_SCOPE`, nicht zu einer vermeintlich gültigen Filialpreisbehauptung. Kettenweite Daten bleiben nur als `CHAIN_WIDE_REPORTED` sichtbar; fehlender Store-Filter ist **keine** Marktbestätigung. `retailerArticleId` kann schon vor einem Ergebnislimit gefiltert werden, auch über `lookup_price`. `matchedCount` und `outputTruncated` unterscheiden vollständig normalisierte Eingabedaten von der begrenzten Antwort.

Zusätzliches, ausdrücklich **namespaced** Datenmaterial innerhalb des Preis-Payloads:
- `eg-preisdaten:conditionalPrices` ist eine Liste getrennter `{priceCents,access,evidence,termsVerified:false}`-Belege für z. B. Lidl Plus/Netto App. Sie sind **keine** bedingungslos nutzbaren Vergleichspreise; **nicht** automatisch in `priceCents` einsetzen.
- `eg-preisdaten:advertisedBenefitText` bewahrt PENNY-Fußnotenpreise, auch wenn wegen Zusatzzeichen keine sichere Cent-Berechnung möglich ist. `conditional` kennzeichnet ungeklärte Bedingungen.
- `eg-preisdaten:referenceOldPriceCents` und `eg-preisdaten:referenceOldText` bewahren beobachtete Streichpreisreferenzen, ohne echte historische Kassenpreise zu behaupten.
- `eg-preisdaten:reportedBaseUnitPrices` enthält Quellangaben `{basis:"kg"|"l",priceEur:"…"}`, **kein nachgerechnetes Grundpreisversprechen**; `eg-preisdaten:advertisedUnitPrice` hält ansonsten nur die unveränderte Quelltextangabe. Packungsmenge und Grundpreisreferenz müssen getrennt bleiben.
- `eg-preisdaten:priceWithoutDepositCents`, `eg-preisdaten:hasDiscount`, `eg-preisdaten:hasConditionalOffer` und `eg-preisdaten:targetDateStatus` ergänzen Quellen- und Gültigkeitswarnungen.

Quellenstatus `UNVERIFIED`/`RESTRICTED` bleibt ein Produktiv-Gate; `usageMode=APP_DISPLAY` blockiert entsprechende echten Snapshots mit `RIGHTS_NOT_CLEARED`. `transportError` ist `TIMEOUT`, `NETWORK`, `TLS` oder `CANCELLED` mit eigenem Fehlercode; HTTP 403/429/204 und fehlerhafte Struktur bleiben separat. URL-Quellen mit Kennwort-/Token-Parametern werden nicht angenommen.

Für reproduzierbare Regressionen:
```sh
python3 -m pip install -r requirements-dev.lock
python3 -m unittest discover -s tests -v
python3 -m price_module < examples/synthetic-price-query.json
```

Letztes CI: [70/70 Tests #41220291373](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220291373).
