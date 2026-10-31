# Recherchefortsetzung: tatsächliche Filialpreiskataloge – 31. Oktober 2026

**Ziel:** Nicht nur Werbeaktionen, sondern echte aktuell angezeigte Preise des möglichst kompletten Sortimentes einer konkreten Filiale. Kein kostenpflichtiger API-Dienst und keine Nutzung fremder Zugangsdaten.

## Neue Tests

### EDEKA: zwei eigenständige Online-Marktshops

Aus öffentlichen GitHub-Projekten stammen konkrete OXID-Shopadressen zweier Händler mit Produktsuche:

- `seidl-kulmbach.edeka.shop` – Referenz: [castellco/superscraper](https://github.com/castellco/superscraper).
- `ec-offenburg.edeka.shop` – Referenz: [InesZenkri/BlackForest24](https://github.com/InesZenkri/BlackForest24).

Das neue [GitHub-Experiment](https://github.com/ecora2003-max/Try/actions/runs/41189405612) testete je eine anonyme Produktsuche nach „Milch“, **ohne fremde Session-Tokens**, und prüfte zuerst die jeweiligen robots-Regeln. Beide Zugriffe mussten wegen nicht zuverlässig verfügbarer/ablehnender robots-Regeln **ausgelassen** werden; **kein** aktueller Preis wurde live abgerufen.

Der in einem alten Open-Source-Projekt gespeicherte Preis ist **kein aktueller Filialpreis**. Zudem können die Shops Online- bzw. Lieferpreise statt Ladenkassenpreise zeigen. Diese Quelle ist daher **nicht als Produktivlösung verifiziert**. EDEKA.de-Nutzungsbedingungen bleiben zusätzlich zu beachten.

### Netto Marken-Discount: wichtiger Identitätsfehler in bestehenden Spuren

**Es gibt zwei verschiedene und voneinander unabhängige Netto-Ketten:**

1. **Netto Marken-Discount** (rot-gelb, EDEKA-Gruppe, `netto-online.de`): Gemeint ist **dieser** Händler in unserer sechs-Händler-Analyse. [Original-Netto-Marken-App-Nutzungsbedingungen](https://sso.netto-online.de/oauth/account/consent?key=nutzungsbedingungen-netto-app) besagen, dass Scan&Go nur in ausgewählten Filialen mit aktivierter Standortermittlung und zum jeweiligen Markt passenden Preisen funktioniert.
2. **Netto mit Scottie-Hund** (schwarz-gelb, Salling Group, `netto.de`): **Ein anderer Händler** mit anderer App und anderen Daten. [Offizielle Klarstellung](https://service.netto.de/hc/de/articles/360016594598-Was-ist-der-Unterschied-zwischen-Netto-und-Netto-Marken-Discount).

**Korrektur zu älteren Forschungshinweisen:** Der `Netto+`-Preisscanner unter `netto.de` belegt **keinen** Preiszugang für Netto Marken-Discount. Belege und künftige Adapter strikt an die Händleridentität binden. Der unabhängig zuvor nachgewiesene **Netto-Marken-Prospektzugriff** auf `netto-online.de` und `wochenprospekt.netto-online.de` bleibt bestehen, ist aber kein normaler Vollpreiskatalog.

### PENNY: Scan&Go kann nicht ohne Filialkontext als offene Preisliste gelten

Die [PENNY-AGB](https://www.penny.de/datenschutz/agbs-scan-and-go) schreiben zur Nutzung im Laden vor, sich per Bluetooth oder mit einem Markt-QR-Code zu verbinden und Produkte einzeln zu scannen. Die offizielle Preisabfrage ist damit **nicht als öffentlich listenbare Gesamtsortiment-API** nachgewiesen. Ein aktuell gepflegtes [Home-Assistant-Projekt ha-penny](https://github.com/FaserF/ha-penny) dokumentiert Konto-/eBon-/Filialendpunkte, aber keine vollständige Produktpreisabfrage. Die bereits im Projekt per Live-Test bestätigten **regionalen PENNY-Angebots-Endpunkte** ändern daran nichts.

### Kaufland: offizielle Scan-Funktion nicht mit offenen Marktdaten verwechseln

Nach [Kaufland-FAQ](https://filiale.kaufland.de/service/haeufige-fragen.html) benötigt Kaufland Scan eine Kaufland Card XTRA und funktioniert in ausgewählten Märkten; Artikel werden einzeln gescannt. Deshalb ist der existierende Scanner **keine nachgewiesene anonyme Bulk-Preisliste**. Die Kaufland-Seller-API und öffentlich zugängliche `kaufland.de`-Produkt-Scraper liefern Marktplatz-Verkäuferpreise, nicht die realen Filial-Regalpreise. Die bestätigten Kaufland-Filialangebote sind separat nutzbar.

### Offene Preisvergleichsdienste: kein Ersatz für einen POS-Preiskatalog

- [smhaggle-Hilfe](https://smhaggle.com/hilfe/) erklärt, dass die Preise hauptsächlich aus fotografierten **Kassenbons von Nutzern** gewonnen werden. Dadurch gibt es weder automatisch tagesaktuelle Preise noch garantierte Vollständigkeit je Filiale.
- [Allelebensmittel Shopping API](https://cfw.allelebensmittel.de/agents) betrifft **Preise aus Online-Shops** und stellt ausdrücklich keine allgemeine Bulk-Export-API dar.
- KaufDA/Marktguru-Prospekte sind Angebote, keine regulären Vollsortimentspreise; Drittanbieter-Nutzungsrechte separat zu prüfen.

## Kumulierte technische Bewertung (weiterhin gültig)

| Händler | Aktueller Produktpreiskatalog bewiesen | Filialgenauigkeit | Vollständige Gesamtabdeckung |
|---|---|---|---|
| Lidl | **Ja:** öffentliche Produktkatalog-GETs mit Normal-/angezeigten Preisen, Rabatten, Kategorien, Unterkategorien und Produktdetails | **Direkter storeKey** | Noch nicht alle Kategorien/Seiten verifiziert |
| ALDI Nord | **Ja:** in fünf Kategorien insgesamt **164/164** bepreiste Produktdatensätze | Individueller Marktfilter fehlt | Nicht nachgewiesen |
| PENNY | Nur Angebotskatalog | Region für Angebote | **Kein** Vollpreiskatalog nachgewiesen |
| Kaufland | Nur Angebotskatalog | Konkreter Markt für Angebote | **Kein** Vollpreiskatalog nachgewiesen |
| Netto Marken-Discount | Offizieller Filialprospekt, kein regulärer Preisfeed | Prospekt mit tatsächlicher Markt-ID | **Kein** Vollpreiskatalog nachgewiesen |
| EDEKA | Markt-Angebote zuvor technisch getestet; unabhängige Online-Shop-Preisquellen als Ansatz, im aktuellen Test nicht zugänglich | Abhängig vom Marktshop | **Kein** Vollpreiskatalog nachgewiesen; Nutzungsbedingungen beachten |

**Bewertung:** In dieser Recherche- und Testrunde wurde kein zusätzlicher sechs-Händler-Vollpreiskatalog freigeschaltet. Die erfolgreichen Lidl-/ALDI-Tests bleiben als separate Nachweise bestehen. **Zugriff auf echte Einzelpreise ≠ Enumerierbarkeit des gesamten POS-Katalogs ≠ Nutzungsfreigabe.**

Alle neuen Dateien und GitHub Actions liegen ausschließlich in `ecora2003-max/Try`. Das Repository `ecora2003-max/Ernaerungsgedaechnis` wurde weder beschrieben noch für Experimente verwendet.
