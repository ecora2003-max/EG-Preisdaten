# Erweiterte Supermarkt-API-Analyse: vollständige DEX-Retrofit-Enumeration
**Stand: 31.10.2026.** Sämtliche sieben Matrix-Jobs im [originalen GitHub-Actions-Lauf 41193283187](https://github.com/ecora2003-max/Try/actions/runs/41193283187) **PASS**.

**Ziel:** Dieselbe von `hakimarun/lidl-plus-api` verwendete Grundmethodik – APK nicht nur nach bereits bekannten URLs, sondern nach den tatsächlichen HTTP-Methoden aller API-Interfaces durchsuchen – auf deutsche Händler anwenden. Ergänzend wurden quelloffene Clients in GitHub untersucht.

## 1. Reproduzierbare Methode

- Eigene Implementierung [tools/retailer_full_retrofit_readonly.py](../tools/retailer_full_retrofit_readonly.py) mit `androguard`, kein gezieltes Erraten von Klassennamen: **alle** DEX-Dateien jedes analysierten APK-Containers (auch XAPK-Splits, sofern relevant) nach deklarierten Retrofit-Annotationen durchsuchen.
- Extrahiert werden ausschließlich lesende, thematisch passende `GET`-/`HEAD`-Routen, Query-/Path-Parameternamen und zugehörige Interface-Namen. Andere HTTP-Methoden werden gezählt, aber nicht aufgezeichnet.
- APK-Bytes nur temporär, SHA-256 des heruntergeladenen Drittanbieterpakets wird im Actions-Artefakt dokumentiert. Kein Aufruf von Händler-APIs, kein App-Login, kein Umgehen von Zertifikatsanforderungen, kein Extrahieren von API-Secrets.
- Ergänzung zu [voriger breiterer JSX/JADX-/DEX-Klassen-Heuristik](../tools/broader_apk_discovery.py), deren [sieben Teiljobs bereits vollständig PASS](https://github.com/ecora2003-max/Try/actions/runs/41192568816) sind.
- **Methodengrenze:** Auswertbar sind statische Retrofit-Methoden in DEX. Flutter/Dart (`libapp.so`), React-Native/Hermes-Bundles, dynamische Endpunktkonstruktion und andere HTTP-Clients sind **nicht vollständig aufgelöst**. Methodenantworten, öffentliche Erreichbarkeit, Auth, Nutzungsrechte, Sortiment und Preiskorrektheit sind getrennt zu verifizieren.

## 2. Ergebnisse der tatsächlich ausgeführten vollständigen DEX-Scans

| Händler | DEX-Dateien | analysierte Klassen | Retrofit-Endpunkte im APK (alle Verben, gezählt) | Belegte thematisch relevante GET-Routen | Bemerkungen |
|---|---:|---:|---:|---|---|
| **ALDI Süd** | 3 | 26.051 | 35 | **8** | Vorherige Namensheuristik fand **0** Klassen, diese Methode extrahierte die obfuskierten Interfaces zuverlässig. |
| **Netto Marken-Discount** | 9 | 79.917 | 324 | 25 | Auch produktbezogene Query-Parameter direkt pro Retrofit-Methode belegt; zwei API-Familien. |
| **Kaufland** | 20 | 108.055 | 159 | 21 | Eigenständige K-SCAN-Produktdownload-API und Händlerangebote/-loyalty klar unterscheidbar. |
| **EDEKA** | 4 | 39.369 | 35 | 3 | EAN-Produktsuche, Angebote und Kataloge – aber kein freier Vollpreisexport. |
| **REWE** | 4 | 38.613 | 0 | 0 | Kein Retrofit im getesteten DEX-Nachweis; **keine Aussage über Flutter-/App- oder Website-Endpunkte**. |
| **PENNY Kundenapp** | 3 | 19.050 | 0 | 0 | Keine Retrofit-Annotation in diesen DEX, andere Protokolle möglich. |
| **PENNY Scan&Go** | 1 | 4.537 | 0 | 0 | Kein Retrofit-Produkt-GET gefunden; Scan&Go-Backend wird über andere App-/Bibliothekskomponenten angesprochen. |

*Die Spalte GET-Routen ist ein thematisch und auf GET/HEAD gefiltertes Ergebnis. Es handelt sich **nicht** um die Anzahl sämtlicher gefundener HTTP-Routen.*

### ALDI Süd – selbst aus aktuellem APK belegte GET-Methoden

```text
GET v3/product-search
GET v3/product-search-suggestion
GET v2/product-category-tree
GET v2/products
GET v2/products/{sku}
GET v2/service-point-product-availability
GET v2/barcode-mapping/{barcode}
GET v1/stores
```

Die Produktsuche hat explizit `q`, `categoryKey`, `promotionKey`, `limit`, `offset`, `servicePoint`, `serviceType` sowie weitere Parameter. Die vollständige Suche war nur durch Annotationsextraktion **auch obfuskierter Interfaces** möglich. Ein unabhängiges [quelloffenes Programm `ByteSizedMarius/aldiscount`](https://github.com/ByteSizedMarius/aldiscount) zeigt konkrete Struktur und paginierte Vollsortiment-Produktsuche über die öffentlich beobachtbare Web-API `api.aldi-sued.de`. Es behauptet bis ca. 3.400 Produktobjekte; **unsere eigene Live-Zählung wird davon nicht ersetzt**. Offiziell freigegebene Nutzbarkeit und tatsächliche regionale Regalpreise sind weiterhin offen.

### Netto Marken-Discount – entscheidende Zuordnung präzisiert

Direkt aus `org.openapitools.client.apis.ProductAPIApi`:
```text
GET rest/api/v2/categoryList
GET rest/api/v2/productSearch?searchString=...&storeId=...
GET rest/api/v2/productScan?ean=...&storeId=...&listUUID=...
```

Zusätzlich aus einer **anderen** API-Klasse `MPOSApi`:
```text
GET api/v1/mpos/{storeId}/itemInfo?itemEAN=...&allRelatedItems=...
GET api/v1/mpos/{storeId}/analyzeBarcode?barcode=...
```

**Neuer Erkenntnisgewinn:** Der Query-Parameter `storeId` gehört laut tatsächlicher DEX-Annotation **auch zur regulär benannten `productSearch`**, nicht nur zur Barcode-/POS-Methode. Das macht eine filialbezogene Textsuche **technisch plausibel**, ohne schon zu beweisen, dass sie Regalpreise liefert oder anonym benutzt werden darf. Weitere Netto-Endpunkte für Angebote, Filialen und Kategorien wurden ebenfalls direkt nachgewiesen. *Netto Marken-Discount* ist nicht der gleichnamige *Netto mit Scottie-Hund*.

### Kaufland – bestätigte Trennung von Produktdownload und Wochenangeboten

```text
GET v1/products/{countryId}/{storeId}
GET v1/products/{countryId}/{storeId}/{itemNr}
GET /data/api/v7/offers/{storeId}
GET data/api/v7/bff/offers/{storeId}
```

K-SCAN-`ProductDownloadApi` und `ProductApi` sind echte Methoden in `com.schwarzit.selfscan.shared.core.network.retrofit.api`, während `OffersV2Api` bzw. `KlDataApi` Angebotsdaten beziehen. Die Reichweite des Produktdownloads und mögliche Eintritts-/Marktsitzung bleibt offen. Zusätzlich aus App-Code: `v1/config/{countryCode}/{storeId}`; aus Angeboten u.a. `/api/v2/leaflets/{storeId}`.

### EDEKA – belegte aktuelle API-Klassen

```text
GET /v1/product/ean/{ean}
GET /v3/offers/grouped?marketId=...&includeNational=...
GET v2/catalogues?marketGln=...
```

EAN-Methode stammt aus Interface `edeka.digital.product.ean.data.MyNetFairRestAPI`, Angebots-/Katalogmethoden aus `de.edeka.sdk.data.OfferApi`. Das nachgewiesene EAN-Interface darf **nicht** als Vollsortimentsliste missverstanden werden. EDEKA-Nutzungsbedingungen untersagen automatisierte Datenübernahme ohne Erlaubnis; keine Live-Datenabfrage wurde erneut durchgeführt.

### REWE – ergänzender, wichtiger Open-Source-Fund außerhalb von Retrofit

Das externe [Projekt `chukfinley/bismark`](https://github.com/chukfinley/bismark) dokumentiert und implementiert **einen lesenden stationären Website-Produktpreis-Endpunkt**:
```text
GET https://www.rewe.de/api/stationary-product-search/products
    ?query=<Freitext>&wwIdent=<REWE-Markt-ID>
```
Nach dem Quellcode enthalten die JSON-Produkte `pricing.current`, `pricing.regular`, `pricing.refund` in **Cent**. Die Autoren berichten konkrete filialbezogene Preise. In der selbst untersuchten aktuellen REWE-App wurden zugleich `/api/stationary-product-search` und `/api/stationary-product-search/{id}` als Stringkonstanten gefunden; damit existieren **zwei voneinander unterscheidbare Quellcode-Indizien**. Diese Routen sind **nicht** gleichzusetzen mit der in [`ByteSizedMarius/rewerse-engineering`](https://github.com/ByteSizedMarius/rewerse-engineering) dokumentierten mTLS-geschützten mobilen Liefer-/Abhol-API. Ein eigener aktueller Live-Preisabruf für diese stationäre API wurde **nicht durchgeführt**. Rechtliche und technische Zugangsbedingungen bleiben zu prüfen.

### PENNY – Ergebnisgrenze

Reguläre deutsche Kundenapp und separate Scan&Go-App wurden statisch analysiert. Die zweite referenziert `scanandgo-p.rewe-group.com` und Produkt-/Item-/Preis-Datentypen, aber **keine für uns belegte enumerierbare Vollpreis-/Produktsuche**. Die Nullwerte in der Retrofit-Tabelle dürfen nicht als Nachweis verstanden werden, dass die App keine produktbezogenen Netzwerkzugriffe hat.

## 3. Prioritäten nach dem neuen Befund

1. **REWE stationäre Web-API**: verlässlich prüfen, ob `wwIdent`-Textsuche aktuell ohne Zugangsschutz und rechtlich zulässig Regalpreise des jeweiligen Marktes liefert, paginiert und großflächig verfügbar ist. **Kein** mTLS-Bypass.
2. **ALDI Süd**: vorhandenen Open-Source-Client und neue tatsächliche obfuskierte APK-Methoden schematisch abgleichen; Preis-/Kategorien-/Store-Abdeckung und Bedingungen separat validieren.
3. **Netto MD**: dokumentierte `productSearch(searchString,storeId)`- und `productScan(ean,storeId,...)`-Antwortmodelle prüfen; daraus keine unbewiesenen anonymen Zugänge ableiten.
4. **Kaufland**: K-SCAN-Produktdownload-Response-Datentypen, Store-Scope und K-SCAN-Sitzungsbedingungen statisch untersuchen.
5. **EDEKA/PENNY**: weiter nur legale, frei zugängliche Quellen oder Betreiberfreigaben prüfen; kein Vollexport belegt.

## 4. Evidenz- und Zugriffsbeschränkungen

Ein APK-Annotationseintrag **belegt nur, dass eine aktuelle App eine entsprechende Methode definiert**. Das allein beweist keine erfolgreiche Händler-Serverantwort, Datenvollständigkeit, Anonymität, Lizenz, Aktualität oder korrekten Kassenpreis. Die erfolgreichen GitHub-Jobs belegen die **statische Durchführung**, nicht einen Preis-API-Erfolg. GitHub-Actions-Artefakte mit maschinellen JSON-Befunden sind sieben Tage verfügbar; dieser Bericht bewahrt die wesentlichen Resultate dauerhaft.

Alle neuen Dateien wurden ausschließlich in `ecora2003-max/Try` angelegt. **`ecora2003-max/Ernaerungsgedaechnis` blieb unangetastet.**
