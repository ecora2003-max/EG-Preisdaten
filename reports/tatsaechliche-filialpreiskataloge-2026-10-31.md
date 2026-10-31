# Tatsächlicher Filialpreiskatalog statt Preis-Snapshots (31.10.2026)

## Verbindliches Ziel dieser Untersuchung

**Gesucht:** ein aktuell abrufbarer *Händler-Preiskatalog* des tatsächlichen Filialsortiments, mit einem verifizierten Verkaufspreis pro Produkt sowie ggf. gleichzeitig geltendem Angebotspreis. Nach Möglichkeit vollständige aktuelle Abdeckung und reale Filialzuordnung.

**Nicht ausreichend:** veraltete Bonpreise, offene Preisvergleichs-Datenbanken, nur Produktstammdaten, nur Prospektartikel, unverbindliche UVP, Marketplace-Preise, Shoppreise ohne Bezug zur Filiale oder ein Einzelbarcode-Scan ohne vollständige Katalogenumeration.

Alle historischen Tests in diesem Projekt erfolgten im Testrepository **Try**. Das gesonderte Android-Repository `Ernaerungsgedaechnis` wurde nicht verändert.

## Belastbare Quellen je Händler

| Händler | Unmittelbarer aktueller realer Preiskatalog | Direkte Zugriffslage | Bewertung |
|---|---|---|---|
| **ALDI Nord** | Offizielle Produktkategorien mit `currentPrice.priceValue` und Grundpreis | Zwei vollständige Kategorieseiten mit 50/50 und 32/32 Produkten live eingelesen; kein verifizierter Gesamtindex, Filialfilter oder ungekürzter Normalpreis | **Teilweise direkt nachgewiesen**; stärkster Kandidat für tatsächlich angezeigte aktuelle Preise |
| **Lidl** | Interner Preis-/Produktabruf für Scan&Go-teilnehmende Filialen ist dokumentiert; öffentliche Produktkatalog-API aus Drittprojekt | Acht Anfragen an `product-catalog.lidlplus.com` ergaben HTTP 400; Lidl-Plus-Offers-API liefert dagegen nur 78 Aktionen/65 normale Einzelsparpreise für DE7434 | **Kein vollständig abrufbarer Filialpreiskatalog nachgewiesen** |
| **PENNY** | PENNY Scan&Go im Markt, mit Einzelartikel-Preisanzeige; Preis kann laut Bedingungen abweichen | 12 Aktionskategorien und regionsgenaue Aktionen als JSON abrufbar, keine Normalpreis-Such-/Gesamtsortiments-API verifiziert | **Einzelartikel intern möglich, Massenkatalog nicht bestätigt** |
| **Kaufland** | Kaufland Scan / K-Scan erfasst Artikel und zeigt laufenden Einkaufsbetrag | Filialaktionen / `klNr`-Gültigkeit verifiziert; `kaufland.de` Marketplace ist kein verlässlicher Filialnormalpreiskatalog | **Kassenseitige Preise intern, Bulk-Preiskatalog nicht bestätigt** |
| **EDEKA** | Manche lokale Markthändler bieten `edeka.shop` mit filialspezifischen Preisen | Anbieterkatalog `edeka.de/sortiment` enthält keine durchgehend lokalen Preisfelder; nur Angebote via Markt-ID getestet; `edeka.shop` erfordert Auswahl tatsächlich teilnehmender Filialen | **Keine flächendeckende Schnittstelle; automatisierte Übernahme von EDEKA.de-Inhalten ohne Freigabe gestoppt** |
| **Netto Marken-Discount** | Netto Plus Scan&Go benötigt Ortung für Preise der tatsächlichen Filiale | Offizieller marktspezifischer PDF-Wochenprospekt funktioniert; Netto-Online-Shoppreise können ausdrücklich von Filialpreisen abweichen; direkte Filial-Produktseite 403 | **Interne Preisfunktion dokumentiert; Produktkatalog-API nicht bestätigt** |
| **ALDI Süd (zusätzlich)** | Open-Source-Client `ByteSizedMarius/aldiscount` dokumentiert unfiltrierte Produktsuche samt `price.amountRelevant`, Grundpreis, `wasPriceDisplay`, optional servicePoint | Ein echter schlichter GET auf `api.aldi-sued.de/v3/product-search` aus GitHub Actions ergab HTTP 403 | **Drittprojekt beschreibt korrektes Datenmodell, unser Zugriff derzeit blockiert** |

### Live-Testbelege

- [ALDI Nord: zwei aktuelle Sortimentskategorien und Preisparser – PASS](https://github.com/ecora2003-max/Try/actions/runs/41186298754)
- [ALDI Nord: direkte öffentliche Algolia-Suche nicht bestätigt](https://github.com/ecora2003-max/Try/actions/runs/41186627062)
- [Lidl: vollständiger Produktkatalog im direkten API-Versuch HTTP 400](https://github.com/ecora2003-max/Try/actions/runs/41185956743)
- [Lidl: nur echte filialbezogene Aktionspreise abgefragt – PASS](https://github.com/ecora2003-max/Try/actions/runs/41183799427)
- [PENNY: 12 Angebotskategorien, nicht gesamtes Sortiment](https://github.com/ecora2003-max/Try/actions/runs/41182962632)
- [Kaufland: Filiallisten von Werbeartikeln, nicht Vollsortiment](https://github.com/ecora2003-max/Try/actions/runs/41181939368)
- [Netto: filialbezogene PDF möglich, kein Normalpreiskatalog](https://github.com/ecora2003-max/Try/actions/runs/41184427978)
- [ALDI Süd: direkter Produktsuchversuch HTTP 403](https://github.com/ecora2003-max/Try/actions/runs/41186725467)

### Originalhersteller-Hinweise zu Scan&Go

- Lidl Plus Scan&Go: https://www.lidl.de/c/lidl-plus-scan-go/s10072875 – nur in teilnehmenden Filialen, Barcode-Scan, Check-in, aktuelle Daten werden synchronisiert; https://www.lidl.de/c/lidl-plus-teilnahmebedingungen/s10005289 – angezeigte App-Preise können von verbindlichen Filial-Regalpreisen abweichen.
- PENNY Scan&Go: https://www.penny.de/datenschutz/agbs-scan-and-go – Artikel einzeln scannen, Preis kann abweichen.
- Kaufland Scan: https://filiale.kaufland.de/service/haeufige-fragen.html – kundenkontoabhängig, nur bestimmte Filialen, laufender Warenkorbwert.
- Netto Plus Scan&Go: https://sso.netto-online.de/oauth/account/consent?key=datenschutzhinweise-netto-app – Standort nötig, um die **je Filiale korrekten Preise** anzuzeigen.

Diese offiziellen Funktionen beweisen, dass die Händler intern *artikelbezogene Filialpreise* verwalten und ausgeben; sie beweisen **keine externe, vollständig auflistbare oder freigegebene öffentliche Preis-API**.

### Gefundene Fremdprojekte – kritisch

- [aldiscount](https://github.com/ByteSizedMarius/aldiscount) – echter unfiltrierter ALDI-Süd-Produktsuchclient, im Test-Runnersystem aber 403.
- [BlackFalconData Lidl Scraper](https://github.com/BlackFalconData-org/lidl-scraper) – kostenpflichtiger Apify-Actor mit Webshop-/Produktpreisen, kein nachgewiesener vollständiger Preisbestand ausgewählter Lidl-Filialen.
- [loukesio/german-supermarket-prices](https://github.com/loukesio/german-supermarket-prices) – 9.109 Preisbeobachtungen, **0 Preise mit Datumsangabe in den letzten 30 Tagen** des 31.10.2026-Snapshots; häufig alte Beobachtungen, teils Händler-Prospekte und unklare Rechte. **Nicht der gesuchte aktuelle Händlerpreiskatalog.**
- [Open Prices](https://prices.openfoodfacts.org) – echte kostenlose API für von Nutzern gemeldete historische Preise; aber unvollständig und kein tagesaktueller Filialpreiskatalog.

## Implementierungsentscheidung

Bisher darf kein Anbieter als `FULL_STORE_PRICE_CATALOG_VERIFIED` gelten. Ein Parser-Erfolg auf zwei ALDI-Nord-Kategorien ist zwar ein Fortschritt, jedoch kein vollständiges Sortiment.

Als belastbare Lösung für den späteren Preisvergleich sind drei Felder getrennt zu validieren: `actual_regular_price`, `actual_offer_price`, `store_id`. Solange die Quelle nur `displayed_current_price` oder `CHAIN_WIDE_REPORTED` liefert, **nicht** als garantierten aktuellen Kassenpreis der gewählten Filiale ausgeben.

Weiteres Vorgehen: ALDI Nord Kategorieindex/Abdeckung und eventuell Händlerpreisregeln verifizieren; für die vier Scan&Go-Händler nur ausdrücklich freigegebene Einzelprodukt-Lookups oder dokumentierte, erlaubte Exporte prüfen; keine technische Schutzumgehung und keine kostenpflichtigen APIs.
