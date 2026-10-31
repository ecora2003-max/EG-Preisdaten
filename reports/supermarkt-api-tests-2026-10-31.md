# Angebots-APIs: reproduzierbarer Live-Test (31.10.2026)

## Ziel und Methode
Gezielte, schonende GET-/einzelne dokumentierte POST-Anfragen von einem **GitHub Actions Ubuntu-Runner** an öffentlich beschriebene Supermarkt-Angebotsendpunkte. Ohne Anmeldung, künstliche Browser-Identität, Captcha-Umgehung oder automatische Wiederholungen. Bei nicht abrufbarer `robots.txt` wurde ein API-Test vorsorglich ausgelassen. Nur Schema, Zählwerte und kurze Produktbeispiele werden gespeichert, nicht komplette Angebotsbestände.

**Wichtig:** HTTP 403 bei `robots.txt` beweist kein allgemeines API-Verbot; es verhindert hier lediglich eine vertretbare Freigabe für unseren schonenden Test. Ebenso belegt HTTP 200 keine rechtliche Nutzungslizenz.

- [Vollständiger letzter Händler-Test: Lauf 41181161800](https://github.com/ecora2003-max/Try/actions/runs/41181161800)
- [ALDI-Nord-Produkttest: Lauf 41181294112](https://github.com/ecora2003-max/Try/actions/runs/41181294112)
- [Prüfcode Händler](../tools/retailer_offers_probe.py)
- [Prüfcode ALDI Nord](../tools/aldi_nord_data_probe.py)

## Nachgewiesene Ergebnisse

| Anbieter | HTTP / Datentyp | Strukturierte Produkte | Folgewoche | Grenzen |
|---|---|---|---|---|
| **PENNY** | 200 JSON | Ja, `offerTiles` mit Preis, Menge, Vorteils- und Grundpreis | **Ja**, 2026-45 (02.11.) | Nur getestete Kategorie `top-angebote`; regionale Zuordnung und Preisbedingungen prüfen |
| **Kaufland** | 200 HTML mit JSON `offerData` | **Ja**, 2.098 Angebotsobjekte über zwei Zyklen | **Ja**, `salesFrom=2026-11-02` bei 753 Objekten; weitere am 09.11. | Allgemeine Seite; keine verifizierte einzelne Filiale, Datumskonflikte bei Einträgen |
| **ALDI Nord** | 200 HTML, eingebettetes `__NEXT_DATA__` | **Ja**, 276 Objekte in `algoliaDataMap` von `OFFER_GET` | **Ja**, explizites `week=next` | Nicht jede Produktkennung garantiert lieferbaren Aktionspreis |
| **Lidl** | 200 JSON für Filialverzeichnis | Angebots-API 400 (beide geprüften Store-Key-Formate) | Nicht bewiesen | 3.282 Filialen, darunter 144 mit `locality` Berlin; Datenmodell im Open Source dokumentiert |
| **REWE** | 403 auf Angebotsseite | Nicht direkt geprüft | Nicht geprüft | HTTP 403 in Testumgebung |
| **EDEKA** | `robots.txt` 403 | API-Test ausgelassen | Nicht geprüft | Öffentliche JSON-Endpunkte sind in Open Source dokumentiert, aber kein Live-Erfolg |
| **Netto Marken-Discount** | `robots.txt` 403 | API-Test ausgelassen | Nicht geprüft | Filialsuch-API im Quellcode dokumentiert, Angebots-API nicht bestätigt |
| **ALDI Süd** | `robots.txt` 403 | API-Test ausgelassen | Nicht geprüft | `v3/product-search` in Open Source dokumentiert, kein Live-Erfolg |

### PENNY: tatsächlich erhaltene strukturierte Produkte

Offizielle JSON-Routen mit einer aus dem Filialkatalog ermittelten Berliner `sellingRegion=15A-01-56`:
- `https://www.penny.de/.rest/offers/by-category/2026-44/top-angebote?region=15A-01-56` — HTTP 200, **9** Produktkacheln.
- `https://www.penny.de/.rest/offers/by-category/2026-45/top-angebote?region=15A-01-56` — HTTP 200, **9** Produktkacheln.

Für die Folgewoche enthält das erste geprüfte Objekt `title="LEERDAMMER Käsescheiben*"`, `quantity="je 140 g"`, `price="1.49"`, `listPrice="2.69"`, `advantage="44%"`, `basePrice="(1 kg = 10.64)"` und `benefitPrice="1.29²"`. Der Zusatzpreis trägt Fußnoten; ohne deren Bedingungen ist er **kein allgemein gültiger Kassenpreis**.

Für die aktuelle Woche enthielt das erste Objekt `title="PRINGLES*"`, `quantity="je 185 g"`, `price="1.69"`, `listPrice="2.79"`.

`offerTiles` enthält u. a. `title`, `quantity`, `price`, `listPrice`, `advantage`, `basePrice`, `benefitPrice`, `productData`, `uuid`.

### Kaufland: eingebettete Daten vollständig dekodiert

Die öffentlich erreichbare Vorschau `https://filiale.kaufland.de/angebote/naechste-woche.html` leitete auf `/angebote/uebersicht.html?kloffer-week=next` um und enthielt `offerData` mit **2** Zyklen und zusammen **2.098 Angebotsobjekten**.

Als `salesFrom` wurden u. a. 2026-11-02 (**753**) und 2026-11-09 (**125**) ermittelt. Produktobjekte besitzen `offerId`, `title`, `price`, `unit`, `dateFrom`, `dateTo`, `salesFrom`, `salesTo`.

**Warnung:** Bei Stichproben widersprachen sich `dateFrom/dateTo` und `salesFrom/salesTo`. Deshalb nicht allein nach Startdatum laden; erst Gültigkeitslogik, Filiale und Ausschlüsse validieren.

### ALDI Nord: `week=next` im eingebetteten JSON

`https://www.aldi-nord.de/angebote-vorschau.html` antwortete mit HTTP 200. Das Next.js-Attribut `props.pageProps.apiData` war eine JSON-kodierte Zeichenkette mit einem `OFFER_GET`-Datensatz. Sein Request enthielt `{"locale":"de","week":"next"}`, die Antwort `algoliaDataMap`, `categories` und `weekSwitchPer`.

`algoliaDataMap` enthielt **276** strukturierte Produktobjekte. Verifizierte Felder u. a. `name`, `brandName`, `currentPrice`, `promotionPrices`, `salesUnit`, `isAvailable`, `assets`, `objectID`; Beispielprodukt: **Erdnüsse**. Diese Felder wurden im tatsächlich geladenen JSON festgestellt, aber noch nicht für jede Produktgruppe semantisch validiert.

### Lidl, EDEKA, Netto und ALDI Süd

Lidl: `https://stores.lidlplus.com/api/v4/DE` lieferte 3.282 strukturierte Filialen (HTTP 200), davon 144 mit Stadtangabe Berlin. `https://offers.lidlplus.com/app/api/v4/DE/DE7434/offers` und `.../DE/7434/offers` antworteten beide HTTP 400. Es wurde nicht versucht, durch App-Identitätsvortäuschung oder Sicherheitsumgehung eine andere Antwort zu erzwingen.

Bei EDEKA, Netto Marken-Discount und ALDI Süd war `robots.txt` auf dem verwendeten Runner mit HTTP 403 nicht abrufbar. Die möglichen Angebotsendpunkte wurden daher **nicht** direkt aufgerufen; ihre Erreichbarkeit ist unbewiesen. REWE antwortete auf den Angebotsseitenabruf direkt mit HTTP 403.

## Empfehlung für Ernährungsgedächtnis

**Zuerst PENNY und ALDI Nord implementieren**, weil echte JSON-Produktdaten einschließlich der kommenden Woche vorliegen. **Kaufland** ist ein weiterer aussichtsreicher Kandidat, benötigt aber erst Filial- und Datumsvalidierung. Lidl benötigt Klärung der 400-Antwort; EDEKA, Netto, ALDI Süd und REWE einen regelkonformen, ausdrücklich erlaubten Zugangsweg beziehungsweise weitere Tests.

Die technischen Resultate belegen **keine Erlaubnis zur fortlaufenden automatisierten Übernahme oder Weiterveröffentlichung**. Für einen produktiven Datenservice sind Nutzungsbedingungen und erforderliche Datenrechte gesondert zu klären.

## Reproduktion

Auf GitHub im öffentlichen Repository **Try → Actions** den Workflow **Supermarket offer API verification (read-only)** oder **ALDI Nord embedded data verification** auswählen und über **Run workflow** einmalig starten. Die Aktionen speichern kurze JSON-Protokolle als GitHub-Artifacts (Aufbewahrung 7 Tage), und die Tests erscheinen vollständig in den jeweiligen Workflow-Logs. Keine Schlüssel, Login-Informationen oder Händler-App-Binaries erforderlich. Die beiden Skripte stehen unter `tools/`.
