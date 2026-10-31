# Übertragung der Lidl-Fundmethodik auf weitere Lebensmittelhändler
**Stand: 31.10.2026; Recherche und neue Prüfinfrastruktur in `Try`.**
**Keine Änderungen an `Ernaerungsgedaechnis`.**

## A. Woher kam die funktionierende Lidl-Produktkatalog-API?

Konkrete, vom früheren `Try`-Bericht genutzte Primärquelle ist
[hakimarun/lidl-plus-api](https://github.com/hakimarun/lidl-plus-api),
insbesondere [LIDL_PLUS_API.md](https://github.com/hakimarun/lidl-plus-api/blob/main/LIDL_PLUS_API.md)
und [webapp/endpoints.json](https://github.com/hakimarun/lidl-plus-api/blob/main/webapp/endpoints.json).

Der Autor dokumentiert eine **statische Rekonstruktion der Android-App 17.11.4** mit **JADX plus eigenem Hermes-v96-String-Parser**.
Er ermittelte nach eigener Beschreibung **343 Retrofit-Endpunkte in 117 Interfaces**; die produktive Modulbasis
`https://product-catalog.lidlplus.com/` sowie GET-Kategorien/Product-APIs waren explizit verzeichnet.
**Dieser Drittbericht selbst enthält keine Live-Netzwerkmitschnitte.** Den separaten
Lidl-Filialkatalog-HTTP-200-Test mit Sprachheader, Kategorien und Einzelprodukt hat unser `Try`-Projekt später selbst dokumentiert:
[Live-Lidl-Testergebnisse](https://github.com/ecora2003-max/Try/blob/main/reports/tatsaechliche-filialpreiskataloge-2026-10-31.md).

Weitere unabhängig gefundene Github-Belege:
[oliverwikth/OpenShoppingList](https://github.com/oliverwikth/OpenShoppingList/blob/main/backend/src/main/resources/application.yml)
benutzt denselben Katalog-Host und die store-basierte Suche;
[madgIitch/What-s-in-my-fridge-/docs/lidl_catalog_api_research.md](https://github.com/madgIitch/What-s-in-my-fridge-/blob/main/docs/lidl_catalog_api_research.md)
beschreibt Kategorien, Unterkategorien und Paginierung für eine spanische Filiale.
Die Abhängigkeit dieser Projekte voneinander wurde **nicht** geprüft; deshalb sind dies Quellcode-Belege, keine drei unabhängig validierten Live-Tests.

## B. Dieselbe Suche für andere Händler: konkrete externe Funde

| Händler | Open-Source-Projekt und Methodik | Verwertbare neue/zusätzliche Aussage | Einschränkung |
|---|---|---|---|
| **ALDI SÜD** | [ByteSizedMarius/aldiscount](https://github.com/ByteSizedMarius/aldiscount), eigener Client aus öffentlich beobachteter Web-JSON-API | Dokumentierte **Produkt-Freitextsuche, Kategorien, Filialen, Wochenangebote**, Option `-store`; daher nächster aussichtsreicher Kandidat für Sortiment statt nur Angebote | Drittprojekt behauptet anonym nutzbare Requests; historischer [APK-Report](https://github.com/chukfinley/apk-url-extractor/blob/master/reports/grocery-price-apis.md) nennt dagegen `api_key` und `servicePoint`. Unterschiede in Version/Backend und konkrete Live-Erreichbarkeit noch **nicht aufgelöst**. |
| **REWE** | [ByteSizedMarius/rewerse-engineering](https://github.com/ByteSizedMarius/rewerse-engineering), inoffizieller Go/Python-Client | [Produktabfragen](https://github.com/ByteSizedMarius/rewerse-engineering/blob/main/pkg/products.go): `GET /api/products?query=...`, `GET /api/products?categorySlug=...`, `GET /api/products/{productId}`; Markt-ID, Service-Typ, Pagination; **Kategorien nur für Liefer-/Abholmärkte** | Laut Projekt benötigt die REWE-API **Client-Zertifikate/mTLS**; diese Zugriffssicherung wird nicht umgangen. Liefer-/Abholpreise sind nicht zwangsläufig identisch mit stationären Kassenpreisen. |
| **EDEKA** | [ByteSizedMarius/edekompile](https://github.com/ByteSizedMarius/edekompile), Rekonstruktion mehrerer ValuePhone-/EDEKA-Dienste | [Architektur](https://github.com/ByteSizedMarius/edekompile/blob/main/auth/architecture.md) unterscheidet SOAP/ValuePhone, Offers-REST-Gateway und User-SSO; dies erklärt, warum EAN-, POS- und Angebotsrouten nicht einfach dieselbe Produktdatenbank bedeuten | Keine allgemein zugängliche bepreiste Vollsortiments-API nachgewiesen; EDEKA-AGB untersagen nicht genehmigte automatische Datenentnahme. Keine App-Secrets oder Login-Flows übernommen. |
| **Netto Marken-Discount** | [chukfinley/apk-url-extractor](https://github.com/chukfinley/apk-url-extractor/blob/master/reports/grocery-price-apis.md) plus **eigene** [JADX-Untersuchung](https://github.com/ecora2003-max/Try/blob/main/reports/eigene-apk-binaeranalyse-2026-10-31.md) | Im echten APK nachgewiesen: `GET rest/api/v2/productSearch`, `GET rest/api/v2/productScan`, `GET api/v1/mpos/{storeId}/itemInfo` | Noch keine erfolgreiche autorisierte Live-Preisabfrage oder vollständige Produktsuche. **Nicht** mit Netto (Scottie/Salling) vermischen. |
| **Kaufland** | Eigene [APK/JADX-Analyse in Try](https://github.com/ecora2003-max/Try/blob/main/reports/eigene-apk-binaeranalyse-2026-10-31.md) | `GET v1/products/{countryId}/{storeId}` und Einzelartikel-GET in K-SCAN gefunden | Format, Umfang und App-Sitzung ungeklärt; Kaufland-Marktplatz-APIs sind etwas anderes. |
| **PENNY** | Bisher eigene deutsche Kunden-App + separate Scan&Go-APK untersucht | Scan&Go-Host `scanandgo-p.rewe-group.com`, Produkt-/Preis-Datentypen; REWE-Gruppen-Technologien plausibel | Kein konkreter kompletter Produktexport verifiziert; keine Gleichsetzung von Penny- und REWE-Schnittstellen. |

**Evidenztrennung:** Quellcode-/APK-Fund != erreichbarer Endpoint != Preis-Response != vollständiger Filialkatalog != Nutzungsberechtigung.

## C. Neu umgesetzt: breiteres Discovery-Verfahren

Dateien:
- [tools/broader_apk_discovery.py](https://github.com/ecora2003-max/Try/blob/main/tools/broader_apk_discovery.py)
- [.github/workflows/broader-apk-discovery.yml](https://github.com/ecora2003-max/Try/blob/main/.github/workflows/broader-apk-discovery.yml)

Das Verfahren erweitert die bisherige Suche nach **nur vier vorab bekannten Klassen**:

1. Öffentliche APK/XAPK-Datei je App als temporäre Datei laden, SHA-256 der Bytes protokollieren. Quellen eines Drittanbieters sind **nicht** verifizierte Originalsignaturen.
2. Im temporär extrahierten APK DEX-, native Bibliotheken und textbasierte Assets breit nach **Hosts/Pfaden** durchsuchen.
3. Aus DEX-Klassenreferenzen **neue** fachlich relevante API-/Service-/Repository-Klassennamen heuristisch ermitteln, ohne die Endpunkte bereits zu kennen.
4. Pro App bis zu 10 priorisierte Kandidaten mit **JADX 1.5.6** dekompilieren; nur **GET/HEAD-Produkt-, Preis-, Such-, EAN-, Kategorie- und Filialrouten** samt unverknüpften Parameternamen speichern.
5. Ein JSON-Bericht als kurzlebiges GitHub-Actions-Artefakt je App (7 Tage), ohne APK-Bytes, Tokens, Zertifikate, Kunden-IDs oder dekompilierten Vollquellcode.

Prüfmatrix: ALDI Süd `de.apptiv.business.android.aldi_de`, REWE `de.rewe.app.mobile`, EDEKA `de.edeka.genuss`, Netto MD `com.valuephone.vpnetto`, PENNY `de.penny.app`, PENNY Scan&Go `de.penny.scango`, Kaufland `com.kaufland.Kaufland`.

**Status**: Skript und Workflow sind angelegt; ein erfolgreicher neuer Lauf und seine tatsächlichen Ergebnisse müssen separat überprüft werden. Ein Downloadfehler zählt nicht als analysierte APK. **Dies ist keine vollständige Hermes-Dekompilierung**: Flutter/Hermes wird weiterhin per String-Signatur gesichtet, dynamisch zusammengesetzte oder stark obfuskierte Routen können fehlen. Nur 10 priorisierte Klassen pro App werden mit JADX untersucht. Eine vollständige dynamische Netzwerkanalyse wurde **nicht** ausgeführt.

GitHub Actions auf dem öffentlichen `Try`-Repository nutzt Standard-Runner ohne kostenpflichtige externe API. Falls die öffentlichen Downloadquellen ausfallen, ist kein Ergebnis vorzutäuschen.

### Sicherheit / Rechtsstatus

Alle Schritte bleiben **statisch und lesend**. Keine Login-/Kassen-/Transaktionsoperationen, kein Umgehen von mTLS/OAuth, keine Nutzung extrahierter Zugangsdaten, kein massenhaftes Abfragen geschützter Händlerdienste. Vor kontinuierlicher Preisübernahme braucht es eine zulässige Datenquelle und Klärung der Nutzungsrechte.

**Nächste Priorisierung:** 1) ALDI SÜD (öffentliche dokumentierte Katalogsuche), 2) Kaufland K-SCAN-Download (Antwortmodelle und Session-Kontext), 3) Netto freie Suche vs. POS-Lookup, 4) REWE Shop-Katalog nur im zulässigen Zugangsrahmen, 5) EDEKA/PENNY offene Produktpfade.

## D. Entscheidender zusätzlicher GitHub-Fund: REWE stationäre Filialpreise

**Direkter Quellcode-Beleg:** [chukfinley/bismark](https://github.com/chukfinley/bismark) /
[bismark.py](https://github.com/chukfinley/bismark/blob/main/bismark.py).
Dieses unabhängige Open-Source-Projekt dokumentiert eine **andere Preis-API als die mTLS-geschützte REWE-App-/Liefer-API**:

```text
GET https://www.rewe.de/api/stationary-product-search/products
    ?query=<produkttext>&wwIdent=<marktID>
```

Der Projektcode wertet `products[].pricing.current`, `regular` und `refund` als **Centbeträge** aus. Er dokumentiert auch den Rückschluss `current < regular` als aktuell reduzierten Preis; das beschreibt eine Dateninterpretation, **nicht** einen durch uns selbst live bestätigten Preis.

**Unabhängiger APK-Beleg:** Im neuen eigenen Scan der realen REWE-APK `de.rewe.app.mobile` vom 31.10.2026 wurden sowohl der String-Pfad `/api/stationary-product-search` als auch `/api/stationary-product-search/{id}` gefunden. Das stützt die Existenz einer stationären Suchfunktion, belegt aber weder exakt dieselbe HTTP-Requestform noch Funktionsfähigkeit.

Das Open-Source-Projekt beschreibt, dass `wwIdent`-Marktkennungen aus REWE-Marktseiten bzw. offizieller `sitemap-maerkte.xml` stammen; dessen Stichprobe umfasst laut README 55 von 56 REWE-Märkten der Region Kiel. Diese Zahlen sind **Drittprojekt-Angaben, kein eigener Test**. REWE-/Nahkauf unterscheiden sich; eine solche Marktkennung ist kein Beweis für gleichen Preis im REWE-Liefershop oder alle aktuellen REWE-Filialen.

**Priorität stark erhöht:** REWE-Stationspreis-Endpunkt ist ein wesentlich besserer Kandidat für tatsächliche Ladenpreise als bisher nur die Liefershop-API. Vor einer produktiven Anbindung: aktuelle legale Erreichbarkeit, Rate Limits, Nutzungsbedingungen, Produktsortimentsumfang, Feldsemantik, fehlende Artikel, Paginierung und Reproduzierbarkeit an echten Kassenpreisen separat verifizieren. Keine Schutzmaßnahmen umgehen.

## E. Die nächste deutlich vollständigere statische Methode

Zusätzlich angelegt:
- [tools/retailer_full_retrofit_readonly.py](https://github.com/ecora2003-max/Try/blob/main/tools/retailer_full_retrofit_readonly.py)
- [GitHub-Actions-Workflow](https://github.com/ecora2003-max/Try/blob/main/.github/workflows/retailer-full-retrofit.yml)
- [Auswertungslauf](https://github.com/ecora2003-max/Try/actions/runs/41193283187)

Anders als die heuristische Suche nach API-Klassennamen enumeriert sie **alle in den DEX-Dateien enthaltenen Retrofit-Methodenannotationen**, einschließlich obfuskierter Klassen, und gibt ausschließlich Produkt-/Preis-/Store-/Katalog-GET/HEAD-Methoden als sichere Metadaten aus. Alle enthaltenen DEX-Dateien, einschließlich nichtkonfigurationsbezogener XAPK-Splits, werden geprüft. Ohne Authentifizierung, dynamischen Händlerverkehr oder Übernahme von Secrets.

**Bereits selbst nachgewiesenes Ergebnis dieser erweiterten Methode bei ALDI SÜD:**
- `GET v3/product-search` (Query `q, servicePoint, serviceType, categoryKey, limit, offset` u.a.)
- `GET v3/product-search-suggestion`
- `GET v2/product-category-tree`
- `GET v2/products` und `GET v2/products/{sku}`
- `GET v2/service-point-product-availability`
- `GET v2/barcode-mapping/{barcode}`
- `GET v1/stores`

Diese 8 Routen wurden durch **direkte Annotationsextraktion der aktuellen APK** bestätigt, nachdem die frühere Klassennamen-Heuristik **0** Treffer erzielt hatte. Das demonstriert, dass eine eingeschränkte Suche tatsächlich nutzbare Endpunkte übersehen kann. Es ist **kein Nachweis eines aktuellen Live-Preisabrufs**.

Für die übrigen Händler sind die vollständigen Ergebnisse nach Abschluss und Auswertung des gleichen GitHub-Actions-Laufs separat nachzutragen. Native Flutter/Hermes-Routen sind auch bei dieser umfassenderen DEX-Methode weiterhin nicht vollständig dekodierbar.
