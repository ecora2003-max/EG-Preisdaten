# Netto Marken-Discount: zusätzliche Preisquellen und funktionierende freie Produktsuche
**Prüftag:** 31.10.2026 (14:00–14:02 UTC). **Schreibziel ausschließlich `ecora2003-max/Try`.**

## Ergebnis: funktionierende Onlinesuche → Preis

**Erstmals wurde eine offizielle freitextbasierte Suche nach Artikeln und der direkte Abruf ihrer Netto-Onlinepreise gemeinsam verifiziert.** Die frühere Implementierung konnte Preise nur zu bereits bekannten Produkt-URLs holen; die neue Methode findet Produktseiten selbst.

### Konkreter Webshop-Endpunkt

Auf der offiziellen [Netto-Startseite](https://www.netto-online.de/) lautet die tatsächliche HTML-Suchformularaktion:

`GET https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPParametricSearch-SimpleOfferSearch?SearchTerm=Haferflocken`

- Dieser direkte GET lieferte HTTP **200** und **zwei echte Kölln-Haferflocken-Produktlinks**.
- `GET .../ViewMMPParametricSearch-Browse?SearchTerm=Haferflocken` lieferte dieselben zwei Produktlinks ebenfalls mit HTTP **200**.
- Die geratenen Varianten `/search?q=...` und `/search?query=...` lieferten dagegen HTTP **404**. Nur die **tatsächlich im HTML vorgefundene Formularaktion** ist als verifiziert zu behandeln.
- Auf Produktdetailseiten steht der Preis im `application/ld+json`-Objekt mit `@type:Product` und `offers.@type:Offer` sowie `priceCurrency:EUR`. Der bereits [live validierte Python-Parser](../catalogues/netto_online.py) prüft numerischen Europreis, Produktname, SKU und GTIN.
- Die Suche liefert **Onlineshop-Produkte und Onlinepreise**, nicht notwendigerweise Einzelpackungen einer Filiale; beim Preisvergleich immer den ganzen 10er-/25er-Pack und den Kilopreis separat betrachten.

### Live-Test: drei Freitextbegriffe

[Erfolgreicher End-to-End-GitHub-Actions-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41208278315) · [Ausführbarer Prüfer](../tools/netto_search_to_online_price.py)

| Freitextsuche | Suchergebnis-Produktlinks | Aufgerufene Produktseiten | Seiten mit maschinenlesbarem EUR-Preis |
|---|---:|---:|---:|
| Haferflocken | 2 | 2 | **1** |
| Mandeln | 10 | 5 | **5** |
| Reis | 10 | 5 | **3** |
| **Summe** | **22** | **12** | **9** |

Beispielpreise aus Live-Test (ohne Versand):
- **Kölln Haferflocken kernig 10×500g: 16,90 €** für 5 kg (3,38 €/kg).
- **Backfee Mandeln gehackt 25×100g: 31,25 €** für 2,5 kg (12,50 €/kg).
- **Clarkys Mandeln blanchiert 10×200g: 34,90 €** für 2 kg (17,45 €/kg).
- **reis-fit Natur Reis 7×1kg: 20,93 €** für 7 kg (2,99 €/kg).
- **reis-fit Langkornreis 8 Minuten 16×500g: 31,84 €** für 8 kg (3,98 €/kg).

Die übrigen drei der zwölf untersuchten Produktseiten ergaben im aktuellen Parser keinen eindeutig akzeptierten `Product/Offer`-Datensatz. Das ist **kein Nachweis**, dass Netto auf diesen Seiten keinen angezeigten Preis hat; ein HTML-Layout-/Parser-Fallback wäre noch zu prüfen.

### Weitere untersuchte Quellen

1. **Dauerhafte Preissenkungen:** Netto veröffentlicht auf der offiziellen Seite [Dauerhafte Preissenkung](https://www.netto-online.de/ueber-netto/Preissenkung.chtm) derzeit nach Daten gruppierte Preissenkungen, u. a. 26., 23. und 19.10.2026. Die Seite lieferte im GitHub-Test HTTP 200. **Allerdings:** im untersuchten HTML keine normalen Produktkacheln, Preisfelder oder Produktlinks; Preissenkungsinformationen liegen offensichtlich in einem anderen Präsentationsformat. Kein strukturierter Datenfeed bestätigt. [HTML-Inspektion](https://github.com/ecora2003-max/Try/actions/runs/41208089259).
2. **Öffentliche Filial- und Wochenangebote:** der bereits implementierte [Netto-Filialangebotsparser](../catalogues/netto_branch_offers.py) hat früher **24/24** sichtbare Aktionskacheln mit Preisen und Artikelkennungen verarbeitet. [Erfolgreicher Live-Test](https://github.com/ecora2003-max/Try/actions/runs/41207688887). Nur **Aktionen**, nicht reguläres Alltags-Vollsortiment.
3. **Netto+-Preisscanner:** laut offizieller [Netto+-App-Beschreibung](https://apps.apple.com/de/app/netto/id1216226806) zeigt der Barcode-Scanner Preise direkt im Markt. Aus der aktuellen APK sind `GET api/v1/mpos/{storeId}/itemInfo?itemEAN=...` und das Antwortmodell `ValidPrice.Amount/Currency` statisch belegt. Der bisherige echte GET-Test an einem vermuteten Host lieferte **nur HTML statt JSON**; kein freier Live-Preiszugang bestätigt. [Bericht](netto-mpos-live-preis-test-2026-10-31.md).
4. **Prospekt und Preis-Checker:** Netto veröffentlicht weitere Einzelartikel-Aktionspreise und teils ältere Vergleichspreise. Sie sind nur für die jeweils beworbene Aktion zu werten, nicht als aktueller universeller Normalpreis.

### Konsequenz für die Einkaufsliste

**Verifizierter Datenweg:** `einkaufsbegriff → offizielles Intershop-SearchTerm → Produktlinks → offizielle Netto-Produktseiten → numerischer EUR-Angebotspreis`.

Der Weg ist kostenlos über Standard-HTTP-GET nutzbar und wurde empirisch getestet; ob eine generelle, dauerhaft robuste Implementierung möglich ist, hängt vom Shop-Aufbau und der Einzelartikel-Abdeckung ab. Im Test konnten **9 von 12** Detailseiten geparst werden. Nicht abgebildete Filialprodukte, Packungsgrößen, Versandkosten und fehlende Lieferfähigkeit müssen ausdrücklich kenntlich bleiben.

**Wichtig:** Die 9 Preisobjekte beweisen Netto-*Online*-Produktpreise, nicht tatsächliche Kassenpreise. Kein Live-Preisabruf über `mpos.itemInfo` wurde in dieser Fortsetzung bestätigt.

## Reproduzierbarkeit

- [Untersuchung des echten Suchformulars](https://github.com/ecora2003-max/Try/actions/runs/41208177965) (Resultat als Workflow-Artefakt).
- [Vollständiger 3-Begriffe-Such-/Preistest](https://github.com/ecora2003-max/Try/actions/runs/41208278315).
- [`tools/netto_more_price_sources.py`](../tools/netto_more_price_sources.py), [`tools/netto_search_to_online_price.py`](../tools/netto_search_to_online_price.py), [`catalogues/netto_online.py`](../catalogues/netto_online.py).

**Keine Änderungen in `ecora2003-max/Ernaerungsgedaechnis` oder der Google-Sheets-Datenbasis.**
