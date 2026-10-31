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


## Abgleich mit aktuellem APK-Basis-Host (abgeschlossen)

[Zusätzlicher erfolgreicher GitHub-Actions-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41204272310) · [statischer Host-Finder](../tools/netto_mpos_base_host_resolve.py).

In allen neun Android-DEX-Bestandteilen wurden öffentliche Hostnamenskonstanten und die Retrofit-Konfigurationsklassen geprüft. **Ergebnis:** Der im APK sichtbare `MPOSApi`-Interface-Code enthält keinen festen API-Basis-Host. Die dekompilierten `ApiClient`-Klassen im untersuchten Satz zeigen ebenfalls keine auswertbare konkrete `mpos`-Basis-URL. Der generische OpenAPI-`ApiClient` ist unter den vermuteten Klassennamen nicht vorhanden. Die Produktionsadresse könnte über Laufzeitkonfiguration oder einen anderen Clientpfad eingespielt werden; das ist eine Hypothese, **kein Nachweis**.

Das APK enthält mehrere Netto-Hostnamen (darunter `app.netto-online.de` und `sia.netto-online.de`), aber keine nachgewiesene eindeutige Zuordnung zu `/api/v1/mpos/{storeId}/itemInfo`. Der Live-Aufruf an `app.netto-online.de` lieferte daher keinen Preis. **Keine weiteren nicht verifizierten Hosts auf Verdacht angesprochen.**

**Abschlussstatus:** `TEST_PERFORMED_NO_LIVE_PRICE`. Die Tatsache, dass die Datenstruktur `ValidPrice` existiert, darf nicht als bereits bestätigte öffentliche API-Erreichbarkeit behandelt werden.
