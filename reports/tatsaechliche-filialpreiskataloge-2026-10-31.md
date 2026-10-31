# Tatsächliche Filialpreiskataloge: Live-Forschung (31.10.2026)

**Striktes Ziel:** Möglichst vollständige Produktlisten eines konkreten Supermarktes mit **aktuellen angezeigten Filial-Verkaufspreisen**, Mengen/Grundpreisen sowie Aktions- und App-Preisen. Historische Bon-Datensätze, UVP und Kaufland-Marktplatzpreise sind **kein Ersatz**.

## Verifizierte Ergebnisse

| Händler | Vollsortiment + aktuelle Preise | Filialgeltung | Status |
|---|---|---|---|
| **Lidl** | **Echte Produktkatalog-API erfolgreich:** 18 Hauptkategorien, Unterkategorien, paginierte Produktlisten mit Preisobjekten; Produktsuche und Produktdetail mit echten Verkaufspreisen | **Konkrete Filialkennung im URL-Pfad**: DE7434 Berlin hatte bei `q=Milch` 40 Treffer; DE7602 Hannover 8. Derselbe Barcode-Artikel im Berliner Markt 0,85 €; im anderen Markt HTTP 204 (nicht im API-Datensatz) | **Stärkster konkreter Kandidat.** Filialpreiskatalog nachgewiesen, vollständige Abarbeitung sämtlicher Kategorien und Bedingungen für dauerhafte Nutzung noch offen |
| **ALDI Nord** | In zwei amtlichen Sortimentkategorien 82/82 Artikel mit `currentPrice.priceValue`, Packung, Grundpreis aus öffentlich eingebettetem Algolia-JSON | Kettenweites Sortiments-JSON, kein geprüfter individueller Filial-Preisfilter | Funktionierender kategorieweiser aktueller Preiskatalog; volle Ketten- und Filialabdeckung unbewiesen |
| **PENNY** | Bisher nur 193 bepreiste Angebotsobjekte aus 12 Kategorien, nicht alle regulären Produkte | Offizielle Verkaufsregion aus Marktverzeichnis | Gesamtpreis-Katalog nicht bestätigt; Scan&Go ist artikelweiser Zugriff, kein enumerierbarer öffentlicher Feed |
| **Kaufland** | Bisher 511 gültige Werbeartikel in gewählter Filiale; keine vollständigen Regalpreislisten bestätigt | Konkrete `klNr`-Filialliste mit Datumsfenstern | Gesamtpreis-Katalog offen; Marktplatz-/Seller-API nicht mit Filialregalpreisen verwechseln |
| **EDEKA** | EDEKA-Marktaktionen als JSON zuvor live verifiziert, aber nicht vollständige Normalpreise | Markt-ID/national-Fallback unterscheidbar | Ohne ausdrückliche Zustimmung kein automatischer EDEKA.de-Contentabruf; keine vollständige aktuelle Filialpreisquelle bestätigt |
| **Netto Marken-Discount** | Offizieller KW45-Filialprospekt als textlesbare PDF getestet; keine sichere Zuordnung sämtlicher Produktpreise | Eindeutige Filialprospekt-URL zu `stores_id` | Vollsortiment-Preisdaten nicht bestätigt; Netto Plus Preisscanner ist nur artikelweise Funktion |

## Lidl – konkrete erfolgreiche Live-Tests

Das zuvor beobachtete **HTTP 400** bei der direkten Lidl-Katalog-API wurde erklärt: Die API erwartet `Accept-Language: de`, nicht `de-DE`. Es wurde **keine Authentifizierung, kein Schutzmechanismus und keine technische Zugangssperre umgangen**. Mit den regulären, dokumentierten App-Kompatibilitätsheadern:

`Accept: application/json`  
`Accept-Language: de`  
`X-Client-Version: 17.0.5`  
`X-Client-Platform: android`

funktionieren normale GET-Aufrufe auf `https://product-catalog.lidlplus.com/api/app/v1/DE/store/DE7434`:

- `/categories` → HTTP 200, **18 Hauptkategorien**; darunter Gemüse, Fleisch, Fisch, Milchprodukte, Backwaren, Grundnahrungsmittel, Tiefkühlkost, Getränke usw.
- `/categories/1003/products?skip=0&limit=30&date=2026-10-31` → HTTP 200, `totalProducts: 29`, **29 von 29 bepreiste Fischprodukte** (zweiter Test mit `limit=30`), die gesamte vom API gemeldete Kategorie in einer Anfrage; Preisfelder `price.price`, `priceWithoutDeposit`, `oldPrice`, `discount`, `lidlPlusOffer`, Packungs- und Grundpreisannotationen.
- `/search?q=Milch&date=2026-10-31` → HTTP 200, 40 Produktdatensätze für Berlin (DE7434); 8 für Hannover (DE7602). In der Berliner Liste z. B. MILBONA fettarme Milch **0,85 €**, BIOLAND fettarme Milch **1,25 €**, HEMME Vollmilch **1,59 €**. Das ist ein **aktueller angezeigter Filialkatalogpreis**, nicht automatisch historischer Normalpreis.
- `/products/8824326891371_DE?date=2026-10-31` → Berlin HTTP 200 mit Produkt, **0,85 €**, Zutaten, Allergenen, Nährwerten und Warenstatus. Derselbe Produkt-ID-Aufruf für Hannover → HTTP 204, **kein Produktdatensatz**.

**Belege:** [Schema, Kategorien und tatsächliche Preise](https://github.com/ecora2003-max/Try/actions/runs/41187206333) · [Eine vollständige bepreiste Kategorie 29/29](https://github.com/ecora2003-max/Try/actions/runs/41187483105) · [Product-ID in zwei Märkten](https://github.com/ecora2003-max/Try/actions/runs/41187388717) · [Fehlerursache Sprachheader](https://github.com/ecora2003-max/Try/actions/runs/41187079242) · [GitHub-Offline-Tests erfolgreich](https://github.com/ecora2003-max/Try/actions/runs/41187280765).

**Implementiert:** [`catalogues/lidl.py`](../catalogues/lidl.py) normalisiert die echten Such- und Kategorien-Produktobjekte, erfasst `price`, Pfand, `oldPrice`, Rabatt-/Lidl-Plus-Indikatoren und `store_key`. Fehlende Preise und unvollständige Pagination werden nicht fälschlich als vollständiger, gültiger Filialpreiskatalog gemeldet. [Vertragstests](../tests/test_lidl_catalogue.py).

**Nicht bewiesen:** Vollständige Abarbeitung aller Kategorien inklusive Unterkategorien und Pagination, Preise aller ~Filialartikel, Store-Genauigkeit vs. Kassenbon für Ausnahmen, Aktualitätsintervall sowie Recht zur kontinuierlichen systematischen Übernahme. Ein GET mit HTTP 200 ist **keine Nutzungslizenz**. Es ist dennoch nun **eine nachweislich funktionierende, reale Filialpreiskatalog-API und nicht bloß eine Prospektschnittstelle**.

## ALDI Nord

[Live-Kategorienparser](https://github.com/ecora2003-max/Try/actions/runs/41186298754): erste Kategorie 50/50 Artikel mit angezeigtem Preis, zweite Kategorie 32/32, jeweils `nbPages=1`; IDs, Mengen und Grundpreise vorhanden. Allgemeine `sortiment.html`-Indexseite liefert keine unmittelbar aus statischem HTML ableitbaren Produktkategorie-Links ([Test](https://github.com/ecora2003-max/Try/actions/runs/41187051287)). Die inoffizielle kostenpflichtige [Parse-API](https://parse.bot/marketplace/397bcd36-69f3-489f-a98d-49e56e4a80a7/aldi-de-api) dokumentiert ebenfalls Produktsuche und Kategoriepreise, ersetzt aber keine eigene geprüfte gratis-Quelle.

## Kritische Unterscheidung

- **Filialbezogen angezeigter aktueller Preis:** Lidl inzwischen per realem Produktdetail getestet.
- **Nachgewiesener früherer regulärer Kassenpreis:** nur mit geeigneter eigener Preisverlaufskette; `oldPrice` auf dem Produktobjekt reicht nicht als Beweis.
- **Angebotspreis:** kann bereits als aktueller Produktpreis angezeigt werden; `oldPrice` und `discount` getrennt halten. Gutschein- und Lidl-Plus-Bedingungen ebenfalls getrennt halten.
- **Vollständige Abdeckung:** erst wenn jeder Kategoriebaum bis zum Ende paginiert und anhand der vom Händler gemeldeten `totalProducts` geprüft wurde.
- **Nutzungsrechte:** gesondert prüfen. Insbesondere EDEKA.de untersagt automatisierte Datennutzung ohne vorherige Erlaubnis.
- **Kaufland:** `kaufland.de` ist ein Marktplatz und liefert nicht automatisch Preise von Kaufland-Supermarktregalen.

**Alle Recherche- und Teständerungen ausschließlich im Repository `Try`. Keine Änderungen in `Ernaerungsgedaechnis`.**
