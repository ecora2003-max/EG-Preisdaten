# Weitere Live-Versuche: Filialpreiskataloge (31.10.2026)

**Ziel:** Auslesbarer, möglichst vollständiger aktueller Produktpreisbestand einer konkreten Filiale. Aktionen ohne regulären Produktkatalog und historische Preisbeobachtungen sind keine Lösung.

## Neu verifizierte Ergebnisse

1. **ALDI Nord:** Der existierende Python-Katalogparser wurde auf **fünf echte unterschiedliche Lebensmittel-Sortimentskategorien** erweitert. [GitHub-Live-Lauf – PASS](https://github.com/ecora2003-max/Try/actions/runs/41188539904). Alle API-Hits hatten einen lesbaren angezeigten Produktpreis:

   | Kategorie | Gemeldete / abgerufene / bepreiste Artikel |
   |---|---:|
   | Joghurt, Quark und Milchdesserts | 50 / 50 / 50 |
   | Milch und Milchgetränke | 32 / 32 / 32 |
   | Schweinefleisch | 34 / 34 / 34 |
   | Tiefkühlobst/-gemüse | 8 / 8 / 8 |
   | Wurstaufschnitt/-streichwurst | 40 / 40 / 40 |
   | **Gesamt über fünf Kategoriesnapshots** | **164 / 164 / 164** |

   **Einschränkung:** 164 sind die Summe von fünf Kategorien, nicht nachgewiesen 164 einzigartige Ladenartikel. Die Preise stehen unter `currentPrice.priceValue` im offiziellen `__NEXT_DATA__`/Algolia-Katalog. Es gibt keinen verifizierten Einzel-Filialfilter. Kein vollständiger Gesamt-Katalog, keine garantierten Kassenpreise.

2. **Lidl:** [Live-Lauf: Unterkategorie Milch & Sahne – PASS](https://github.com/ecora2003-max/Try/actions/runs/41188277397). Das echte filialbezogene Produktkatalog-API liefert **27/27 Produkte einschließlich aktuellem Preis** über `/categories/1004/categories/1001/products?skip=0&limit=30&date=2026-10-31`. Bereits davor weitere vollständige Kategorie Fisch/Meeresfrüchte **29/29**. Das zeigt, dass die Produktpreisliste auch in **verschachtelten Kategorien** funktioniert. Nicht alle 18 Wurzelkategorien sind bis zum Ende getestet.

3. **PENNY:** [Live-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41188513187) – zwei versuchte öffentliche Such-URLs `/suche?q=Milch`, `/suche?query=Milch` gaben **HTTP 404**. Eine zuvor getestete offizielle PENNY-Sortiment-Produktdetailseite hatte **keinen echten Regalpreis**. Nur regional gebundene Sonderangebote sind technisch bestätigt. **Das ist kein Beweis, dass es keinerlei interne Preis-API gibt.**

4. **Kaufland:** [Live-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41188513187) – die veröffentlichte Filialwebsite beantwortet `/suche.html?q=Milch` mit HTTP 200 und enthält einige Preisfelder; der Test konnte sie **nicht als vollständige Normalpreis-Produkte einer Filiale** validieren. Die Variante `?search=Milch` enthielt keine Suchtreffer. Händler-Filialangebote bleiben die einzige bestätigte maschinenlesbare Preisquelle. Die separate Seller-API betrifft ausschließlich den **Kaufland-Marktplatz** und dessen Verkäuferpreise.

5. **Netto Marken-Discount:** Vorhandene [Netto+](https://apps.apple.com/de/app/netto/id1216226806) bietet im realen Markt einen Barcode-Preisscanner, jedoch **keinen nachgewiesenen anonymen, listenbaren Gesamtpreisfeed**. Offizieller marktbezogener PDF-Prospekt technisch nachgewiesen, keine vollständigen Regal-Normalpreise. Verbindliche Zugriffsbeschränkungen wurden nicht umgangen.

6. **EDEKA:** Keine weiteren automatisierten Abrufe, da die zuvor geprüften EDEKA.de-Nutzungsbedingungen eine ausdrückliche Freigabe für die systematische Datenübernahme verlangen. Dritt-Online-Marktplätze und einzelne `edeka.shop`-Shops sind keine bestätigte bundesweite Filial-POS-Datenquelle.

## Weitere geprüfte Community-Spuren

- `LS19GamerMarius/snapmarkt-server` implementiert herkömmliches Puppeteer-Scraping von **Onlineshop- oder normalen Webseiten**, darunter Lidl.de, ALDI Süd und PENNY; **nicht** die verifizierte Filial-Produktkatalog-Schnittstelle. Daher für tatsächliche Ladenkassenpreise nicht belastbar.
- `Scxttk/lechariot-backend` dokumentiert PENNY-Regionalangebote und Kaufland-App-Filialangebote. Dies sind **Aktionsquellen**, keine vollständigen Normalpreiskataloge.
- `EvickaStudio/kaufland-discounts` und `Stortox/KaufiAlert` nutzen Kaufland-Angebots-Endpunkte; keine regulären kompletten Sortimentspreise.
- Preisvergleichs-/Marketplace-APIs, die Kaufland.de-Produktseiten oder Sellers abfragen, sind für Supermarktregalpreise ungeeignet.
- Kein in diesen untersuchten Quellen veröffentlichter, offen nutzbarer Vollpreiskatalog für PENNY, Kaufland, Netto oder EDEKA bestätigt.

## Arbeitsstand

Nur **Lidl** hat bislang einen **konkreten, filialbezogenen, funktionierenden Katalogendpunkt mit aktuellen Einzelproduktpreisen**. **ALDI Nord** hat einen reproduzierbaren, breiten Katalog einzelner Kategorien mit angezeigten Preisen, jedoch keinen Filialfilter. Bei den anderen vier Händlern ist das Ziel nicht belegt. Produktive, fortlaufende Nutzung setzt zusätzlich geeignete Berechtigungen und sorgfältige Preisvalidierung voraus.

**Repos:** Änderungen ausschließlich in `ecora2003-max/Try`; **`Ernaerungsgedaechnis` nicht geändert**.
