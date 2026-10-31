# Fortsetzung: Scan&Go-Katalogzugänge und Reverse-Engineering-Funde

**Datum:** 31. Oktober 2026 · **Bearbeitet:** ausschließlich `ecora2003-max/Try` · **Nicht verändert:** `ecora2003-max/Ernaerungsgedaechnis`

## Zieldefinition

Gesucht wird ein **vollständig enumerierbarer, aktueller Filial-Verkaufspreiskatalog** pro Händler und Standort, möglichst inklusive normalem Preis, App-Preis und Angebots-Preis. Einzelne Barcode-Lookups sind eine wertvolle Teilfunktion, aber **kein vollständiger Produktlistenexport**. Jede Quelle benötigt auch technisch passende Berechtigungen.

## 1. Neuer GitHub-Fund: statische APK-Analyse mit konkreten EDEKA- und Netto-Endpunkten

**Originalprojekt:** [chukfinley/apk-url-extractor](https://github.com/chukfinley/apk-url-extractor) · [Analyse von sechs Supermarkt-Apps vom 12.07.2026](https://github.com/chukfinley/apk-url-extractor/blob/master/reports/grocery-price-apis.md).

Dieser Bericht wurde in der aktuellen Runde direkt aus GitHub abgerufen und der Quelltext überprüft. Der Autor analysierte statisch APK-/DEX-/Flutter-Kompilate, **nicht** den Netzwerkverkehr; die unten stehenden Routen sind daher **im App-Code dokumentiert, aber nicht live validiert**.

### Netto Marken-Discount (rot-gelb, `netto-online.de`)

Im untersuchten valuephone-/Retrofit-Stack mit **178 genannten Retrofit-Endpunkten** findet sich:

```text
GET /api/v1/mpos/{storeId}/itemInfo?itemEAN={ean}&allRelatedItems={flag}
GET /api/v1/mpos/{storeId}/analyzeBarcode?barcode={barcode}
```

Das spricht für einen **artikelweisen tatsächlichen Filialpreis-Lookup** der mobilen Selbstscan-Kasse. `mpos` bezeichnet mobile Point of Sale und ist keine reguläre Shop-Produktsuche. Eine gültige `storeId` und nach Betreiberregeln ggf. Markt-Sitzung/Auth sind erforderlich. Der Fremdbericht nennt in dieser Passage keinen eindeutig verifizierten Host für diese Pfade. **Kein erfolgreicher Live-Abruf**, keine Umgehung der Markt-/Benutzeranmeldung, kein Abruf eines Netto-Vollsortiments.

**Wichtig:** Das ist **Netto Marken-Discount**, nicht Netto mit Scottie-Hund.

### EDEKA

Im selben APK-Analyseprojekt werden folgende App-API-Bereiche genannt:

```text
GET /v1/product/ean/{ean}
GET /v3/offers/grouped?marketId={id}&includeNational=...
GET /v2/catalogues?marketGln={gln}
```

Als App-Hosts nennt der Autor `offerfinder.server.valuephone.com` und `shopping.mobile.vpserverapp.valuephone.com`. Die Analyse belegt einen **Barcode-/EAN-Lookup und marktbezogene Angebotsdaten**, nicht eine komplette Produkt-/Preis-Suchliste. Eine dauerhafte automatische EDEKA-Nutzung ist gemäß den bereits ermittelten EDEKA.de-Nutzungsbedingungen nicht ohne Freigabe gestattet; deshalb wurde kein neuer Produktabruf ausgeführt.

**Andere, bereits geprüfte EDEKA-Open-Source-Bibliothek:** [ByteSizedMarius/edekompile](https://github.com/ByteSizedMarius/edekompile) enthält Angebote, Marktzuordnung und eBon-Methoden, aber bislang keine technisch nachgewiesene vollständige Filial-Preisliste.

## 2. Unabhängiger Architekturbeleg: GK Self-Scanning

EDEKA dokumentiert in seinen [App-Bedingungen](https://www.edeka.de/services/nutzungsbedingungen/) GK Software als technischen Dienstleister für die App einschließlich Scan&Go. Die öffentlich lesbare [GK Self-Scanning-Architektur](https://help.sap.com/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-backend/topics/clientsdk_self_scanning_using_self_scanning_service/architecture_overview.html) erläutert technisch:

- Die **Store Device Control (SDC) / Master Data Service** verteilt für den ausgewählten Markt **vereinfachte Artikelstammdaten und Preise** als „Master Data Pump“ zum Start eines Scan&Go-Einkaufs.
- Das Gerät kann damit Artikel **offline** erkennen und vorläufig bepreisen; die zentrale Warenkorb-/POS-Engine validiert die Positionen, Aktionen und finalen Preise.
- Das [GK-Check-in-Konfigurationsschema](https://help.sap.com/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-client-bring-your-own-device/topics/customizingguide/general_configuration.html) enthält unter anderem `businessUnitId`, `tenantId` und `baseUrl`; der reguläre Start einer Session kann einen Markt-QR-Code erfordern.
- Die [GK-Gateway-Dokumentation](https://help.sap.com/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-backend/topics/clientsdk_self_scanning_using_self_scanning_service/architecture_overview.html) beschreibt Authentifizierung und Validierung von Anfragen.

**Relevanz:** Ein **marktbezogener Artikel-/Preis-Snapshot** existiert in dieser SDK-Architektur tatsächlich. Das heißt aber **nicht**, dass sich der konkrete EDEKA- oder Netto-Datenpump ohne berechtigten App-Check-in, Tenant und Auth abrufen lässt. Außerdem ist nicht bewiesen, dass diese allgemeine SDK-Konfiguration identisch mit jeder EDEKA-/Netto-Filialimplementierung ist.

**Historische Verbindung zu Netto:** Ein [GK-Investorbericht von 2020](https://investor.gk-software.com/en/publications/research?cid=764&task=download) berichtete über Netto-Tests von GK Scan&Go; ein [Retail-Optimiser-Bericht von 2020](https://retail-optimiser.de/en/edekas-netto-brings-self-scanning-to-its-app/) bezeichnet die damalige Netto-Implementierung als Eigenentwicklung. Deshalb können wir **keine unverändert gemeinsame Backend-API im Jahr 2026** als gesichert behaupten.

### Technische Testgrenze

Der [eigens angelegte GitHub-Actions-Dokumentationscheck](https://github.com/ecora2003-max/Try/actions/runs/41190377549) lief ohne Programmfehler, **übersprang aber alle drei SAP-Hosts** wegen im Runner nicht verifizierbarer Crawler-Regeln. Diese Aufgabe belegt daher **keine erfolgreiche HTTP-Abfrage** der SAP-Dokumentationsseiten aus GitHub Actions. Die Inhalte wurden stattdessen anhand öffentlich erreichbarer Web-Dokumentationen abgeglichen. Der Test hat niemals einen echten Markt-/Artikelpreis abgefragt. [Testcode](../tools/gk_official_selfscan_docs.py).

## 3. PENNY + REWE: shopreme Preisbestand, aber geschützt

[Shopreme-Dokumentation](https://docs.shopreme.com/kb/datahub/overview) und [bereits bestandener Test](https://github.com/ecora2003-max/Try/actions/runs/41190033352) belegen ein importiertes Marktproduktverzeichnis und `storePrices`-/Preisänderungs-Datensätze. [Produktscanning](https://docs.shopreme.com/kb/clients/scan-go-and-sdk/product-scanning) basiert auf importierten Barcode→Produktverbindungen; eine Warenkorb-`/evaluate`-Funktion wird **gegen ein externes Pricing-System vom Shopreme-Backend aus** aufgerufen, nicht als anonyme App-Produktsuche.

**Folgerung:** Es existiert ein vollständiges internes Produkt-/Filialpreis-Datenmodell, aber kein verifizierter kostenfreier externer Vollpreiszugriff.

## 4. Weitere Ketten

- **Kaufland:** Die bisherige Filial-API liefert nachweislich `klNr`-Werbeartikel, keine kompletten Ladenpreise. Marketplace-Seller-API ist keine Alternative. Ein bestimmter Vollsortiment-/K-Scan-Produktpreis-Endpunkt wurde auch im neuen GitHub-Suchlauf nicht belastbar identifiziert.
- **ALDI Nord:** Fünf vollständige Kategorien lieferten 164 von 164 bepreisten Datensätzen; keine Einzel-Filialpreiszuordnung, keine Gesamtsortiment-Vollständigkeit.
- **Lidl:** Erfolgreiche echte Produktkatalog-API mit konkretem Filial-`storeKey`; bisher zwei vollständige Teilkategorien (29/29 und 27/27), bisher der beste belegte direkte Pfad.

## 5. Realistischer nächster technischer Ansatz

1. **Netto Marken-Discount:** Hersteller-/App-Bedingungen prüfen, ob ein berechtigter Testzugang zu `mpos/.../itemInfo` ohne tatsächlichen Einkauf oder Filialsitzung existiert. Solange nicht nachgewiesen, keine automatisierten Barcode-Probes oder Passwort-/Token-Übernahmen. **Einzel-Scan ist noch kein Gesamtkatalog.**
2. **EDEKA:** Produktdetail/Barcodelookup und GK-Master-Data-Pump anhand einer offiziell freigegebenen Testumgebung oder einem Entwickler-/Partnerzugang validieren.
3. **PENNY:** Um zulässigen Preisimport-/Produktkatalog-Export bei Shopreme oder PENNY als Nutzer einer Filiale ersuchen. Ohne Token keine private Händlerverwaltung abfragen.
4. **Kaufland:** Suche gezielt nach Filialpreis-/POS-Service-API statt Seller-API fortsetzen.
5. **Lidl:** Vollständigen Kategorienbaum inklusive Datum, gültigem Preis, Coupon-/App-Preis, Mengen und Pfand zuverlässig validieren. Recht zur kontinuierlichen Nutzung separat klären.

## Entscheidende Qualitätsgrenze

**Kein neu gefundener App-Endpunkt wurde in diesem Durchlauf als tatsächlicher, aktuell zugänglicher Gesamtfilialpreiskatalog bestätigt.** Gefunden wurden *konkrete, glaubwürdige EAN-/POS-Schnittstellen* und eine dokumentierte, filialbezogene Master-Data-Architektur, die bei einem legitimen Integrationszugang nutzbar sein könnte.

Die hier verlinkten Reverse-Engineering-Projekte sind Drittbeobachtungen; statisch gefundene Pfade können veraltet, ungenutzt oder durch Authentifizierung geschützt sein. Fehlende EAN-/Produktdateien werden weder erfunden noch aus fremden Quellen als vollständiges Sortiment ausgegeben.
