# Vollständigkeit und Aktualität der Supermarkt-Preisdaten
**Prüfzeitpunkt:** 31.10.2026, ca. 11:54–11:59 UTC (12:54–12:59 Uhr Berlin)  
**Prüfgegenstand:** Die tatsächlich verfügbaren Preisdaten der bereits ermittelten APIs, ohne weitere Fragestellungen.  
**Schreibziel:** ausschließlich `ecora2003-max/Try`; `Ernaerungsgedaechnis` nicht verändert.

## Prüfung und Ergebnisübersicht

| Händler / Datenquelle | Nachweis innerhalb der API | Preisfeld-Abdeckung | Tatsächliche Sortiments-Vollständigkeit | Aktualitätsnachweis |
|---|---|---|---|---|
| **Lidl**, Filiale **DE7434** | 85 Kategorie-Knoten, davon 16 Verzweigungen und **69 vollständig paginierte Blattkategorien**; Summe der `totalProducts` über alle Blätter **2.005**, tatsächlich **2.005 Einträge** gelesen | **2.005 / 2.005** mit numerischem aktuellen Preis; **0** unbepreiste Einträge, keine Duplikate **innerhalb einzelner Blätter** | **Vollständig relativ zum von dieser API am Stichtag veröffentlichten Kategoriebaum**. Gleichheit mit sämtlichen realen Kassenartikeln **unbekannt**; Kategorien können gleiche Produkte enthalten, globale Unique-Zahl nicht ermittelt. | Live-Daten für `date=2026-10-31`; erste Seite bei erneutem Abruf unverändert. Dasselbe Blatt mit `date=2026-10-30` lieferte `totalProducts=0`: **kein verlässlicher historischer Preisabruf** belegt. Nur HTTP-`Date`, keine originäre Preis-Zeitmarke. |
| **ALDI Nord**, zwei Kategorien | Kategorien hatten `nbHits=50` und `nbHits=32`, beide `nbPages=1`; tatsächlich **82 unterschiedliche Produkte innerhalb der jeweiligen Kategorien** zurückgegeben | **82 / 82** mit numerischem aktuellem Preis | **Vollständig für exakt diese zwei Kategorien**, nicht das gesamte Sortiment oder eine konkrete Filiale | Erste Kategorie bei Wiederholung identisch. HTTP-Cache `max-age=600, stale-while-revalidate=86400`: Antwort darf auch nach Ende der 10-Minuten-Frischefrist noch als veraltet geliefert werden. Kein Nachweis des tatsächlichen Zeitpunkts einer Preisaktualisierung. |
| **REWE stationär**, `wwIdent=840174` und `831002` | Drei Suchbegriffe × zwei Filialen, **6 Antworten mit je 12 Artikeln**; jeweils 12 unterschiedliche IDs in jeder Antwort | **72 / 72** mit `pricing.current` und `pricing.regular` in Cent und numerischem `refund` | **Nicht nachgewiesen**. Ein Versuch mit `limit=50` und ein Versuch mit `offset=12` ergaben jeweils **dieselben 12 Treffer** wie ohne Parameter. API hat in diesem Test keine nachgewiesene nutzbare Pagination oder Gesamtanzahl. | Same-query-Wiederholung nach Sekunden unverändert. Server nennt aktuelles HTTP-`Date`, aber weder Preis-`updatedAt` noch `Last-Modified`/Cache-Alter. Tatsächliches Änderungsintervall unbekannt. |
| **ALDI Süd**, `servicePoint=B384`, `walk-in` | Für `q=` meldete API bei `limit=12` und `limit=60` stets **`totalCount=3538`**. 12/12 auf einer Seite, anschließend 60/60 der ersten 60er-Seite sowie **59/60** bei `offset=60` | **12/12**, **60/60** und **59/59** der drei erfolgreich getesteten Einzelantworten mit `amountRelevant` in Cent | **Unbestätigt**. Die API weist einen paginierten Gesamtkatalog aus, aber umfassende Seitenläufe scheiterten bereits beim ersten Request mehrfach mit **HTTP 403** (GitHub Actions). Die 59er-Rückgabe auf einer 60er-Seite verlangt zudem Prüfung auf ausgelassene Produkte und Lücken. | Ca. **51 Minuten** nach einem früheren Test noch `totalCount=3538`. HTTP `Cache-Control: public, max-age=300` (5 Minuten). Das beweist **nicht**, dass die Preisdaten alle fünf Minuten aktualisiert werden. Keine produktspezifische Änderungszeit. |

## REWE: Filialgenauigkeit und Grenzen der Suche

Direkter [Testlauf](https://github.com/ecora2003-max/Try/actions/runs/41198776617), Ergebnisartefakt `price-data-quality-rewe`:

- `Haferflocken`: 11 gemeinsame Produkte, **5** davon mit unterschiedlichen Filialpreisen.
- `Milch`: 10 gemeinsame Produkte, **4** davon mit unterschiedlichen Filialpreisen.
- `Reis`: 8 gemeinsame Produkte, **0** davon mit Preisunterschied.
- Alle 72 Antwortpositionen der sechs Suchanfragen mit aktuellen und regulären Preisen. Die 72 enthalten Überschneidungen zwischen Filialen; sie sind **keine 72 eindeutig verschiedenen Ladenartikel**.
- `limit=50` änderte die Trefferanzahl **nicht**; `offset=12` ergab **dieselben 12 Artikel und Preise**. Damit ist mit diesem Interface **kein vollständiger Artikelkatalog** nachgewiesen.

## Lidl: relevante Vollständigkeitsgrenze

[Erfolgreicher 91-GET-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41198776617), Artefakt `price-data-quality-lidl`:
- Gesamte von der API exponierte Navigation rekursiv durchlaufen: **85 Knoten**, **69 Blätter**, **69/69** Blätter vollständig bis `totalProducts` paginiert.
- **2.005/2.005** Preisdatenfelder erfolgreich gelesen, **keine unbepreisten Datensätze**.
- Dies ist eine starke **API-interne Abdeckungsprüfung**. Es gibt **keinen unabhängigen Nachweis**, dass die API jeden real vorrätigen Artikel der Filiale einschließt. Die 2.005 sind **Kategorieeinträge**, nicht nachgewiesen 2.005 verschiedene SKUs.
- Ein Test von `date=2026-10-30` für ein Blatt ergab 0 Produkte, während `date=2026-10-31` 93 Produkte ergab; das belegt allein Datumsabhängigkeit, **nicht** tägliche Preisaktualisierung.

## ALDI Nord: begrenzte Vollständigkeit, mögliche Cache-Verzögerung

[Erfolgreicher Prüflauf](https://github.com/ecora2003-max/Try/actions/runs/41198776617), Artefakt `price-data-quality-aldi_nord`:

- 50/50 + 32/32 in den beiden Milchkategorien; **82/82** aktuell angezeigte Preiswerte, **0 fehlende**.
- Im ersten Kategorietest blieb Produkt-ID/Preis-Fingerprint beim Wiederholungsabruf unverändert.
- Cache-Anweisung wörtlich `public, max-age=600, stale-while-revalidate=86400`. **Die mögliche Ausgabe von bis zu 24 h länger veralteten Cache-Inhalten** ist eine Cache-Policy-Beobachtung, kein Nachweis, dass gerade Preise tatsächlich 24 Stunden alt sind.

## ALDI Süd: robuste Einordnung der gescheiterten Vollabfrage

- [Erfolgreiche Seiten-Diagnose](https://github.com/ecora2003-max/Try/actions/runs/41198868513): eine 12er-Seite mit **12** bepreisten Produkten, eine 60er-Seite mit **60**, die zweite 60er-Seite (`offset=60`) mit **59**; `meta.pagination.totalCount=3538` jeweils unverändert, HTTP 200.
- Drei Versuche, denselben API-Katalog in einem längeren Durchlauf vollständig zu paginieren, erhielten jeweils bereits bei der **ersten Anfrage HTTP 403**; in diesen Läufen wurden **keine Katalogprodukte gelesen**. Daher gibt es **keinen empirisch vollständig eingelesenen ALDI-Süd-Katalog**.
- `max-age=300` ist der Cache-Frischehorizont der erfolgreichen Antwort (5 Minuten), **nicht** die bewiesene Updatefrequenz der Produktpreise.
- **Keine Hochrechnung auf 100 % Abdeckung** aus den erfolgreich geprüften 12-, 60- und 59er-Seiten zulässig.

## Was „aktuell“ empirisch bedeutet

1. **Abrufaktuell:** Das jeweilige HTTP-Ergebnis wurde am 31.10.2026 direkt vom Anbieter-Endpunkt erhalten; Zeitstempel des Abrufs und teils Server-`Date` sind dokumentiert. **Bei allen vier Händlern nachgewiesen** für die angegebenen Proben.
2. **Preisänderungsaktuell:** Es ist nachgewiesen, dass eine Preisänderung innerhalb einer bestimmten Zeit (z. B. Minuten) in der API erscheint. **Bei keinem Händler nachgewiesen**; dafür wären bekannte Preisänderungsereignisse samt wiederholtem Abgleich nötig.
3. **Kassenaktuell:** Es ist nachgewiesen, dass der API-Preis zu diesem Zeitpunkt dem wirklichen Kassenpreis entspricht. **Bei keinem Händler nachgewiesen**, da keine Kassenbon-/Regalpreis-Kontrollmessung in diesem Auftrag vorliegt.

## Technische Nachweise

- [Prüfcode ALDI Süd](../tools/check_price_completeness_aldi_sued.py)
- [Prüfcode REWE](../tools/check_price_completeness_rewe.py)
- [Prüfcode Lidl](../tools/check_price_completeness_lidl.py)
- [Prüfcode ALDI Nord](../tools/check_price_completeness_aldi_nord.py)
- [Sammelworkflow](../.github/workflows/price-completeness-freshness.yml)
- [ALDI-Süd-Diagnostik](../tools/check_aldi_sued_pagination_diagnostic.py)

**Nicht geprüft:** Die anderen Händler EDEKA, Netto, Kaufland und PENNY haben bislang keinen vergleichbar zugänglichen, verifizierten Normalpreis-Vollkatalog. Ohne solche Datengrundlage sind positive Aussagen zur Katalogvollständigkeit oder Updatefrequenz nicht möglich.

Keine Schreibänderungen an Ernährungsgedächtnis, Google Sheets oder anderen Repositories.
