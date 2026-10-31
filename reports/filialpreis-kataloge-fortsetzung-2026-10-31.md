# Fortsetzung: tatsächliche Filialpreiskataloge – neue Untersuchungen, 31.10.2026

**Klarstellung:** Nur echte aktuelle Filialpreise des möglichst gesamten Sortiments einschließlich aktueller Rabatte sind als Lösungsziel akzeptabel. Produktstammdaten, UVP, externe historische Preisbeobachtungen und reine Wochenaktionslisten gelten nicht als Vollpreiskatalog. Kein Wechsel auf kostenpflichtige APIs.

**Sicherheits- und Bearbeitungsgrenze:** Alle Änderungen wurden ausschließlich im Testrepository `Try` durchgeführt. `Ernaerungsgedaechnis` wurde nicht geändert. Keine Händler-Anmeldedaten aus Dritt-Repositories übernommen und keine Sperren umgangen.

## Neu erfolgreiche Tests

### 1. Lidl: Unterkategorien sind ebenfalls über eine konkrete Filialkennung bepreist abrufbar

[GitHub Actions: Lidl nested category price](https://github.com/ecora2003-max/Try/actions/runs/41188018700)

- `GET https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434/categories/1004/categories` mit `Accept-Language: de` → HTTP 200, **sechs Milchprodukt-Unterkategorien** (Milch & Sahne, Joghurt, Käse, Butter, Eier, Nachtisch).
- Für die ausgewählte Unterkategorie Milch & Sahne liefert `.../categories/1004/categories/1001/products?skip=0&limit=10&date=2026-10-31` → HTTP 200, **27 gemeldete Produkte, zehn von zehn in der Stichprobe mit Preis** (z. B. Crème fraîche 1,09 €).
- Bereits zuvor: eine komplette Kategorie Fisch & Meeresfrüchte **29/29** Produkte mit aktuellen Preisfeldern sowie differierende Produktsuche in Berlin und Hannover. Deshalb ist jetzt **auch die mehrstufige Kategoriestruktur** nachgewiesen, nicht nur ein einfacher Prospekt.
- **Noch offen:** sämtliche 18 Hauptkategorien und alle Untergruppen auf Vollständigkeit einschließlich Nicht-Lebensmitteln prüfen; Ergebnisse mit tatsächlichen Kassenpreisen verifizieren, Rabattbedingungen korrekt unterscheiden, rechtlich zulässige Wiederverwendung klären.

### 2. ALDI Nord: offizieller Navigationsbaum mit 27 bekannten Produkt- und Themenrouten

[GitHub Actions: ALDI navigation taxonomy](https://github.com/ecora2003-max/Try/actions/runs/41188129757)

- Die erste naive Suche nach Kategorien im statischen HTML verfehlte die Routen. Der anschließende Test im Next.js-`__NEXT_DATA__`-Baum unter `page.header.sideDrawerNavigation` fand **27 offizielle URLs** zu Produktbereichen und Themen.
- Darunter Milchprodukte, Fleisch/Wurst, Fisch/Meeresfrüchte, Obst/Gemüse, Backwaren, Vorräte, Getränke, Haushalt, vegane Produkte.
- **Achtung:** Nicht alle 27 Einträge sind echte unterste Produktkategorien; darunter auch Themen wie Marken, Bio, Weihnachten und Preis-Highlights. Ein vollständiger, überschneidungsfreier Katalogbaum ist deshalb **noch nicht nachgewiesen**.
- Bestätigte Preise bleiben die beiden Kategorien **50/50** und **32/32** Produktdatensätze mit `currentPrice.priceValue`. Eine exakte Produkt-ID-Zusammenführung mit den 276 Folgewoche-Aktionsobjekten ergab in diesen zwei Testkategorien **0 Überschneidungen**. Das beweist weder Unmöglichkeit noch einen korrekten Vor-Aktions-Preis.

### 3. PENNY: tatsächliche Einzelprodukt-Sortimentsseite hat keine Regalpreisfelder

[GitHub Actions: public non-offer price check](https://github.com/ecora2003-max/Try/actions/runs/41188175061)

- `https://www.penny.de/sortiment/` HTTP 200, **20 interne Produktsortiment-Links** im untersuchten HTML.
- Direkte öffentliche Produktseite `/sortiment/food-for-future/fuer-die-schnelle-kueche/food-for-future-reis-nuggets-vegan`: **0 Preisindikatoren**, 0 Preis-JSON-LD-Einträge und 0 dargestellte EUR-Werte im abgerufenen HTML.
- Die Einzelproduktseiten liefern hier also Produktstammdaten/Marketing, **keinen tatsächlichen aktuellen Kassenpreis**. Die bekannte `/.rest/offers`-Schnittstelle bleibt lediglich ein regionaler Aktionskatalog.

### 4. Kaufland: öffentliche Sortimentseite enthält keinen erkennbaren Normalpreis-Katalog

[GitHub Actions: public non-offer price check](https://github.com/ecora2003-max/Try/actions/runs/41188175061)

- `https://filiale.kaufland.de/sortiment.html` HTTP 200, ca. 200 kB HTML; **0 Product-JSON-LD-Objekte**, keine regulären Preisfelder und keine `data-product-id`-Einträge.
- Unabhängige Entwicklerprojekte **KaufiAlert** und **EvickaStudio/kaufland-discounts** nutzen `app.kaufland.net/data/api/v5|v7/offers/{storeId}` und `/api/v4/stores` für **filialbezogene Werbeartikel**. Diese Abfragen liefern nicht das komplette Regalangebot.
- Die Community-Codebeispiele enthalten eingebettete App-Basic-Authentifizierung. **Diese Credentials wurden nicht übernommen, und die geschützte API wurde nicht mit fremden Kennungen abgefragt.**
- Die separate `sellerapi.kaufland.com`-Produktsuche und Assortment-Insights beziehen sich nach offizieller Dokumentation auf den **Kaufland-Marktplatz (Buy-Box-Preise)** und **nicht** auf den Filialkassenpreis.

### 5. Netto Marken-Discount: erneute Vollpreisprüfung bleibt offen

- Öffentliche Prospekt- und Filial-Produktlistenseiten sind keine belegten Normalpreiskataloge. Filialproduktseiten werden im GitHub-Runner blockiert; der Prospekt-Workflow ergibt filialbezogene PDF-Werbeangebote, **nicht das vollständige Sortiment**.
- `netto-online.de` liefert aus dem verwendeten GitHub-Runner bei `robots.txt` keine verlässliche Nutzungserlaubnis; der automatisierte Einzeltest für die Startseite wurde deshalb nicht fortgesetzt.
- Die offizielle Netto-Plus-App dokumentiert Scan&Go mit korrekten Filialpreisen bei aktivem Standort, aber **keinen öffentlich auflistbaren Preiskatalog**. Datenschutz/Nutzung und erforderliche Sitzung/Marktzutritt sind gesondert zu beachten.

### 6. EDEKA: Filialspezifische Shoppreise existieren, aber keine frei nutzbare Verbund-API bestätigt

- Drittanbieter dokumentieren teilnehmende Marktshops auf `edeka.shop` mit Preis- und Grundpreisangaben und separaten `edeka.de/sortiment`-Produktstammdaten.
- Nicht automatisch alle EDEKA-Märkte beteiligt, teils Online-/Lieferpreise statt Kassenpreisen.
- **Keine erneuten automatisierten EDEKA.de-Abfragen:** Die für EDEKA.de ermittelten Nutzungsbedingungen untersagen automatisierte Übernahme ohne schriftliche Zustimmung. Technisch erfolgreiche Markt-Angebots-GETs von früher sind keine Lizenz.

## Ergebnis / Implementierungsentscheidung

| Händler | Ein aktuell angezeigter Katalogpreis technisch nachgewiesen? | Filialfilter des *Produktkatalogs*? | Vollständige Gesamtdeckung bestätigt? |
|---|---|---|---|
| Lidl | **Ja** | **Ja** | Nein; komplette Einzelkategorie und Unterkategorie-Stichprobe |
| ALDI Nord | **Ja** | Nicht nachgewiesen | Nein; zwei Kategorien |
| PENNY | **Nein** (nur Aktionen) | Nicht nachgewiesen | Nein |
| Kaufland | **Nein** (nur Aktionen) | Nicht nachgewiesen | Nein |
| EDEKA | Marktshop-Preise als Drittanbieterhinweis, nicht für Gesamtverbund verifiziert | Je teilnehmendem Shop möglich, nicht für alle | Nein |
| Netto Marken-Discount | **Nein** (nur Aktionen / Prospekt) | Nicht nachgewiesen | Nein |

**Wichtig:** Ein Erfolg bei einer ungeschützten GET-Anfrage belegt technische Erreichbarkeit, nicht eine vertragliche Freigabe für regelmäßigen Download, Spiegelung oder öffentliche Anzeige fremder Preisdaten. Auch bei Lidl/ALDI Nord ist die Freigabe zu klären.

## Für die nächste Entwicklungsphase

- Lidl: vollständigen Kategoriebaum/Seitenumfang **begrenzter Tests** und Preis-Rabatt-Modell sauber validieren; keine massenhaften Abrufe, bevor Nutzungsrechte geklärt sind.
- ALDI Nord: echte Produktkategorien von Marketing-Routen trennen; mögliche Filial-Preisvariation belegen, bevor „Marktpreis“ ausgegeben wird.
- PENNY, Kaufland, Netto: ein konkreter Filialpreis-Katalog kann nicht durch bloßes Umbenennen eines Aktionsfeeds rekonstruiert werden; erforderlich sind ein nachweislich freigegebener API-/Preisexport oder ein Händlervertrag.
- EDEKA: ausdrücklich autorisierter Zugang zu Marktshop-/POS-Preislisten.
