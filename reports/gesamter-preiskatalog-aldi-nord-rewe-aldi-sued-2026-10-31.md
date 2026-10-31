# Gesamter Preiskatalog erreichbar? ALDI Nord, REWE, ALDI Süd
**Live-Tests am 31. Oktober 2026, zwischen 12:11 und 12:20 UTC.**  
**Untersuchungsfrage ausschließlich:** Lassen sich alle aktuell vom Händler veröffentlichten Produkt- und Preisdatensätze abrufen, nicht nur einige Suchtreffer? Keine Prüfung anderer Themen.

## Kurzurteil

| Händler | Tatsächlicher Abruf | Gesichert vollständig? | Präzises Urteil |
|---|---|---|---|
| **ALDI Nord** | Offizielle Sitemap mit 5.218–5.222 URLs; **198** `/sortiment/`-Kategorie-/Landing-Pfade; **174** Produktlisten; daraus **3.706** Listeneinträge, **1.781 verschiedene Produkt-IDs**. **3.698/3.706** Listeneinträge mit numerischem Preis. | **Nein, nicht gesichert** | Alle **174 tatsächlichen Produktlisten** lieferten je `nbPages=1` und ihre gesamten `nbHits`, aber 8 Preise fehlen. Die offizielle Sitemap listet zusätzlich **2.307 einzelne Produktseiten** unter `/produkt/`. Ohne überprüfte SKU-Zuordnung zu den 1.781 Listen-IDs ist die Vollständigkeit des Gesamtartikelstamms **nicht belegt**. |
| **REWE stationär** | Für `wwIdent=840174` pro Suchbegriff **12 Ergebnisse**, mit Preis. Zusätzliche Aufrufe mit `limit`, `offset`, `page`, `pageSize`, `size` und `from` ergeben weiterhin nur **die gleichen 12 Produkt-IDs**. Auch `page=999` liefert dieselben zwölf. | **Nein** | Aktuell nur **gezielte Produkt-/Textsuche mit Preis**. Kein getesteter Mechanismus für alle Produkt-IDs eines normalen stationären REWE-Marktes, kein nutzbarer Gesamtzähler. |
| **ALDI Süd** | `servicePoint=B384`/`walk-in`, REST `/v3/product-search`: **alle 59 Seiten mit `limit=60`** bis zum gemeldeten Ende abgerufen, **3.537 verschiedene Artikel mit Preis**; unabhängiger vollständiger Durchlauf mit **74 Seiten `limit=48`**, dabei **3.549 verschiedene Artikel mit Preis**. | **Nein, strenge Vollständigkeit nicht nachweisbar** | Der Endpunkt ist **systematisch seitenweise in großer Breite abrufbar**; alle 3.537 bzw. 3.549 zurückgegebenen Artikel waren bepreist. Das API-`totalCount` war in beiden Läufen konstant **3.538**; die Unterschiede bei den beiden Seitengrößen widerlegen, dass `totalCount` bisher ein verlässlicher exakter Produktzählwert ist. |

### Wichtige genaue Interpretation

- **ALDI Nord**: Die API liefert wirklich alle Listenpositionen **innerhalb der 174 geprüften Kategorie-Listings** (`nbHits` = Anzahl der Treffer; `nbPages=1`). Aber die 3.706 Listeneinträge sind wegen Kategorieüberschneidung **nur 1.781 einzigartige IDs**, und das offizielle URL-Inventar hat 2.307 Produktdetailseiten. Die Differenz ist ein ernstes Coverage-Signal, jedoch kein mathematischer Nachweis von genau 526 fehlenden Artikeln: `objectID` und Produktdetail-Slug-IDs müssen erst explizit abgeglichen werden.
- **REWE**: Aufrufe mit vermeintlichen Seitenparametern ließen manchmal unterschiedliche *Preis-Fingerprints* erscheinen, aber die **Menge aller zwölf Produkt-IDs blieb identisch**. Selbst `page=999` gab zwölf Artikel zurück. Der Verdacht einer funktionierenden Paginierung ist daher **widerlegt**. Der Online-Liefer-/Abholshop hat möglicherweise separate sortimentweite Kategorien, die sich technisch und hinsichtlich Preis-/Marktkontext vom stationären REWE-Preisendpunkt unterscheiden.
- **ALDI Süd**: Der 60er-Lauf lieferte an den Offsets **60, 120 und 3000** jeweils nur **59 statt 60** Produkte; trotzdem lieferte die letzte Seite `offset=3480` **60** Produkte. Der zweite Lauf mit 48er-Pages lieferte ebenfalls in drei mittleren Seiten **47 statt 48**, aber in der letzten Seite `offset=3504` **48 Produkte**. `offset` 3538, 3552, 3600 und 4000 ergaben jeweils **HTTP 400**. Ein auf `totalCount=3538` begrenzter Aufruf kann also produkt- und seitengrößenabhängig weniger oder mehr Datensätze als `totalCount` liefern; die letzte Seite wird nicht auf die Restanzahl abgeschnitten. Keine Duplikate innerhalb der einzelnen Durchläufe, alle gelieferten Artikel mit `price.amountRelevant`. Bislang **kein absolut vollständiger, konsistenter Artikelstamm**.
- Bei **allen drei** beziehen sich die Preise auf veröffentlichte Web-/API-Daten. Eine vollständige Übereinstimmung mit tatsächlich vorhandenen Regal-/Kassenartikeln einer spezifischen Filiale wurde nicht ermittelt.

## Konkrete Mess- und Code-Nachweise

1. **ALDI Nord**: [Vollständiger Sitemap-Kategoriescan](https://github.com/ecora2003-max/Try/actions/runs/41200008094), [Sitemap-URL-Strukturauswertung](https://github.com/ecora2003-max/Try/actions/runs/41200514284). Testcode: [Kategorie-Enumerator](../tools/full_catalogue_access_aldi_nord.py), [Sitemap-Struktur](../tools/aldi_nord_sitemap_structure.py).
2. **REWE**: [12 Such- und Parameterproben](https://github.com/ecora2003-max/Try/actions/runs/41200008094), [Kontrolltest mit wiederholten Seitenparametern und zwölf identischen Produkt-IDs](https://github.com/ecora2003-max/Try/actions/runs/41200163751). Testcode: [Katalogzugang](../tools/full_catalogue_access_rewe.py), [Kontrollvergleich](../tools/rewe_pagination_control_test.py).
3. **ALDI Süd**: [59×60-Seiten-Kataloglauf](https://github.com/ecora2003-max/Try/actions/runs/41200008094), [74×48-Seiten-Gegenprobe](https://github.com/ecora2003-max/Try/actions/runs/41200359479), [Grenzoffsets am Katalogende](https://github.com/ecora2003-max/Try/actions/runs/41200644160). Testcode: [60er Lauf](../tools/full_catalogue_access_aldi_sued.py), [48er Gegenprobe](../tools/full_catalogue_access_aldi_sued_48.py), [End-Offset-Test](../tools/aldi_sued_catalogue_end_probe.py).

Alle Messwerte wurden durch Github-Actions-GitHub-Runner tatsächlich erzeugt, nicht aus angenommenen API-Antworten konstruiert. Testartefakte werden nur sieben Tage gehalten; dieses Dokument sichert die wichtigsten Zahlen dauerhaft.

## Technisches Gesamtfazit

- **ALDI Süd: fast vollständiger und seitenweise zugänglicher großer bepreister API-Katalog.** Eine exakte 100%-Aussage ist wegen **3.537 / 3.549 unterschiedliche Artikel vs. gemeldete 3.538** nicht vertretbar. Eine erneute ID-Level-Reconciliation (stabile Sortierung, dynamische Unterschiede, Filtertyp) wäre erforderlich.
- **ALDI Nord: alle offiziell per Sitemap aufgefundenen 174 Produktlistenseiten lassen sich vollständig abrufen**, aber nicht jeder Eintrag trägt einen Preis, und der Abgleich zu 2.307 Produktdetail-URLs fehlt. Kein Nachweis, dass das *gesamte* Sortiment als bepreiste Menge erschlossen ist.
- **REWE: Der stationäre API-Endpunkt stellt derzeit nur abfragbare Teilmengen, keinen enumerierbaren Vollkatalog bereit.** Mehr Freitext-Suchwörter bedeuten nicht bewiesene Vollständigkeit.

**Repositorygrenze eingehalten:** Nur `ecora2003-max/Try` beschrieben; `Ernaerungsgedaechnis` unverändert.
