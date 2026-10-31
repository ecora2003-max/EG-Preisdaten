# Netto Marken-Discount: echter Live-Preistest des MPOS-Endpoints
**Testtag:** 31.10.2026 · **Messung:** 13:10:51 UTC.

## Tatsächlich durchgeführte HTTP-Anfrage

[Erfolgreich ausgeführter GitHub-Actions-Test](https://github.com/ecora2003-max/Try/actions/runs/41204386410) · [Testskript](../tools/netto_mpos_live_price_test.py)

- **Methode:** anonymes GET, nur Lesezugriff.
- **Getesteter öffentlicher Netto-Hostname:** `app.netto-online.de` (aus Netto-APK-Hostname-Kandidaten; Zugehörigkeit zur MPOS-API selbst nicht bewiesen).
- **Endpunkt:** `/api/v1/mpos/7679/itemInfo`.
- **Parameter:** `itemEAN=4316268677943` (bei Netto gelistete laktosefreie H-Milch 1,5 %) und `allRelatedItems=false`.
- **robots-Prüfung:** `ALLOW`.
- **HTTP-Status:** **200**, aber **`Content-Type: text/html; charset=UTF-8`**.
- **Payload:** HTML statt des erwarteten `ItemInfoResponse`-JSON.
- **Ergebnis:** `NON_JSON_RESPONSE`, `price_verified=false`; **kein tatsächlicher Filialpreis** ermittelt.

## Warum das kein Erfolg ist

Ein erfolgreicher HTTP-Status allein ist keine funktionierende Preis-API. `app.netto-online.de` liefert hier offenbar die HTML-Webapp (oder eine vergleichbare HTML-Rückgabe) und **nicht** den Netto-POS-Service. Die statische App-Klasse `org.openapitools.client.apis.MPOSApi` enthält zwar `GET api/v1/mpos/{storeId}/itemInfo`, der generierte Rückgabetyp `ItemInfoResponseItemInfo` hat `ValidPrice` und der Typ `ValidPrice` enthält `Amount` und `Currency`; dies beweist lediglich, dass **das App-SDK für diese Preisantwort vorgesehen ist**.

## Bereits bestätigter Status

- **Preissuche technisch entworfen:** `productSearch(searchString,storeId)` → `Product[]` (EAN und Produktname, aber ohne Preis).
- **POS-Preisantworttyp statisch bestätigt:** `itemInfo` → `ItemInfo[].ValidPrice.Amount/Currency`.
- **Abfrage einer konkreten EAN aus einer echten Netto-Filiale:** über den hier getesteten öffentlichen Host **nicht erfolgreich**.
- **Noch nicht geklärt:** der echte Produktions-Basis-Host, eventuell erforderliche App-/Filialsitzung, Erreichbarkeit des Services ohne Authentifizierung, Aktualität und Abweichung zum tatsächlichen Kassenpreis.

Keine Login-/Zahlungs-/Warenkorbmethoden aufgerufen; keine Sperre umgangen, keine Kundendaten verarbeitet.

**Fazit:** Ein aktueller Netto-Filialpreis ist durch diesen Test **nicht nachgewiesen**. Der nächste sinnvolle technische Schritt ist die eindeutige Zuordnung der `MPOSApi` zur verwendeten Basis-URL anhand des App-Initialisierungscodes statt beliebiger URL-Kombinationen.

**Ablage:** ausschließlich `ecora2003-max/Try`. Hauptrepository unverändert.
