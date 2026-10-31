# Netto: Verifizierter Onlinepreis als Alternative zur MPOS-Filialpreis-API
**Live-Test am 31.10.2026 um 13:32 UTC.**

## Ergebnis
**Ein aktueller, auf der offiziellen Netto-Seite gespeicherter Onlinepreis wurde erfolgreich ausgelesen.** Der Preis muss laut aktualisierter Zieldefinition nicht zwingend filialbezogen sein. Die vorher untersuchte MPOS-`itemInfo`-API ist **weiterhin nicht live nutzbar bestätigt**; beide Datenwege sind strikt zu unterscheiden.

### Tatsächlicher Testdatensatz

- **Netto-Produkt:** Kölln Haferflocken kernig 500 g, **10er-Pack** (5 kg insgesamt)
- **Netto-Angebotspreis (Onlineshop):** **16,90 €** für den 10er-Pack, rechnerisch **3,38 €/kg** beziehungsweise **1,69 € pro 500 g**; keine Aussage, dass 500-g-Einzelpackungen einzeln verkauft werden.
- **Artikelnummer/SKU:** `2162281000`.
- **GTIN:** `4000540200300` (aus offizieller eingebetteter Produktdatenstruktur; als GTIN des Onlineartikels behandeln, nicht automatisch der Einzelpackung).
- **Quelle:** [Offizielle Netto-Produktseite](https://www.netto-online.de/koelln-haferflocken-kernig-500-g-10er-pack/p-2162281000).
- **Preisobjekt:** `{"@type":"Offer","priceCurrency":"EUR","price":"16.90"}` in `application/ld+json`, eingebettet in `{"@type":"Product"}`.
- **Verfügbarkeit im Quellobjekt:** `https://schema.org/InStock`.
- **Marktbezug:** `NETTO_ONLINE_SHOP`, `store_id=null`, kein nachgewiesener Filialkassenpreis.
- **Testlauf:** [GitHub Actions 41205995579 – PASS](https://github.com/ecora2003-max/Try/actions/runs/41205995579); Ergebnis `LIVE_PRICE_CONFIRMED`, genau ein eindeutig zuordenbares numerisches EUR-Preisobjekt.

### Umsetzung im GitHub-Testrepository

- [`catalogues/netto_online.py`](../catalogues/netto_online.py): offline testbarer Parser für `Product`-JSON-LD/`Offer`, Name, SKU, GTIN, Marke, Preis in EUR, Verfügbarkeit. Explizite Kennzeichnung **Onlinepreis**, nicht Filialpreis.
- [`tools/netto_online_adapter_live_check.py`](../tools/netto_online_adapter_live_check.py): Live-Einzelartikelabruf über offizielle Produktseite und Parser-Kontrakttests (Fehlwährung, fehlerhafter Preis, falsche SKU, falsche Hostadresse).
- [`.github/workflows/netto-online-offer-adapter.yml`](../.github/workflows/netto-online-offer-adapter.yml): kostenlose GitHub-Actions-Validierung auf der bereits bekannten Netto-Produkt-URL.

**Wichtiges Parserdetail:** Die Produktseite enthält ein `application/ld+json`-Script, das unescapte Steuerzeichen im Schema-Text enthält. Bei `json.loads(strict=True)` scheiterte der Live-Test trotz tatsächlich vorhandener Preisangabe. Der Parser verwendet nun `json.loads(...,strict=False)`, **validiert aber weiterhin** ausdrücklich `@type=Product`, `@type=Offer`, `priceCurrency=EUR` und eine endliche nichtnegative Dezimalzahl; keinerlei Preis wird geraten. Der erneut ausgeführte Live-Test war erfolgreich.

### Verhältnis zur früheren `itemInfo`-Entdeckung

Die SDK-Typen sind weiterhin tatsächlich im Netto-App-Code nachgewiesen:
`MPOSApi.itemInfo` → `ItemInfoResponseItemInfo.ValidPrice.Amount/Currency`.
Aber **der bisher einzige echte GET-Test** gegen den vermuteten Host `app.netto-online.de` antwortete HTTP 200 mit HTML statt JSON; die wahre Produktivserveradresse ist nicht eindeutig gefunden. [Nachweis](netto-mpos-live-preis-test-2026-10-31.md). **Über `itemInfo` wurde weiterhin kein tatsächlicher Preis abgerufen.**

### Noch offen für die allgemeine Einkaufsliste

Der aktuelle Netto-Online-Parser akzeptiert **eine bekannte Produktdetail-URL**, nicht beliebige Suchbegriffe. Die automatische Entdeckung der passenden Produktseiten durch Netto-Suche, die Prüfung vergleichbarer Verpackungsgrößen und Versandkosten sind **noch nicht implementiert**. Dieser einzelne erfolgreiche Onlinepreis macht die generelle Produktsuche nicht vollständig produktionsreif. Außerdem kann das Online-Sortiment vom Regalangebot abweichen; ein Produkt, das ausschließlich in der Filiale angeboten wird, muss dort nicht vorhanden sein.

**Repositorygrenze:** Sämtliche Änderungen nur in `ecora2003-max/Try`; keine Änderung am Hauptrepository `Ernaerungsgedaechnis` oder Google Sheets.
