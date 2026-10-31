# EDEKA: einmaliger Vollpreiskatalog-Download – Ergebnis
**Prüfung am 31.10.2026, 12:33 UTC.**

## Ergebnis
**Kein vollständiger EDEKA-Filialpreiskatalog heruntergeladen.**
Es ließ sich kein einheitlicher, vollständig listenbarer API-Katalog mit tatsächlichen Preisen sämtlicher Artikel einer EDEKA-Filiale oder des gesamten EDEKA-Verbunds nachweisen. Deshalb wurde **keine irreführend als vollständig bezeichnete Preisdatei** ins GitHub-Repository geschrieben.

## Tatsächlich überprüfte Endpunkte (einmaliger eigener GitHub-Actions-Lauf)
[Erfolgreicher technischer Quelltest](https://github.com/ecora2003-max/Try/actions/runs/41201603492) · [Prüfcode](../tools/edeka_catalogue_source_probe.py) · Artefakt `edeka-catalogue-source-probe`.

| Quelle | HTTP | Beobachtung | Preisgesamtkatalog? |
|---|---:|---|---|
| `https://www.edeka.de/sortiment/4311596029167/` | 200 | Öffentliche EDEKA-Produktinformationsseite, kein Preis im getesteten HTML | **Nein** |
| `https://b2c-gw.api.edeka/` | 200 | Startseite des EDEKA B2C API Gateway V2; verweist für API-Zugang an EDEKA | **Kein auswertbarer Produktdaten-Endpunkt** |
| `https://www.edeka24.de/Lebensmittel/Fertiggerichte/` | 200 | Versandshop-Kategorieseite, mindestens 22 Produktkacheln und sichtbare Europreise | **Nur EDEKA24-Versandshop**, kein filialbezogener EDEKA-Kassenpreiskatalog |
| `https://www.edeka24.de/sitemap.xml` | 404 | Unter dieser Adresse keine zugängliche Sitemap | **Nein** |
| `https://www.edeka24.de/robots.txt` | 200 | Technisch erreichbar; kein Produktdaten-Export | **Nein** |

### Warum die Datei nicht einfach heruntergeladen werden kann
1. **Keine bundesweit einheitlichen EDEKA-Filialpreise.** Verkaufs- und Aktionspreise sind marktgebunden. Es müsste mindestens ein konkreter Markt oder ein konkretes Online-Sortiment festgelegt werden.
2. **Produkte und Preise liegen in getrennten Quellen.** Die öffentliche EDEKA-Produktstammseite enthält Produktdetails, aber keine vollständigen marktbezogenen Preise; die bereits aus der echten EDEKA-APK extrahierten `/v1/product/ean/{ean}`- und `/v3/offers/grouped`-Endpunkte bieten einen **Einzelartikel- bzw. Angebotszugang**, keinen nachgewiesenen gesamten Preiskatalog.
3. **EDEKA24 ist nicht identisch mit der stationären Filiale.** Dort sind Preise sichtbar, aber sie gelten für den deutschlandweiten Versandshop und ein anderes Sortiment. Eine EDEKA24-Datei würde den geforderten Filial-Preiskatalog nicht ersetzen.

### Nachvollziehbare weitere Recherche
- [ByteSizedMarius/edekompile](https://github.com/ByteSizedMarius/edekompile) bietet laut Quelltext Angebote/Marktsuche, jedoch keinen nachgewiesenen Gesamtpreisexport.
- [Quelloffene EDEKA-Angebots-API](https://github.com/VinceDerPrince/Edeka-API) beschreibt Wochenangebote, keinen Alltagsartikel-Vollkatalog.
- [EDEKA B2C Gateway](https://b2c-gw.api.edeka/) weist selbst auf einen separaten Zugang zum Gateway hin.
- [EDEKA24](https://www.edeka24.de/) bezeichnet sich als deutschlandweiter Versandhandel mit langlebigen Produkten.

## Konsequenz
Für den vereinbarten Zweck (möglichst alle Produkte **mit realen Filialpreisen**) ist ein **vollständiger einmaliger Download derzeit nicht möglich zu belegen**. Der einzig korrekt nachgewiesene Status ist `NOT_DOWNLOADED_NO_VERIFIED_FULL_PRICE_SOURCE`. Die Versuchsdaten und der Quelltest sind im Testrepository gesichert.

**Änderungen ausschließlich in `ecora2003-max/Try`**, keine Änderungen im Produktionsrepository oder in Google Sheets.
