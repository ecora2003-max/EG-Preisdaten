# EDEKA-Produkt- und Preisdaten: tatsächlicher Downloadstand – 31.10.2026

**Ablage:** `ecora2003-max/EG-Preisdaten`, identisches Repository mit dem zuvor als `Try` verwendeten Testrepository (Repository-ID 1440618134). Keine Änderung an `Ernaerungsgedaechnis`, `EG-Produktdaten` oder Google Sheets. Die GitHub-Ablage ist **öffentlich**.

## Was erfolgreich heruntergeladen und in GitHub zurückgelesen wurde

| Datei | Inhalt | Ergebnis |
|---|---|---|
| [`data/edeka/2026-10-31/offers_10003451_raw.json`](../data/edeka/2026-10-31/offers_10003451_raw.json) | Vollständige offizielle Angebots-API-Antwort für Markt-ID `10003451` (Berlin) | **256 von 256** gemeldeten Angeboten, **256** numerische Preise |
| [`data/edeka/2026-10-31/offer_products_10003451.json`](../data/edeka/2026-10-31/offer_products_10003451.json) | Normalisierte Artikelnamen, Angebots-IDs, Preise, Basispreis-Texte und Validität für Berlin | **256** Zeilen, ausdrücklich **nur Angebotsartikel** |
| [`data/edeka/2026-10-31/offers_913988_raw.json`](../data/edeka/2026-10-31/offers_913988_raw.json) | Vollständige offizielle Angebots-API-Antwort für Markt-ID `913988` (Hamburg) | **40 von 40** gemeldeten Angeboten, **40** numerische Preise |
| [`data/edeka/2026-10-31/offer_products_913988.json`](../data/edeka/2026-10-31/offer_products_913988.json) | Normalisierte Angebotsprodukte und Preise für Hamburg | **40** Zeilen |
| [`data/edeka/2026-10-31/product_page_subset.json`](../data/edeka/2026-10-31/product_page_subset.json) | Offizielle EDEKA-Produktseiten: Numerische Produktseiten-ID (als GTIN-Kandidat, nicht unabhängig anhand der Packung verifiziert), Produktname, Produkt-URL, unbekannter Preis | **240 unterschiedliche Produkte**; **kein** Normalpreis |
| [`data/edeka/2026-10-31/manifest.json`](../data/edeka/2026-10-31/manifest.json) | Quellen, Marktauswahl, Zählwerte, Zeitpunkte, SHA-256 der offiziellen Angebotsantworten | Erfasst |
| [`data/edeka/2026-10-31/product_page_subset_manifest.json`](../data/edeka/2026-10-31/product_page_subset_manifest.json) | Crawl-Grenzen, Fehler, eindeutige Produktzahl, Titelbereinigung | Erfasst |

**Übergreifend:** **296 Angebots-/Preispositionen** aus zwei Marktkatalogen, außerdem **240 separate Produktseiten-Einträge ohne Normalpreis**. Angebotsartikel zwischen den beiden Märkten können sich überschneiden. Kein pauschaler GTIN-Abgleich zwischen Angeboten und Produktstamm möglich.

### Qualität und Gültigkeit

- Die beiden Angebots-API-Antworten haben `national: false` und ihre Datensatzlänge stimmt genau mit `anzahl` überein. Das beweist **vollständige Abfrage innerhalb der beiden konkreten Angebots-API-Antworten**, nicht die Existenz einer vollständigen Liste aller EDEKA-Produkte.
- Der von der API veröffentlichte Zeitraum lautet `gueltig_von=2026-10-26T00:00:00Z` bis `gueltig_bis=2026-10-31T00:00:00Z`. **Bereits zum Download um 15:25 UTC lag dieses Enddatum in der Vergangenheit.** Kein heute gültiger Preis ohne unabhängige Klärung der Gültigkeitssemantik.
- Die Produktseiten haben keine numerischen regulären Preise im geprüften HTML; `price_eur` ist daher **null (= unbekannt, nicht 0)**.
- Die Produktdatei wurde nach GitHub-Rücklesung korrigiert: Ein allgemeiner Seitentitel war zunächst den 240 Namen vorangestellt. [Offline-Normalisierung](../tools/edeka_repair_product_titles.py), [erfolgreicher GitHub-Actions-Lauf](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41215636727), **240/240 korrigiert und verifiziert**.
- Der Produktseiten-Crawl folgte bei insgesamt **240 erfolgreichen Seitenaufrufen** den offiziellen internen Produktempfehlungslinks. Es gab **keine HTTP-Fehler**, aber **829 weitere verlinkte Seiten waren noch in der Queue**, bevor die bewusst begrenzte Obergrenze erreicht wurde. Es sind **nicht** sämtliche offiziellen EDEKA-Produkte.
- Die offizielle Sortimentsuche meldet zum Prüfzeitpunkt wechselnde Größenordnungen von **ca. 5.900–6.000** Produkten (u. a. 5.969, 5.996). Diese Zahlen sind **kein vollständiger Bestand aller Artikel sämtlicher EDEKA-Filialen**.
- Der offizielle Index `https://www.edeka.de/_sitemap.xml` sowie `https://www.edeka.de/sortiment/suche/` gaben aus dem GitHub-Actions-Runner **HTTP 403**, obwohl eine EDEKA-Produktdetailseite zugänglich war. Keine Sperre umgangen, keine vollständige Pagination technisch möglich gemacht.
- Das separate [EDEKA B2C API Gateway](https://b2c-gw.api.edeka/) verlangt einen Zugang durch EDEKA. **Keine Zugangsdaten/Partner-Endpunktverträge wurden im Gespräch oder in den verfügbaren Werkzeugsystemen vorgefunden.** Vom Nutzer behauptete Freigabe zum Download/GitHub-Speichern wurde zugrunde gelegt, **nicht unabhängig verifiziert**.

## Reproduzierbarkeit

- [Angebotsstruktur und erreichbare Marktangebote](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41214522585).
- [Angebotsdownload und tatsächlicher Commit](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41214770369); [Snapshot-Skript](../tools/edeka_authorized_market_snapshot.py).
- [Produktseitenstruktur](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41214904531) und [403 bei Sortimentsuch-Pagination](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41215007869).
- [240 öffentlich erreichbare Produktdetailseiten](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41215163056); [Crawl-Skript](../tools/edeka_product_linkgraph_snapshot.py).
- [Titelkorrektur und GitHub-Commit](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41215636727).

**Status:** `MARKET_OFFERS_SAVED_296`, `PRODUCT_PAGE_SUBSET_SAVED_240`, `COMPLETE_EDEKA_REGULAR_PRICE_CATALOG_NOT_ACCESSIBLE_WITH_CURRENT_ENDPOINTS`.

Für den vollständigen, marktbezogenen normalen Produkt-/Preiskatalog benötigt das System einen technisch nutzbaren autorisierten Datenexport oder den konkreten Partner-API-Endpunkt mit passenden Zugangsdaten. Die vorhandene öffentliche Wochenangebots-API stellt diesen nicht bereit.
