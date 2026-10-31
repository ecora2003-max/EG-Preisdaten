# Entwicklungsmandat – Händlerangebote und Preisquellen
**Team:** Preisdaten | **Auftraggeber:** Architektursteuerung / Chat 1 | **Arbeitsstand:** 31.10.2026

## 1. Fachprodukt
Ein austauschbarer, ressourcenschonender **Datenquellenadapter**, der für deutsche Supermarktketten bekannte, zum Kaufdatum gültige Aktionspreise und, wo möglich, aktuelle reguläre Artikelpreise liefert. Alle Ausgaben sind quellen-, zeit- und marktgebunden, ohne vorzutäuschen, ein vollständiger Supermarktpreiskatalog zu sein.

## 2. Zielhändler
ALDI Nord, ALDI Süd, Lidl, REWE, EDEKA, Netto **Marken-Discount** (`netto-online.de`, nicht Netto-Scottie/Salling), Penny, Kaufland. Die acht Händler müssen einzeln identifizierbar sein; keine automatische Gleichsetzung von Discount-Marken und Händlergruppen.

## 3. Bestehende Arbeit und Nachweise
Das Repo ist ehemals `Try`. Bereits vorhanden sind Python-Referenzadapter, Forschungsberichte, Live-Testskripte und GitHub-Actions-Artefakte. **Nicht neu beginnen oder Ergebnisse erfinden.**
- `README.md`: chronologischer Forschungsstand; bestehende Tests und Berichte erhalten.
- `adapters/retailer_offers.py`, `catalogues/`, `tests/`, `tools/`, `reports/`: vorhandene Implementierungen und Messprotokolle.
- `reports/umfang-und-aktualitaet-preisdaten-2026-10-31.md`: Lidl-Kategorieabdeckung und REWE-Preistests.
- `reports/gesamter-preiskatalog-aldi-nord-rewe-aldi-sued-2026-10-31.md`: ALDI-Nord-Kategorien, ALDI-Süd-Pagination mit inkonsistenten Zählern, REWE nur gezielte stationäre Suche.
- `reports/netto-produktsuche-filialpreise-status-2026-10-31.md`: Netto-App enthält Produktliste mit EAN/Artikelnummer, separates POS-Preismodell **nur statisch** belegt; keine freie Filialpreisantwort.
- `reports/netto-weitere-preisquellen-und-freitextsuche-2026-10-31.md`: Netto-Webshop-Suchpreise sind **Onlinepreise**, nicht bestätigte Filialregalpreise.
- Penny/EDEKA/Kaufland: bisher vor allem regionale oder filialbezogene Aktionsdaten; keine vollständige öffentliche POS-Preisquelle belegt.
Berichte sind Momentaufnahmen; **aktuelle Ergebnisse vor weiteren Behauptungen erneut prüfen**. Vorhandene Referenz-URLs auf das frühere `Try` können über GitHub-Weiterleitungen funktionieren, sollten später kontrolliert aktualisiert werden, ohne historische Dokumente zu verfälschen.

## 4. Ausgangseingaben
`SearchRequest` (dokumentierter Modul-Eingang): Liste von `retailerId`/optional Händler-`storeId`/Region, Suchbegriff, Lebensmittelkategorie oder GTIN; `shoppingDate`, zulässiger Zeitraum für aktuelle und kommende Angebote, gewünschter Typ `SALE`/`REGULAR`/`BOTH`, Abruflimits und optional Offline-Modus. Fehlende Filialkennung löst **nicht** automatisch eine bestätigte Filialgeltung aus.

## 5. Datenausgabe
In `contracts/v1` der Architektur stehen `price.observation`-Nachrichten. Jede Beobachtung soweit verfügbar: konkrete Ware, Händler, Filiale/Region/Geltungsgrad, `gtin`/Händler-SKU, Namen, Marke/Eigenmarke, Bio-Status (nur wenn belegt), Gebindemenge und Basis, Preis-Cents, Preisart, Aktionsgültigkeit, App-/Couponbedingungen, Pfand, Quelle, Abrufzeit, Lizenzstatus, Abdeckungsstatus, Parser-/Adapterversion.
Neben Preisen eigene `DatasetCoverage`/Fehlerantwort dokumentieren: Kategorien, Seiten, Treffer, Abbruchgründe, Rate-Limits, Art der Prüfung. Teilmengen als solche markieren. `null` nicht zu `0` konvertieren. Interne Felder können anders heißen; Mapping zum Vertrag testbar belegen.

## 6. Such- und Katalogstrategie
- **Priorität A:** Angebotsabruf **aller acht Händler**, einzeln und cross-chain vergleichbar, aktuelle und bereits bekannt gegebene zukünftige Konditionen für Einkaufstag.
- **Priorität B:** aktuelle reguläre Preise **gezielt** für Produkte und FoodTypes, speziell Lidl, ALDI Nord/Süd, REWE; keine unbewiesene Vollständigkeit.
- **Priorität C:** Eigenmarken-/Katalog- und Filialpreise von EDEKA, Netto, Penny recherchieren, falls rechtmäßig erreichbar; öffentliche Kataloge ohne Preise als **Produktmetadata**, nicht als Preise, melden.
- **Priorität D:** zulässige Open-Data-Quellen (z. B. Open Prices), falls nützlich; Historie strikt von gegenwärtigen Händlerpreisen trennen. Quellenüberschneidungen deduplizieren; übernommene Quellenrechte für Speicherung/Redistribution prüfen.
- **Nicht** in diesem Modul: Matching-Bestätigung, Warnfarben, Kaufentscheidungen, Budgetplanung, Rezeptgenerierung, OCR oder reale Preis-/Bestandsbuchung.

## 7. Technische Anforderungen
- Trenne pro Händler Quelladapter, Parsing, Normalisierung und Transport; austauschbare Quellen mit einheitlichem Vertrag. Keine direkten Room-/UI-Abhängigkeiten.
- Bei Hersteller-/SKU-Daten immer genaue Quelle, Feldauszug, Umrechnung und Typ prüfen. Online- und Stationärpreis nie vermischen; `oldPrice` nicht als regulären Kassenpreis deklarieren.
- Nur rechtmäßig zulässige, vorsichtige GET-Abfragen; keine Logins fremder Nutzer, Tokens, geschützte Schnittstellenumgehung, automatische Massenextraktion bei ungeklärten Rechten. Kein verpflichtender kostenpflichtiger Dienst, kein Server.
- Timeouts, Caching, ETag wenn zulässig, sichere Fehlergrenzen, zurückhaltende Rate, sofortiger Abbruch bei Sperren, Monitoring nicht als Dauerjob versprechen. Trenne öffentliche API von inoffiziell beobachtetem Endpunkt.
- Daten zeitlich konsistent; Filial-/Regionsgültigkeit/Angebotsdatum nicht erraten.
- Android-Integrationspfad dokumentieren: Python-Referenz als Spezifikation oder auf Android portierbare Logik, keine versteckte Pflicht eines Cloudservers.

## 8. Lieferumfang
Fachkern mit dokumentierter `search`/`fetchOffers`/`lookupPrice`-Schnittstelle und optionalem Offline-Fixture-Provider; typisierte Fehler/Ergebnisse, Testfixtures, Validierungs- und Regressionstests, Quellenmatrix, Minimalbeispiele, Integrationsanleitung. Live-Quellen mit Status `LIVE_VERIFIED`, `EXPERIMENTAL`, `BLOCKED` oder `NOT_TESTED`; Rechte separat `PERMITTED`/`UNVERIFIED`/`RESTRICTED`.

## 9. Entscheidungsgrenzen
Du darfst technische Quellen/Parser, Retryverhalten, interne Datenklassen und Tests eigenständig verändern. **Du darfst nicht** die Semantik des kanonischen Vertrags, die App-Datenbank oder die Datenhoheit der Haupt-App ändern. Änderungen an gemeinsamem Modell als fachliche Änderungsvorschläge im eigenen Repo dokumentieren.

## 10. Akzeptanz
Siehe `docs/ACCEPTANCE.md`; ohne Tests und reale Nachweise wird nur `RESEARCHED` oder `PROTOTYPE`, nicht `READY_FOR_INTEGRATION`, gemeldet.
