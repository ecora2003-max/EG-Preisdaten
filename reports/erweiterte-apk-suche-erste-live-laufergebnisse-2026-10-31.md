# Ergebnisse der erweiterten API-Suche: tatsächliche statische APK-Läufe

Stand: 31.10.2026. [Neuer GitHub-Actions-Lauf](https://github.com/ecora2003-max/Try/actions/runs/41192568816) mit sechs abgeschlossenen App-Analysen; Kaufland läuft zum Zeitpunkt dieser Auswertung noch.

Alle Ergebnisse beruhen auf temporär heruntergeladenen APK/XAPK-Paketen und **statischer Auswertung**, nicht auf Händler-HTTP-Liveabfragen.
Zugriffsberechtigungen, nutzbare reale Filialpreise und Vollständigkeit wurden **nicht** nachgewiesen.

| App | App-Paket | APK gelesen / JADX | Neue/präzisierte Hinweise | Bewertung |
|---|---|---|---|---|
| REWE | `de.rewe.app.mobile` | Ja; 9 Klassen untersucht | In der aktuellen APK als reine Pfadkonstante gefunden: **`/api/stationary-product-search` und `/api/stationary-product-search/{id}`**; außerdem `/api/products`, `/api/grocerysearch`, `mobile-clients-api.rewe.de` | **Wichtiger bislang nicht priorisierter Hinweis auf stationäre Produktsuche**, aber kein HTTP-Methoden- oder Preisbeleg zu dieser Route und keine Aussage über Login/mTLS. |
| Netto Marken-Discount | `com.valuephone.vpnetto` | Ja; 10 von 12 priorisierten Klassen | In `ProductAPIApi` jetzt erneut echte Retrofit-`GET`-Annotationen `rest/api/v2/productSearch`, `productScan`, `categoryList` bestätigt; `OfferServiceApi` bietet `GET rest/v4/offers`, `GET rest/v4/offers/leaflets`; StoresApi mit `api/v1/stores` | Produktnachrichten bleiben ohne bestätigte Rückgabepreise / zulässige Live-API-Zugriffe. |
| ALDI SÜD | `de.apptiv.business.android.aldi_de` | APK statisch gesichtet; **0** per Klassennamen-Heuristik ausgewählte Retrofit-Interfaces | Reale Hostkonstanten u.a. `api.aldi-sued.de` und `asl.api.aldi-sued.de`, Preis-Datentyp `ProductPriceDto`; extern [`aldiscount`](https://github.com/ByteSizedMarius/aldiscount) dokumentiert Freitextsuche, Kategorien und Filialauswahl | Kein Negativnachweis: 0 ausgewählte Klassen bedeutet lediglich heuristische Fehl-/Untererkennung, **nicht** dass keine API existiert. |
| EDEKA | `de.edeka.genuss` | Ja; 10 von 16 ausgewählten Klassen | `OfferApi` bestätigt Retrofit-`GET v2/catalogues` und `GET /v3/offers/grouped`. EAN-/Valuephone-Pfade in früherem Lauf gefunden. | Kein neuer freigegebener vollständiger Filialpreis-Katalog. AGB-Schranken beachten. |
| PENNY Kundenapp | `de.penny.app` | APK statisch gesichtet; 0 heuristisch ausgewählte Klassen | Firestore-bezogene Angebot-/Marktmodelle und `app.penny.de`, `account.penny.de` | Keine passende Katalogmethode nachgewiesen; Heuristik nicht erschöpfend. |
| PENNY Scan&Go | `de.penny.scango` | Ja; eine Kandidatenklasse dekompiliert | Host `scanandgo-p.rewe-group.com`, `PromotionsApi` ohne durch den Filter identifizierte passende Produkt-GET-Methode | Weiterhin keine belegte freie Vollsortiments- oder Preis-API. |

## Methoden- und Datenqualität

- Open-Source-Herkunft der erfolgreichen Lidl-API-Suche: [hakimarun/lidl-plus-api](https://github.com/hakimarun/lidl-plus-api), statische JADX-Dekompilierung + Hermes-v96-Stringparser, laut Doku 343 Retrofit-Endpunkte / 117 Interfaces; **ohne** Live-Validierung durch den Drittentwickler.
- Neues Skript [`broader_apk_discovery.py`](../tools/broader_apk_discovery.py) verallgemeinert APK-Stringsuche und **entdeckt Kandidatenklassen anhand der tatsächlich vorhandenen DEX-Klassennamen**, statt nur vier bekannte Klassennamen abzufragen.
- Je App werden maximal **10** priorisierte Klassen mit JADX untersucht. Die Kandidatenfindung über Klassennamen erkennt manche obfuskierten Methoden/Flutter-/Hermes-Strings nicht. Folglich **noch keine vollständige** Enumeration aller Retrofit-Annotationen und **keine vollständige Hermes-Bytecode-Rekonstruktion**.
- Die Strings `stationary-product-search` stammen bei REWE aus der **realen APK**, aber keine Live-Suchantwort und keine bekannte Autorisierung dazu. Sie dürfen nicht als funktionierende API verkauft werden.
- Die EDEKA-APK-Daten wurden nur statisch ausgewertet. Keine erneute automatisierte Abfrage von EDEKA-Servern.
- Die APKPure-Quellen sind Drittanbieterpakete. SHA-256 des tatsächlich bezogenen Containers liegt je Artefakt vor; Original-Herausgeber-Signaturen wurden nicht separat geprüft.
- Alle Händlerendpunkte werden nur **als unbestätigte Kandidaten** behandelt, bis zulässige Live-Verifikation inklusive Preisfeld, Store-ID-Geltung und Paginierung erfolgt.

## Weitere Open-Source-Hinweise

**REWE:** [ByteSizedMarius/rewerse-engineering](https://github.com/ByteSizedMarius/rewerse-engineering) dokumentiert Markt-/Liefer-/Abholkontext, GET `/api/products?query=...`, GET `/api/products?categorySlug=...`, Produktdetails. Das Drittprojekt verlangt App-Client-Zertifikate (mTLS); sie werden von uns weder extrahiert noch verwendet. Die hier neu hervorgehobene `/api/stationary-product-search`-Stringkonstante ist **nicht automatisch** über denselben Client oder Marktmodus nutzbar.

**ALDI SÜD:** [ByteSizedMarius/aldiscount](https://github.com/ByteSizedMarius/aldiscount) beschreibt (nach eigener Darstellung) anonym erreichbare JSON-Web-API mit Produktsuche/Kategorien, was gezielt mit der APK-/Web-Routenlage verglichen werden sollte, bevor Datenzugriff angenommen wird.

## Schreibschutz

Alle Dateien/Commits dieser Untersuchung liegen in `ecora2003-max/Try`. **`ecora2003-max/Ernaerungsgedaechnis` wurde nicht verändert.**

## Laufstatus

Sechs Teiljobs erfolgreich abgeschlossen, `kaufland` zum Berichtszeitpunkt noch in Bearbeitung. Sobald verfügbar, ist der tatsächliche Kaufland-JSON-Befund aus demselben Lauf separat zu bewerten; ältere Kaufland-`GET v1/products/{countryId}/{storeId}`-Methode ist bereits durch einen früheren gezielten JADX-Lauf dokumentiert.
