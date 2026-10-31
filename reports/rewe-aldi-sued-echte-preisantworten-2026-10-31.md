# REWE und ALDI Süd: erster eigener Live-Preisabruf mit öffentlich lesbaren Endpunkten
**Ausführung:** 31.10.2026, 11:00 UTC · **Repository:** ausschließlich `Try`.

## Nachweis (neuer eigener GitHub-Actions-Lauf)

[Workflow 41195015622 – komplett erfolgreich](https://github.com/ecora2003-max/Try/actions/runs/41195015622) · [einmaliges Prüfsystem](../tools/one_shot_public_price_probe.py) · JSON-Artefakt `one-shot-price-feasibility` (Retention 7 Tage).

Maximal **eine einzige Produktsuchanfrage pro Händler** (kein Crawling, keine Paginierung, keine Zugangsdaten, keine Zertifikate, kein Fingerprinting oder Umgehen einer Schutzmaßnahme). Vor jeder Anfrage wurde `robots.txt` geprüft; verbotene/unklare Routen würden übersprungen. Ergebnisse wurden auf Schema-, Zähl- und wenige Preisfelder reduziert.

| Quelle | Prüfung | Ergebnis |
|---|---|---|
| **REWE stationär** | `GET https://www.rewe.de/api/stationary-product-search/products?query=Haferflocken&wwIdent=840174` | **HTTP 200, JSON, 12 Produkte**, erste fünf Beispiele enthalten `pricing.current` = 189, 249, 199, 229, 299 Cent; für diese fünf `pricing.regular` identisch; `pricing.refund=0`. Felder `products`, `state`, `term`. |
| **ALDI Süd** | `GET https://api.aldi-sued.de/v3/product-search?q=Haferflocken&servicePoint=B384&serviceType=walk-in&limit=12&offset=0` | **HTTP 200, JSON, 1 Produkt**, `price.amount=99`, `amountRelevant=99` Cent, `currencyCode=EUR`. Root-Felder `data`, `meta`. |

**Bedeutung:** Das sind erstmals **eigene echte Live-Produktpreisantworten** zusätzlich zu den vorherigen Lidl-/ALDI-Nord-Ergebnissen. Der noch ältere API-Fund aus Github und der App-Code allein hätten diese Aussage nicht gerechtfertigt. Quellen: [chukfinley/bismark](https://github.com/chukfinley/bismark) (REWE) und [ByteSizedMarius/aldiscount](https://github.com/ByteSizedMarius/aldiscount) (ALDI Süd). Die tatsächlich funktionierenden API-Adressen wurden mit den Quellen und der vorherigen eigenen APK-Dekompilierung abgeglichen.

**Unsicherheiten:** Der REWE-Test verwendet genau einen `wwIdent`, der ALDI-Test genau einen `servicePoint` und ein Suchwort. `12` bzw. `1` sind **Suchtrefferzahlen**, nicht Gesamtsortiment, nicht sämtliche Haferflocken des Marktes. Der Nachweis eines `wwIdent`-Parameters belegt noch keine tatsächliche Variabilität zwischen Märkten. Keine unabhängige Kassenbon-Validierung und keine Dokumentation einer erlaubten kontinuierlichen Datenübernahme. Die Funktionsfähigkeit im GitHub-Actions-Runner beweist keine identischen Zugriffsbedingungen in einer Android-App.

### robots-Prüfung und Nutzungsrecht

- `www.rewe.de/robots.txt` wurde gelesen und erlaubte den konkreten Suchpfad für den Prüf-User-Agent.
- Auf `api.aldi-sued.de` lieferte `robots.txt` HTTP 404; das Standardsignal wurde als nicht disallowed interpretiert. Die Website `www.aldi-sued.de` hat eigenständige Regeln, die nicht automatisch die API-Subdomain abdecken.
- **robots-Status ist keine urheber-/datenbankrechtliche Lizenz, keine API-Partnerschaft und keine Garantie künftigen Zugriffs.** Vertrags- und Nutzungsbedingungen gesondert prüfen. Insbesondere kein unbegrenzter Abruf im produktiven System, bevor die Berechtigung geklärt ist.

## Als Referenzmodell in Try umgesetzt

[adapters/stationary_price_catalogues.py](../adapters/stationary_price_catalogues.py) interpretiert **ausschließlich bereits gelieferte JSON-Objekte** ohne Netzwerkanfrage:
- REWE: `pricing.current` und `regular` in Cent, `refund` (Pfand), Rabatt nur bei explizitem numerischem Vergleich.
- ALDI Süd: `price.amountRelevant` bevorzugt, danach `amount`, `bottleDeposit`, Währung, `wasPriceDisplay` getrennt.
- Store-ID in jedem Eintrag explizit; fehlende Preise und fehlende Pfandbeträge bleiben **unbekannt und werden nicht als Null interpretiert**.
- REWE-Katalogvollständigkeit bleibt `None`, wenn keine Gesamtzahl aus der Antwort bekannt ist. ALDI-Seitenzählung vergleicht mit `meta.pagination.totalCount` nur für die erhaltene Antwortseite.
- Synthetic-Contract-Tests in [tests/test_stationary_price_catalogues.py](../tests/test_stationary_price_catalogues.py), [Github Actions PASS](https://github.com/ecora2003-max/Try/actions/runs/41195124182).

**Keine Änderungen an `ecora2003-max/Ernaerungsgedaechnis`.** Keine tatsächlichen Vorratsbestände, Ernährungstagebücher oder Käufe erfasst/geändert.

## Zusätzlicher entscheidender Live-Beleg: echte Filialpreis-Unterschiede bei REWE

[Zweiter erfolgreicher GitHub-Actions-Lauf 41195181867](https://github.com/ecora2003-max/Try/actions/runs/41195181867) · [Prüfcode](../tools/rewe_two_store_scope_probe.py) · Artefakt `rewe-two-stores-one-term`.

Am **31.10.2026 11:02:37 UTC** wurden genau **zwei** lesende Suchabfragen auf demselben REWE-Endpunkt `/api/stationary-product-search/products` für dasselbe Suchwort `Haferflocken` ausgeführt, jeweils mit unterschiedlichen `wwIdent`-Werten `840174` und `831002`, beide **HTTP 200**.

- Markt `840174`: **12** Suchtreffer; Markt `831002`: **12** Suchtreffer.
- **11 identische Produkt-IDs** in beiden Antworten, je **1 exklusiver Treffer**.
- Unter den **11 gemeinsamen Produkten waren 5 aktuell angezeigte Preise unterschiedlich**.
- Beispiele der jeweils gleichen Produkt-ID mit unterschiedlichen Centpreisen (Markt 840174 → Markt 831002): **0,95 € → 0,99 €**, **0,85 € → 0,99 €**, **2,29 € → 2,39 €**.
- Im Ergebnis wurden nur Aggregat- und Preisangaben gespeichert, keine Kunden- oder Login-Daten.

**Interpretation:** Damit ist durch einen eigenen aktuellen Test nachgewiesen, dass REWEs stationäre Suchschnittstelle **je `wwIdent` tatsächlich unterschiedliche Produktpreise und Treffer** liefern kann. Das ist stärker als bloß ein Filial-Parameter im Quellcode. Es bestätigt noch keine Vollständigkeit, Kassenbon-Gleichheit, Lizenz oder vertraglich erlaubte Dauernutzung.

## Zusätzlicher Live-Beleg: ALDI Süd meldet 3.538 Artikel im paginierten Suchkatalog

[Dritter erfolgreicher GitHub-Actions-Lauf 41195314409](https://github.com/ecora2003-max/Try/actions/runs/41195314409) · [Prüfcode](../tools/aldi_sued_catalogue_one_page.py) · Artefakt `aldi-single-catalogue-page`.

Am **31.10.2026 11:04:32 UTC** lieferte die bekannte ALDI-SÜD-Produktsuche für `servicePoint=B384`, `serviceType=walk-in`, **leeren Suchtext `q=`**, `limit=12`, `offset=0` und `currency=EUR`:

- **HTTP 200, JSON**
- `meta.pagination.totalCount = 3538` (**vom API-Server gemeldete Artikelgesamtzahl für diese Suche/Filialauswahl**)
- `meta.pagination.offset = 0`, `limit = 12`
- **12 Produkte auf erster Seite, alle 12 mit numerischem `price.amountRelevant` in Cent und Währung EUR**

**Entscheidend:** Damit ist ein **paginiert durchsuchbarer bepreister Sortimentskatalog** direkt und ohne Händlerlogin live bestätigt. Das demonstriert eine gute technische Möglichkeit, sämtliche vom Endpunkt gemeldeten Artikel abzurufen. **Nicht** nachgewiesen ist, dass alle 3.538 tatsächlich paginiert abrufbar sind, jeden realen Ladenartikel abbilden, die Kassenpreise korrekt sind oder eine komplette bzw. dauerhafte Datenextraktion erlaubt ist. Aus Rücksicht auf Zugriffsbelastung und Datenrechte wurden **nicht** 3.538 Artikel heruntergeladen, sondern nur die erste Seite mit 12 Exemplaren.
