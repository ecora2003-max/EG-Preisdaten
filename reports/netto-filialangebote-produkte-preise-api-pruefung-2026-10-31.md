# Netto Filialangebote: maschinenlesbare Aktionsartikel und Preisabgleich

**Prüfung:** 31.10.2026, ca. 13:45–13:55 UTC. **Ziel:** Die vom Nutzer verlinkte [Filialangebote-Seite](https://www.netto-online.de/filialangebote) und ihre angebotenen Produkte als Preisvergleichsquelle erschließen. Kein Gesamtpreiskatalog nötig.

## Ergebnis: 24/24 Filialangebote mit numerischen Preiswerten technisch verifiziert

- Direkter HTTP-GET auf `/filialangebote` und auf zwei Varianten mit `?stores_id=7679` beziehungsweise `?stores_id=8135`: **HTTP 403 aus GitHub Actions**. Keine Zugangssperre umgangen.
- Offizielle alternative, **erfolgreich lesbare** Webseiten:
  - [`/angebote/c-N07`](https://www.netto-online.de/angebote/c-N07)
  - [`/lebensmittel-angebote/c-N07941`](https://www.netto-online.de/lebensmittel-angebote/c-N07941)
- Beide Seiten enthielten einen identischen `Filial-Angebote`-Bereich: **24 `tc-store-product-tile`-Kacheln**, davon **24 verschiedene `data-ff-id`-Kennungen**, **24/24 Aktionspreise durch zwei voneinander unabhängige Darstellungen je Kachel abgeglichen** (sichtbares Preiselement und Preis im kodierten Produktlink).
- **Vier** der 24 Kacheln zeigten außerdem einen gesondert gekennzeichneten App-Preis; diese Preisart wurde nicht als regulärer, allgemein verfügbarer Verkaufspreis übernommen.
- Der Seitenkopf nennt **Montag 26.10.2026 bis Samstag 31.10.2026**. Die zugehörigen internen Angebotslinks tragen außerdem `ValidTo=2026-10-31 20:00:00`; die Bedeutung des Zeitpunkts als tatsächlicher Ablauf oder lediglich Wishlist-Grenze ist **nicht unabhängig bestätigt**.

### Stichproben, direkt aus Nettos HTML auf dem Prüfdatum

| Netto-Kachel | Angebotsartikel-Kennung `data-ff-id` | Allgemeiner veröffentlichter Aktionspreis | App-Preis separat |
|---|---|---:|---:|
| Gurken | `46150` | 0,89 € | — |
| Grünländer Scheiben | `452955` | 1,69 € | 1,49 € |
| Zewa Toilettenpapier | `838564` | 6,99 € | — |
| Coca-Cola oder Zero | `454229` | 1,29 € | — |
| Möhren | `45544` | 1,19 € | — |
| Speisekartoffeln | `45099` | 2,99 € | — |

**Prüfnachweis:** [GitHub-Actions-Lauf 41207688887 – PASS](https://github.com/ecora2003-max/Try/actions/runs/41207688887), Ergebnisartefakt `netto-validated-branch-offers`. Der Test erfasst in beiden erfolgreichen Seiten jeweils 24 von 24 Kacheln, erkennt vier Apppreise und findet insgesamt 24 verschiedene IDs. Die Testdaten wurden tatsächlich heruntergeladen und geprüft, nicht geratet.

## Wie der Datenpfad technisch aussieht

1. Die öffentliche Netto-Kategorieseite liefert die Aktionskarten **bereits im serverseitig ausgelieferten HTML**. Eigene Ajax-API nicht erforderlich.
2. `<div class="tc-store-product-tile" data-ff-id="46150">...` enthält Name, Packungsinformation sowie `.grid-top-price .product__current-price.tc-product-price`.
3. Jede Kachel besitzt einen Link mit Route `ViewMMPWishlist-AddStoreArticle`. In dessen URL-Parametern stehen `SKU`, `Name`, `Price`, `BasePrice`, `ValidTo` sowie weitere Darstellungsfelder. Beispielsweise nach dem URL-Dekodieren `SKU=46150; Name=Gurken; Price=0.89; ValidTo=2026-10-31 20:00:00`.
4. **Wichtig:** `ViewMMPWishlist-AddStoreArticle` ist eine **Wunschlistenaktion mit potenzieller Zustandsänderung**, keine geeignete reine Preis-API. Der Endpunkt wurde **nicht aufgerufen**. Das Skript liest ausschließlich die bereits öffentlich im HTML enthaltenen Link-Parameter und vergleicht sie mit dem sichtbaren Preis.
5. Die ebenfalls im HTML referenzierte Route `Offers-GetStoreNavigationLayerContent` betrifft die Angebotsnavigation. Sie ist **nicht** als Produktpreis-Endpunkt nachgewiesen. Die offizielle `theme.min.js` wurde einmalig auf erkennbare interne Routen durchsucht; kein eindeutig identifizierter anonymer Nur-Lese-JSON-Endpunkt für sämtliche Filialprodukte.

## Implementierung im isolierten Testrepository

- [`catalogues/netto_branch_offers.py`](../catalogues/netto_branch_offers.py): Parser, erkennt ausschließlich `Filial-Angebote`-Kacheln; validiert Produktkennung, Namen, öffentlich angezeigten Aktionspreis und URL-`Price`, separiert Apppreis, hält Quelle und Gültigkeitsangaben.
- [`tools/netto_branch_offers_live_check.py`](../tools/netto_branch_offers_live_check.py): offline Kontrakttest und zwei echte HTTP-Preisquellen; meldet unvollständige oder widersprüchliche Kacheln als Fehler.
- [`.github/workflows/netto-branch-offers-validate.yml`](../.github/workflows/netto-branch-offers-validate.yml): kostenloser manuell/bei Code-Änderung startbarer Test, keine zyklische Hintergrundüberwachung.
- [`tools/netto_offer_markup_and_js_paths.py`](../tools/netto_offer_markup_and_js_paths.py) und [`tools/netto_store_offer_dom_schema.py`](../tools/netto_store_offer_dom_schema.py): Belege zur tatsächlichen HTML-Struktur und zur Trennung von App-/Werbe- und Produktpreisen.

## Was damit noch NICHT nachgewiesen ist

- **Nicht der vollständige normale Nettokatalog.** Die bestätigten 24 Angebote sind ein Teil der veröffentlichten **Wochenaktionen**; eine beliebige Produktsuche mit regulären Filialpreisen wird damit noch nicht bereitgestellt.
- **Keine konkreten Filialpreise bestätigt.** Ohne wirksam ausgewählte Filiale sind die Daten als **allgemein veröffentlichte Netto-Filialangebote** zu kennzeichnen; regionale Verfügbarkeit und abweichende Aktionsbedingungen möglich.
- **Keine dauerhafte Preisgültigkeit.** Diese Stichprobe gilt laut Website nur vom 26. bis 31.10.2026. Nach diesem Zeitraum müssen die Seiten erneut geprüft und nicht einfach die alten Zahlen verwendet werden.
- **Keine Belege, dass `ViewMMPWishlist-AddStoreArticle` eine rein lesende API ist.** Es wäre fachlich falsch, diesen Link als Preisschnittstelle abzufragen.

**Arbeitsstatus:** `PUBLIC_NETTO_BRANCH_OFFER_PRICES_VALIDATED_24_OF_24`, die alternative allgemeine Produktsuche/POS-Kassen-API bleibt `NOT_VERIFIED`.

Änderungen ausschließlich in `ecora2003-max/Try`; Hauptrepository und Google Sheets unverändert.
