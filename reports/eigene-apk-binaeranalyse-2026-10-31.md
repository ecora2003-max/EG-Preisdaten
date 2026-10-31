# Eigene APK-Binäranalyse der Supermarkt-Apps – 31.10.2026

## Ausführung und Reproduzierbarkeit

**Tatsächlich selbst ausgeführt**, nicht nur Aussagen anderer Reverse-Engineering-Projekte übernommen: Die öffentlich verteilten APK/XAPK-Container wurden temporär im kostenlosen GitHub-Actions-Runner heruntergeladen und deren DEX-, Native- sowie ausgewählte Asset-Dateien statisch untersucht. Keine App wurde installiert, ausgeführt, angemeldet oder mit einem Markt-/Kundenkonto verbunden.

- **[Erfolgreicher vollständiger Binäranalyse-Lauf für fünf Android-Pakete](https://github.com/ecora2003-max/Try/actions/runs/41191014066)**; [Quellcode](../tools/real_apk_static_analysis.py); Resultat als GitHub-Actions-Artefakt `actual-apk-endpoint-analysis`.
- **[Sicherheits- und Parser-Vertragstests PASS](https://github.com/ecora2003-max/Try/actions/runs/41191014117)**; [Tests](../tests/test_apk_static.py).
- APK/XAPK-Quellen: öffentliche reguläre Download-URLs von APKPure, über `https://d.apkpure.com/b/APK/{package}?version=latest`. Die heruntergeladenen Original-Binärdateien werden nach der Analyse gelöscht; **keine APKs, dekompilierten Quelltexte, Zertifikate oder API-Schlüssel wurden ins Repository übernommen**.
- Die SHA-256-Prüfsummen beziehen sich auf **genau das heruntergeladene Paket**, nicht zwingend auf eine vollständige Google-Play-Installation mit allen Splits. APKPure ist ein Drittanbieter; eine kryptografische Bestätigung der Herausgeber-Signatur wurde bislang nicht durchgeführt. **Statische Code-Referenz ist weder tatsächlich erreichbarer Endpoint noch Nutzungsberechtigung.**

## Eigene Erkenntnisse aus echten Paketen

| Händler | Paketkennung | Datei | Analysierte Dateien | Belegte technische Hinweise |
|---|---|---:|---:|---|
| **EDEKA – aktuelle App** | `de.edeka.genuss` | 48.743.613 Bytes | 1.443 | `/v1/product/ean/{ean}`; `/v3/offers/grouped`; `offerfinder.server.valuephone.com`; `ItemInfoDto`, MPOS-Klassen |
| **PENNY Kundenapp** | `de.penny.app` | 33.114.421 Bytes | 1.478 | `FirestoreMarket`, `FirestoreOffer`, `FirestoreOfferWeek`, `app.penny.de`, `account.penny.de`; **kein vollständiger regulärer Preisfeed daraus belegt** |
| **PENNY Scan&Go** | `de.penny.scango` | 18.377.522 Bytes | 396 | **`scanandgo-p.rewe-group.com`**, `ItemInfo`, `ProductDetail`, `PriceFormatter`, `SearchView`. Getrennt von der aktuellen Penny-Coupon-App |
| **Netto Marken-Discount** | `com.valuephone.vpnetto` | 190.153.095 Bytes | 1.503 | **`/v1/mpos/{storeId}/itemInfo`**; **`/api/v2/productSearch`**, `/api/v2/productScan`; `/v1/mpos/{storeId}/analyzeBarcode`; `ProductSearchResponse`; `app.netto-online.de` |
| **Kaufland** | `com.kaufland.Kaufland` | 171.100.002 Bytes | 2.662 | **`k-app-scan-dz-bff.api.prod.sit.sys.odj.cloud`**; **`ProductDownloadApi`**, `ProductSyncManager`, `ProductRemoteRepository`, `ReducedProductEntity`; Filialangebots-`/api/v7/offers/{storeId}` |

Diese Treffer kommen aus **eigenen Binär-Scans**; insbesondere Netto und Kaufland enthalten damit **konkrete neu identifizierte Produkt-/Scan-API-Kandidaten**, die in unseren vorherigen reinen Webseiten- und Prospektstudien noch nicht sichtbar waren.

### Netto Marken-Discount – stärkste neue API-Route

Im Paket `com.valuephone.vpnetto` werden gleichzeitig ein Store-kontextgebundener POS-Barcode-Lookup sowie eine **`productSearch`**- und **`productScan`**-Route referenziert. Das ist wesentlich spezifischer als ein allgemeiner Angebotsfeed.

- `/v1/mpos/{storeId}/itemInfo` wird aus demselben APK direkt bestätigt wie die statische Drittanalyse von `chukfinley/apk-url-extractor`.
- `/api/v2/productSearch` könnte – dem Namen nach – eine Produktsuche sein. **Ob sie Normalpreise liefert, welche Host-/Auth-/Query-Parameter sie erfordert und ob sie sämtliche Produkte listet, wurde nicht geprüft.** Ein Name allein ist kein Beweis für Nutzbarkeit.
- Andere MPOS-Methoden enthalten bewusst checkout-/transaktionsbezogene Aufgaben. **Diese wurden weder ausgeführt noch mit Kunden-, Zahlungs- oder Filialsitzungen angesprochen.**

### Kaufland – Produktdownload statt nur Einzel-Barcode

Das Kaufland-Paket enthält `ProductDownloadApi`, `ProductSyncManager`, `ProductLocalRepository`, `ProductRemoteRepository` und `ReducedProductEntity` sowie den eindeutig nach K-SCAN benannten Produktionshost:

```text
k-app-scan-dz-bff.api.prod.sit.sys.odj.cloud
```

Eine **lokale Produkt-Synchronisation/Download-Schnittstelle** erscheint damit wahrscheinlicher als zuvor. Sie könnte Preis-/Barcode-Stammdaten für den Scanner synchronisieren, aber die konkreten Request-/Response-Modelle und eventuelle Store- und Sitzungsbedingungen sind noch nicht bestätigt. Die bereits bekannte Filialangebots-API `app.kaufland.net` ist **nicht** automatisch derselbe Service.

### EDEKA – aktuelle statt alte App geprüft

Die echte aktuelle EDEKA-App hat das Google-Play-Paket `de.edeka.genuss` (nicht die alte `com.valuephone.vpedeka`-App). Die DEX-Klassen der aktuellen App enthalten sowohl Valuephone-Angebots- und EAN-Produkt-APIs als auch MPOS- und ItemInfo-Datentypen. Das bestätigt eine reale **Barcode-Produktabfrage** im aktuellen Code; einen enumerierbaren vollständigen Filial-Preisdatensatz haben wir nicht gefunden.

### PENNY – getrennte App-Oberflächen

Die reguläre Coupon-App und die ältere separate **PENNY Scan&Go**-App sind zwei unterschiedliche Pakete und technische Backends. Letztere referenziert tatsächlich `scanandgo-p.rewe-group.com`; Namens-/Klassenfunde weisen auf `ItemInfo`, `ProductDetail` und `PriceFormatter` hin. Ohne bestätigte öffentliche Katalog-Route und Berechtigung liefert dieser Host bislang **keinen für uns verifizierten vollständigen Preiskatalog**.

## Methodische Grenzen

- Statische Treffer im Code können historisch, nicht mehr verwendet, an andere Länder gebunden, nur zu Testzwecken vorhanden oder durch Authentifizierung geschützt sein.
- DEX-Strings und Hostnamen wurden **nicht** zu unbewiesenen konkreten HTTP-Aufrufen zusammengesetzt.
- Für **alle sechs Händler** fehlt weiterhin der Nachweis eines vollständigen, freigegebenen, tagesaktuellen **Filialkassenpreis-Katalogs**. Lidl bleibt die zuvor erfolgreich getestete Ausnahme mit tatsächlich lesbaren Produktpreis-API-Seiten (zwei komplette Kategorien); auch bei Lidl steht die Gesamtvollständigkeit aus.
- Es wurden **keine produktiven Store-/Session-Keys, OAuth- oder App-Signing-Credentials** aus APKs verwendet. Ziel ist eine legale, für den Nutzer langfristig wartbare Free-Plan-Lösung, nicht die Umgehung von Zugangskontrollen.

## Nächster Prüfschritt

Technisch sinnvoll ist die gezielte Dekompilierung der oben gefundenen **Netto `ProductAPIApi` und Kaufland `ProductDownloadApi`** mit JADX, um die *statisch vorgesehenen* REST-Methoden, Feldnamen und Store-ID-Parameter exakt zu verstehen. Auch dies ist keine Berechtigung zum Zugriff auf geschützte Händlerdaten.

**Repositoryregel:** Änderungen ausnahmslos in `ecora2003-max/Try`; `ecora2003-max/Ernaerungsgedaechnis` bleibt unverändert.
