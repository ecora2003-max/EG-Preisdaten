# Scan&Go-Preiskataloge – EDEKA, PENNY und andere Händler

**Prüfung:** 31.10.2026 · **Ziel:** Tatsächliche Marktpreise des möglichst vollständigen physischen Filialsortiments. Keine bloßen Prospekte oder historischen Bonpreise. Keine bezahlten APIs, keine fremden Benutzerkonten oder App-Tokens.

## Wichtigster neuer Architekturfund: PENNY und REWE nutzen denselben Scan&Go-Lieferanten

Der Lösungsanbieter **shopreme** bestätigt die direkte Integration seines Scan&Go-SDK in die deutsche [PENNY-App](https://www.shopreme.com/blog/more-than-160-penny-germany-stores-go-live-with-scan-go-by-shopreme/) und die [REWE-App](https://shopreme.com/de/case-studies/rewe-scan-and-go-success-story). Dies ist eine **echte gemeinsame Technologie**, nicht nur eine Vermutung aufgrund der REWE-Konzernzugehörigkeit.

### Was tatsächlich in der Shopreme-Architektur existiert

Die öffentlich zugängliche [DataHub-Dokumentation](https://docs.shopreme.com/kb/management-console/datahub-import-jobs) bestätigt:

- einen **zentralen vollständigen Produktimport** (`productName`, `scanCodes`, `productNumber` und Merkmale); Produkte werden grundsätzlich global importiert;
- **filialspezifische Preise** über `storeId` bzw. das Array `storePrices`;
- einen **eigenständigen Preisimport** mit `productNumber`, `price`, `strikePrice` und `taxRate`, ausdrücklich auch für regelmäßige Delta-Updates;
- Kategorienimporte sowie die Preisanzeige und Produktzuordnung nach dem Scan;
- getrennte Einkaufswagenpreisberechnung inklusive Rabatten durch den [`/evaluate`-Mechanismus](https://docs.shopreme.com/kb/datahub/outbound-api/baskets-and-pricing).

Die [Produktdetaildokumentation](https://docs.shopreme.com/kb/management-console/product-detail-page) erläutert ausdrücklich Standardpreise oder Filialpreise je Produkt. Die [Verwaltungsoberfläche](https://docs.shopreme.com/kb/management-console/overview) kann anhand `Available in` die Produkte eines bestimmten Marktes filtern.

**Wichtig:** `/evaluate` ist laut offizieller Dokumentation eine **ausgehende Server-zu-Preisengine-Schnittstelle**, die den Warenkorb bewertet. Es ist **keine bewiesene öffentliche Produktpreissuche** und darf nicht als solcher Endpoint ausgegeben werden.

**Zugriffsgrenze:** Der Händlerbetrieb verwendet getrennte, benutzerauthentifizierte Shopreme-Managementserver mit **API-Tokens bzw. HTTP-Basic-Authentifizierung**. Die für Händler konfigurierten produktiven Import-/Preisexportdaten sind nicht öffentlich freigegeben. Ein von shopreme dokumentiertes Datenformat ist **keine anonyme Händler-API**, ebenso keine Nutzungsfreigabe. **Bisher keine aktuelle PENNY-Preiszeile aus dieser Quelle ausgelesen.**

**Weitere Spur:** [Shopreme erklärt Offline-Scanning](https://shopreme.com/de/solutions/scan-and-go): Lokale kleine Produktdateien mit Preisen, Namen und Barcodes werden auf Scannergeräte geladen. Ob diese Daten vollständig, aktuell, filialbezogen und rechtmäßig exportierbar sind, muss getrennt nachgewiesen werden. Der Scan&Go-Dienst kann für die finale Preisberechnung über die Server-Pricing-Engine gehen. Eine lokale Scanner-Zwischendatei ist **nicht** automatisch der volle POS-Preiskatalog.

### Reale Tests

[GitHub Actions – Public Vendor Sources, bestanden](https://github.com/ecora2003-max/Try/actions/runs/41190033352), [Script](../tools/vendor_scan_go_feasibility.py):

- Sechs öffentliche Dokumentationsseiten unter `docs.shopreme.com` konnten mit HTTP 200 gelesen und inhaltlich auf Produktimport, Filialpreise, Preisaktualisierung und externe Preisberechnung geprüft werden.
- `b2c-gw.api.edeka` wurde nach eingeschränkter/nicht verifizierbarer robots-Policy **nicht automatisiert abgefragt**.
- Es wurde weder ein Drittanbieter-Token benutzt noch eine geschützte Einkaufssitzung gestartet.
- **Keine der geprüften Händlerplattformen gab in diesen Tests einen extern abrufbaren Vollpreisbestand zurück.**

## EDEKA: konkretes offizielles API-Gateway – aber Zugang nur auf Anfrage

Die tatsächlich erreichbare [öffentliche Startseite von `https://b2c-gw.api.edeka/`](https://b2c-gw.api.edeka/) nennt sich **„EDEKA B2C API Gateway V2“** und fordert Interessierte ausdrücklich auf, EDEKA für den API-Zugang zu kontaktieren. [EDEKA-App-Bedingungen](https://www.edeka.de/services/nutzungsbedingungen/) nennen **GK Software** als technischen Dienstleister, Scan&Go und Kontofunktionen.

Die [offizielle EDEKA-Scan&Go-Beschreibung](https://www.edeka.de/services/scan-go/) bestätigt marktgebundenes Scannen nach Anmeldung. [EDEKA-Datenschutz](https://www.edeka.de/datenschutz/) bestätigt die Verarbeitung von EAN-/Scanartikeldaten und der Marktzuordnung.

**Open Source:** [ByteSizedMarius/edekompile](https://github.com/ByteSizedMarius/edekompile) implementiert EDEKA-App-Angebote, Marktfindung und digitale Kassenbons. Die tatsächlich dokumentierten Befehle/Quellcode-Dateien enthalten **keine Produkt-Scan- oder vollständige Filialpreis-API**. App-Anmeldedaten können auch Zahlungsvorgänge autorisieren; sie dürfen nicht in GitHub Actions oder einem öffentlichen Repository verwendet werden.

**GK-Dokumentation als technische Forschungsrichtung:** Das [Self-Scanning-Backend von GK](https://help.sap.com/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-backend/topics/productdescription_basket_service/overview.html) beschreibt Offline-Produktstammdaten auf dem Einkaufsgerät und eine finale Warenkorbpreis-/Aktionsberechnung. Dies beschreibt eine **allgemeine GK-Architektur**, nicht den empirisch bewiesenen konkreten EDEKA-Gateway-Pfad. Daraus darf kein öffentlich zugänglicher Produktpreiskatalog konstruiert werden.

**Ergebnis EDEKA:** Technische Markt-Angebotsdaten existieren (vorherige echte Live-Tests), Scan&Go verarbeitet Markt-/Artikeldaten. Die offizielle B2C-Gateway-Startseite belegt einen potenziellen autorisierten Integrationsweg; die Erlaubnis ist noch nicht erteilt. Ein Vollsortiment mit aktuellen Preisen wurde **nicht** ausgelesen.

## PENNY: viel konkreter geworden, aber keine kostenlose öffentlich lesbare Preis-API

Aufgrund des nun direkt nachgewiesenen **shopreme-SDK** sind die Felder für den Filialpreis-Bestand und ihre Synchronisierung nachvollziehbar. Das macht einen technisch sauberen Import **nach einer Erlaubnis des Händlers/Anbieters** realistisch. Ohne freigegebene Shopreme-Integration gibt es dagegen aktuell nur unsere vorher live bestätigten `penny.de/.rest/market` und regionalen Aktionslisten, keinen vollständigen Ladenpreiskatalog.

## REWE als technische Schwester – nicht PENNY-Daten

[ByteSizedMarius/rewerse-engineering](https://github.com/ByteSizedMarius/rewerse-engineering) besitzt `pkg/products.go` mit Such- und Kategoriesuche `GET /api/products`, `GET /api/products/{id}` samt Marktkontext. **Dies ist die REWE-App-Produkt-API, nicht die PENNY-Scan&Go-/Shopreme-Datenbank.** Laut Projektbeschreibung erfordert die App-Schnittstelle mTLS bzw. gerätespezifische Zugangsvoraussetzungen; keine Schutzumgehung oder Übernahme fremder Zertifikate.

## ALDI Nord: vermeintliche Übertragbarkeit der Shopreme-Lösung ist geografisch begrenzt

[shopreme-Pressemitteilung](https://shopreme.com/de/blog/aldi-nord-new-checkout-experience-shopreme) bestätigt Scan&Go-Testfilialen von ALDI Nord **in den Niederlanden**; diese Information belegt **keine** Verwendung desselben Preisbackend in deutschen ALDI-Nord-Filialen. Unsere deutschen ALDI-Nord-Produktkategorie-Preis-Tests (164/164 Hits über fünf Kategorien) bleiben davon unabhängig.

## Netto Marken-Discount / Kaufland

Keine bestätigte Identität der dortigen Scan&Go-Technologie mit shopreme. Ein analoger Hostname oder gleicher JSON-Aufbau ist nicht belegbar; für beide besteht bislang nur Zugriff auf bekannte marktbezogene Werbeartikel-/Prospektdaten. Die Netto-plus-App erfordert Registrierung und Standort für Scan&Go-Preise; eine auflistbare API wurde nicht gefunden. Die Kaufland-Scannerfunktionen benötigen Marktsitzungen/Kaufland Card, aber kein bestätigter Vollpreiskatalog-Endpunkt.

## Konsequenz für „Ernährungsgedächtnis“

1. **Lidl** bleibt die einzige in diesem Projekt live validierte **filialbezogene Katalog-Schnittstelle mit aktuellen angezeigten Einzelpreisen**, mit bekannten Grenzen für die vollständige Artikeldeckung.
2. **ALDI Nord** verfügt über einen nachweislich abrufbaren kategorieweisen Preiskatalog; filialindividuelle Preise bislang nicht bestätigt.
3. **PENNY** hat mit shopreme einen **nachweislich existierenden store-spezifischen Produkt-/Preisbestand**, aber bisher **keinen für uns nutzbaren API-Zugriff**.
4. **EDEKA** hat ein offizielles, **zugangspflichtiges B2C-Gateway** sowie separate Scan&Go-Funktionen. Ein konkreter öffentlicher Vollpreiskatalogzugang ist nicht erwiesen.
5. **Netto Marken-Discount/Kaufland:** Keine neue Vollpreis-Schnittstelle bestätigt.

**Protokoll:** Ausschließlich `ecora2003-max/Try` wurde beschrieben. Das separate App-Repository `Ernaerungsgedaechnis` wurde nicht verändert. Die offizielle Händler-/SDK-Dokumentation wurde nicht als Berechtigung zur Datennutzung missverstanden.
