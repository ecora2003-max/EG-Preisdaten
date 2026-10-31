# Netto Marken-Discount: Gezielte Produktsuche und reale Filialpreise – Test 31.10.2026

**Ziel:** Für ein Einkaufsprodukt per Text oder EAN den aktuellen Filialpreis suchen. Ein Vollsortiment-Download ist dafür ausdrücklich nicht nötig.

## Statisch nachgewiesene Netto-App-Schnittstellen

Aus der realen Android-App `com.valuephone.vpnetto` und ihren DEX-/Retrofit-Annotationen:

| Retrofit GET | Parameter | Rolle |
|---|---|---|
| `rest/api/v2/productSearch` | `searchString`, `storeId` | Textsuche für ausgewählten Markt; Preisinhalt noch unbewiesen |
| `rest/api/v2/productScan` | `ean`, `listUUID`, `storeId` | Barcode-Suche; mögliche Bindung an Liste |
| `rest/api/v2/categoryList` | – | Produktkategorien |
| `api/v1/mpos/{storeId}/itemInfo` | `itemEAN`, `allRelatedItems` | Filialbezogener POS-Artikelabruf; keine anonyme Preisabfrage bestätigt |

Die beiden Produkt-API-Familien `ProductAPIApi` und `MPOSApi` sind in der aktuellen APK vorhanden. Die statische Untersuchung bestätigt **Methoden, aber keine erfolgreichen Preisserverantworten**.

## Zusätzliche tatsächlich durchgeführte Prüfung

**[Netto-App-Host-/Modell-Analyse](https://github.com/ecora2003-max/Try/actions/runs/41202181244)**:

- Alle neun DEX-Dateien der App, öffentliches Paket-SHA-256 `eab697ef54d3d236f92578b6c65d327f208a8c115b6a89d7ae94ff281cd1e51e`.
- `ProductAPIApi` tatsächlich als Retrofit-Interface bestätigt.
- `org.openapitools.client.models.ProductSearchResponse` im generierten App-Code mit JSON-Feldern `message`, `result` und `returnCode`; eine Klasse dieser Art allein belegt keinen **numerischen Verkaufspreis**.
- Die APK enthält Netto-Hostnamen wie `app.netto-online.de`, `www.netto-online.de` und `sia.netto-online.de`. Eine eindeutige Abbildung **genau der Produktsuch-Route auf ihren produktiven Basis-Host** wurde dadurch noch nicht erreicht.

**[Anonymer Live-Suchtest](https://github.com/ecora2003-max/Try/actions/runs/41202237702)**, `GET rest/api/v2/productSearch?searchString=Haferflocken&storeId=7679`:

| Erprobter Host | Beobachtung |
|---|---|
| `app.netto-online.de` | HTTP 200, aber **HTML-Seite** und kein Preis-JSON |
| `www.netto-online.de` | Nicht als API getestet, weil Vorabprüfung technische HTTP 403 bei `robots.txt` ergab |
| `sia.netto-online.de` | Keine Suche ausgeführt, weil Crawler-Zugriff auf diesen Pfad verneint wurde |

Damit **bislang 0 nachgewiesene aktuelle Netto-Filialpreise über `productSearch`**. Ein HTTP 200 mit HTML ist keine erfolgreiche API-Antwort.

## Auftragsstatus

`PRODUCT_SEARCH_METHOD_CONFIRMED / LIVE_PRICE_NOT_YET_VERIFIED`

**Weitere technische Aufgabe:** Den vom Retrofit-Client tatsächlich verwendeten Basis-Host anhand der App-Service-Initialisierung bestimmen. Danach mit einer einzigen echten Markt-ID-Suche das **JSON-Produktschema und die Preisfelder** validieren. Ohne bestätigte Preisdaten ist ein Preisvergleichsadapter noch nicht produktionsreif.

**Änderungen nur in `ecora2003-max/Try`. Das Hauptrepository blieb unverändert.**
