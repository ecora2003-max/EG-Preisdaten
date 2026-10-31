# Preisdaten – Wiederaufnahmestand (31.10.2026)

## Verifizierter Fortsetzungslauf 31.10.2026 – acht Händler, Rechte/Scope/Preisart (Code `79df4094c3ef87c6324eda5bf9e3a2628599524d`)

- **GitHub Actions [#41228924705](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41228924705): SUCCESS, 103/103 Tests, 0 Fehler, 0 Skips.** Tatsächlich ausgeführt: Python 3.12, `pip install -r requirements-dev.lock`, `python3 -m compileall -q adapters catalogues price_module tests`, `python3 -m unittest discover -s tests -v`, `python3 -m price_module < examples/synthetic-price-query.json` und Envelope-Check. Job `124618816732`; Logs zeigen `Ran 103 tests in 0.281s / OK`; Compile/CLI/Envelope erfolgreich.
- **Neue ausführbare Negativ-/Positivmatrix:** `tests/test_policy_edgecases.py` mit 6 zusätzlichen Unit-Tests. Alle acht Händler: angebliches `rightsStatus=PERMITTED`/fiktiver Lizenzverweis im angelieferten Dataset ändert **nicht** die feste `APP_DISPLAY`-Sperre für Fremdquellen; synthetische Demo bleibt von externer Quelle getrennt; `PRIVATE_USER_HISTORY` ist kein Händler-Liveabrufmodus; für die vier Angebots-only-Händler wird eine als SALE maskierte `CURRENT_DISPLAYED`-Zeile atomar verworfen; Markt S1/S2 erfordert genaue Scope-Provenienz; fehlerhafte zweite Angebotszeile verwirft das gesamte Dataset, auch bei Suchfilter.
- **Kotlin-Portierungsbelege:** `tests/fixtures/porting_vectors.json` jetzt **28** unabhängige synthetische JSON-Paritätsfälle, davon vier neue: untrusted permission claim, gemischter APP_DISPLAY-Datensatz, fehlende Store/Region-Bindung, Netto-Angebotskanal mit falscher regulärer Preisart. Die Python-Paritätsprüfung ist in den 103 Tests enthalten; **kein Kotlin-JVM- oder Android-Test** durchgeführt.
- **Architekturstand frisch gelesen:** `EG-Architecture@d7aa7dda1f0a34b52102b35785195e7ade26ceb4`, ADR-014/016, `docs/RETAILER_SOURCE_POLICY.md`, `docs/PRICE_RIGHTS_AND_DISPLAY.md`, `contracts/v1.1/README.md`. Retailer-Policy `1.0.1` identisch (Git-Blob `06a05d5c47be8d67fb75dfca11821d8793be86fb`); v1-Schema und Beispiele jeweils exakt gleiche Blob-SHAs wie eigene Fixtures (`bedde467`, `5f483a1`). v1.1 weiterhin Draft und **kein** Ersatz des Preis-v1-Vertrags.
- **Rechteblockade unverändert:** Für keine externe Quelle ist eine hinreichend dokumentierte zweckbezogene App-Abruf-/Speicher-/Anzeigegrundlage nachgewiesen; `APP_DISPLAY` bleibt fail-closed, `RESEARCH_ONLY` nur für zulässige Einzelprüfung, eigene bestätigte Bons ausschließlich im privaten Host-Preisgedächtnis. Keine Live-GETs, keine neue Quellenlizenz, keine Behauptung vollständiger acht Händler-/Filialabdeckung. ALDI-Süd- und REWE-Angebotsfeeds sowie einzelne Filial-/Prospektgeltungen bleiben unbewiesen.
- **Konkrete nächste Aktion:** Bei nächstem Lauf neueste Architektur/Policy und HEAD lesen; anschließend negative Offline-Fixtures für credentialbehaftete oder händlerfremde Quell-URLs und Markt-/Region-Scope bei den vier zulässigen regulären Suchhändlern ergänzen. Falls eine Quelle produktiv genutzt werden soll, **vorher** quellen-/endpointbezogene Rechte-, Nutzungsbedingungen-, Datenbank- und Rate-Limit-Prüfung durch zuständige Stelle; keine neuen Live-/Massenscrapes. Codex muss alle 28 JSON-Fälle erst auf Kotlin/JVM sowie App-/Gerätetests portieren.


**Grad:** `PARTIAL_READY / OFFLINE_VERIFIED` (Fachkern); **nicht** `READY_FOR_INTEGRATION` für produktive Händler-Livefeeds und nicht `INTEGRATED`. Das maßgebliche Ziel steht in `docs/ACCEPTANCE.md`.
**Letzter vollständig geprüfter Code-Commit:** `c78dcb393e8aa89f403953f0473d1149281c09d8`; neuste geprüfte JSON-Fixtures: `46e40ed97f06e43b319a64ee02233ffeff27bee7`. [CI #41227950088](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227950088) **97/97 Tests PASS**, 24 transportable Portierungsvektoren, Compile/CLI PASS. Alle Tests tatsächlich auf GitHub Actions ausgeführt.
**Architekturvertrag:** `1.0.0-draft` für Preisbeobachtungen, zuletzt `d7aa7dda1f0a34b52102b35785195e7ade26ceb4` gelesen. `contracts/v1`-JSON-Schema und Beispiele unverändert zum eigenen Fixture (Git-Blob-SHAs identisch); Policy `retailer-source-capabilities.v1.json` v`1.0.1`, ADR-014/016. Shopping-v1.1 gesonderter, nicht freigegebener Entwurf.
**Haupt-App:** nur gelesen, `6ba419ed2875c1988f45afee65e2708e7895cacf`; kein anderer Repo-Write.
**Historische Forschung:** ehemals `Try`, via GitHub-Redirect identisch mit `EG-Preisdaten`. Forschungsberichte bleiben erhalten.

## Weitere Umsetzung – historische Zeitwahrheit (31.10.2026)

- **Code `c78dcb393e8aa89f403953f0473d1149281c09d8`**: Bei Preisbeobachtung **nach** dem angefragten historischen Einkaufstag erhält die Ausgabe auch bei rückwirkend geltendem Aktionsfenster ausdrücklich `eg-preisdaten:targetDateStatus=OBSERVED_AFTER_TARGET_DATE`. Berechnung anhand von `observedAt` mit `Europe/Berlin`-Kalendertag (Offsetgrenze und Mitternachtswechsel getestet). Dadurch darf die App kein rückblickend bekannt gewordenes Händlerangebot still als *damals belegte* Preisalternative übernehmen. Ohne historische Beobachtung zum damaligen Datum bleibt der damalige Preis unbelegt. 2 neue Unit-Tests, keine Händler-Live-Beweise.
- **Fixture `46e40ed97f06e43b319a64ee02233ffeff27bee7`**: zusätzliches maschinenlesbares Kotlin-/Python-Paritätsszenario für den Berlin-lokalen Kalenderübergang; jetzt **24 Paritätsfälle** (einschließlich 5 ADR-016-Gates). CI [#41227950088](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227950088): **97/97 PASS**, 0 fehlgeschlagen; vollständige Unit-, Legacy-, Schema-, Portierungs- und CLI-Regression. Vorgänger [#41227915355](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227915355) auf `c78dcb393e8aa89f403953f0473d1149281c09d8`: **97/97 PASS**.
- Architekturrevision `d7aa7dda1f0a34b52102b35785195e7ade26ceb4`: seit `3cfd591` nur architekturinterne Tests/Dokumente/Audits, **keine** Änderung des fachlichen v1-Preisvertrags oder der importierten Retailer-Policy. Die alte JSON-Schema-Fixture bleibt exakt identisch.
- **Nächste überprüfbare Aufgabe:** Scope/Datum/Evidenz und Anbieter-Regression im Preisadapter weiter prüfen, insbesondere ALDI Süd und REWE als noch nicht real belegte Angebotsquellen. Ungeklärte Quellenrechte/Filialabdeckung als echte Freigabe-Blocker markieren, nichts pauschal für App-Produktivbetrieb freischalten.

## ADR-016 / aktualisierte Architektur – verifizierter Umsetzungsstand

**Letzter geprüfter Code:** `13dcac61ba8a49dc0963074eccc25c7b763b55d7`; **letzter geprüfter Code- und Fixture-Stand:** `6a45e460a3e85859504587ef1af562f77ce21e30`. [GitHub Actions #41227740061](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227740061): **95/95 Tests PASS, 0 Fehler, 0 übersprungene Tests**, Python 3.12 mit `requirements-dev.lock`, Compile, Schema-Validierung und synthetischer CLI-Test PASS. Architekturrevision `3cfd591543ea4b8836992b1269de4db5e20a929f`, Schema `contracts/v1` ist bytegleich mit vorhandenen lokalen Schema-/Beispiel-Fixures. Das neue Shopping-`v1.1` ist für diesen Preisbeobachtungs-Adapter kein freigegebener Ersatz für `1.0.0-draft`.

**Neue verbindliche Funktionsmatrix:** ADR-016, `policies/retailer-source-capabilities.v1.json` v`1.0.1` lokal als `price_module/retailer_capabilities.v1.json` eingefroren. Für **ALDI Nord, ALDI Süd, REWE, Lidl** sind gezielte begrenzte Einzelpreisabfrage und Angebotserfassung vorgesehen. Für **Penny, Kaufland, EDEKA, Netto Marken-Discount** sind ausschließlich veröffentlichte Angebote funktional erlaubt; die `REGULAR`-Kanäle werden in `search_catalog_prices`, `search_product_prices` und `search(kind=BOTH)` mit `CAPABILITY_NOT_ALLOWED` / `POLICY_DENIED` verworfen. Vorhandene historische Parser verbleiben technisch zu Forschungs-/Regressionstestzwecken, sind **nicht** produktiv exponiert.

Neue `search_product_prices(request,datasets)` verlangt `retailerArticleId`, `gtin`, `foodTypeId` oder nichtleere `query` und begrenzt auf max. **50 Treffer** (Standard 20). Anders als ein Bulk-Katalogimport ist dies eine deterministische, schreibfreie Abfrage **bereits rechtmäßig bereitgestellter Snapshots**, kein Live-Collector. Die bestehende `search_catalog_prices`-Funktion ist der historische Offline-Forschungs-/Parserport und ebenfalls ADR-016-gefiltert. Die vier künftig vorgesehenen Angebotswege sind noch nicht alle mit aktuellen, rechtlich freigegebenen Live-Quellen belegt.

**Rechte als zweites unabhängiges Gate:** `APP_DISPLAY` für fremde nicht nachgewiesen erlaubte Händlerdaten bleibt mit `RIGHTS_NOT_CLEARED` blockiert, **auch bei fachlich erlaubtem Händler**. `UNVERIFIED` bedeutet nicht bewiesen verboten, aber keine verifizierte rechtliche App-Freigabe. `PRIVATE_USER_HISTORY` und Android-Hostdoppelgate liegen allein bei Codex/Produktdaten; keine persönlichen Bons wurden übernommen.

**CI-Nachweise:** `bcca8ff` [#41227542690](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227542690) 93/93 PASS. `3cd4f5a` [#41227630314](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227630314) 95 Tests mit 8 Fehlern, weil die neuen Testanfragen noch das alte `maxResults=100` verwendeten. Mit explizitem `maxResults=20` repariert: `13dcac61` [#41227677782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227677782) 95/95 PASS; neueste 23 JSON-Paritätsfälle inklusive 5 ADR-016-Vektoren ebenfalls [#41227740061](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227740061) 95/95 PASS. Alte Tests und acht Anbieter-Regressionsfälle unverändert durchgelaufen.

**Verbleibende Blockade / nächste Umsetzung:** ALDI-Süd- und REWE-Angebots-Bridges sind noch nicht quellengesichert; reguläre Preisabfragen nur für vier Zielhändler zulässig und selbst dort nur soweit verifizierbare, rechtlich hinreichend geklärte Quellen vorliegen. Prüfe als Nächstes gegen die jeweils neuesten Architektur- und Rechtsvorgaben besonders zeitliche Quellen-Geltung, filial- und regionengebundenen Scope sowie erlaubte Zugriffsmethoden. **Keine** Vollsortiments-, Live-Zugriffs-, App-Nutzungsrechts- oder Android-Gerätetest-Freigabe behaupten. `PARTIAL_READY / OFFLINE_VERIFIED` bleibt zwingend.

## Neueste Implementierungs- und Abnahmeprüfung (31.10.2026)

- **Code `a85dc60056248a600a10c95000e59b77dfc8873c`**: Preisbeobachtungs-IDs berücksichtigen nun Gebindemenge, Pfand, konditionale Preise und Quellmetadaten statt nur Artikel/Preis. ALDI-Nord-Quellgültigkeit bleibt erhalten; Kanal-/Preisart-Widersprüche, Cent-Überläufe und falsche Rabatt-Flags werden atomar abgewiesen. CI [#41223722580](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223722580) PASS (82 Tests).
- **Code `0c959c59d4a7b33ad33b7e5c8d2ca6db49a10dee`**: `tests/fixtures/porting_vectors.json` enthält **18 vollständig synthetische Kotlin-/Python-Paritätsfälle** mit manuell festgelegten Erwartungsprojektionen: Preis-null/0, Mehrfachgebinde/Grundpreis, Pfand/Apppreis, Zukunft/Verfall, Scope-/Regionbindung, Rechte-/Host-Sperren, atomare Ablehnung, Preisart, identische SKU mit unterschiedlichem Gebinde, REWE-Preisarten, alle acht Händler. `tests/test_porting_vectors.py` validiert Ausgabe gegen Architektur-JSON-Schema, Erwartungsfelder und unveränderte Eingaben. CI [#41223829550](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223829550): **83/83 PASS**, Compile + CLI PASS. **Noch keine Kotlin-JVM-Ausführung**; die JSON-Vektoren sind portierbare Testeingaben für Codex.
- **Code `a60359c8ca11f95330e51ff4e1129ff191f1868a`**: ALDI-Süd meldet nur bei lückenlosen, eindeutig bepreisten und identifizierten Ergebnissen `catalogue_complete=true`; Lidl-Pagination akzeptiert keine booleschen Seitenzähler. CI [#41223853921](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223853921): **85/85 PASS**, Compile + CLI PASS, Paritätsvektoren eingeschlossen.
- **Code `6f907892c018e8e66ba2624ae577044c05493a05`**: Unterscheidung von NET, DRAINED und GROSS bei ausdrücklich ausgewiesenen Gebindemengen, Original-Gebindetext als Provenienz-Extension und kein unzulässiger NET-Grundpreisabgleich für Abtropf-/Bruttogewicht. CI [#41223933684](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223933684): **88/88 PASS**, Compile + CLI PASS; Paritätsvektoren weiterhin grün.
- **Code `5fefd76299612b0d5559cca771744a58409a5502`**: `APP_DISPLAY`-Fixture-Ausnahme ist gegen falsch deklarierte Händlerdaten gehärtet: `fixture=true` verlangt `format=synthetic-fixture`, `origin=synthetic-fixture` und keine externe `sourceUrl`. Andernfalls `INVALID_FIXTURE` mit atomarem Rollback. Zwei zusätzliche JSON-Paritätsfälle (nun 18), ein Unit-Test. CI [#41224039268](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41224039268): **89/89 PASS**, Compile + CLI PASS. Technisch bleibt es eine Metadatenprüfung, keine kryptografische Prüfung synthetischer Herkunft.
- **Prüfkommando (CI Python 3.12):** `pip install -r requirements-dev.lock && python3 -m compileall -q adapters catalogues price_module tests && python3 -m unittest discover -s tests -v && python3 -m price_module < examples/synthetic-price-query.json`. Tatsächliche Ausführung: GitHub Actions, Run-IDs oben; nicht als lokale Ausführung ausgegeben.
- **Quellen-/Rechtestand unverändert:** keine neuen Händler-GETs, keine App-Darstellungs-/Caching-/Redistributionsrechte bestätigt; 8/8 Provider technisch benannt, aber nicht 8/8 produktive Live-Quellen freigegeben. Vertragsversion `1.0.0-draft`, Architektur-SHA `d22862739bd0e3ef8451ce029e54f7c33ee53e40`. Android-Portierung, echte Geräte- und Haupt-App-Regression weiterhin **nicht getestet**.

## Anbieter- und Abnahmematrix
`LIVE_VERIFIED` bedeutet **frühere begrenzte GitHub-Live-Tests vom 31.10.2026**, nicht gegenwärtig wiederholte Tests, allgemeine Exportberechtigung, Vollständigkeit oder bestätigten Kassenpreis.

| Händler | Angebote – historisch live | Gelistete Preise – historisch live | Filialgenauigkeit | Zukunft | Vollständigkeit | Rechte | letzter Forschungstest / getesteter Code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ALDI Nord | LIVE_VERIFIED | LIVE_VERIFIED | Kettenweite Angabe, Filiale nicht bestätigt | Folgewoche getestet | 174 Sortimentslisten, 1.781 IDs, kein Vollsortimentsbeweis | UNVERIFIED | 31.10.2026 / `b539399` |
| ALDI Süd | EXPERIMENTAL als eigenständiger Angebotsfeed | LIVE_VERIFIED, aktueller `walk-in`-Preis | Servicepoint, keine Kassenprüfung | Nicht nachgewiesen | Zähler/Pagination widersprüchlich | UNVERIFIED | 31.10.2026 / `b539399` |
| Lidl | LIVE_VERIFIED | LIVE_VERIFIED | Store-Key und Produktpreise belegt | veröffentlichte zeitgebundene Aktionen | 69/69 API-Blätter, 2.005 Kategorieeinträge, nicht sämtlicher Ladenbestand | UNVERIFIED | 31.10.2026 / `b539399` |
| REWE | Kein separater Feed im neuen Kern nachgewiesen | LIVE_VERIFIED, `current/regular` | zwei Märkte mit Preisunterschieden | Nicht nachgewiesen | Suchantwort max. 12 im Test, Pagination ungeklärt | UNVERIFIED | 31.10.2026 / `b539399` |
| EDEKA | LIVE_VERIFIED, markt-/nationalgebunden | Kein Vollsortiment-Preisfeed | Markt-ID, Nationalfallback getrennt | Woche getestet | 296 Angebotsobjekte aus zwei Märkten, 240 zusätzliche unbepreiste Produktseiten | RESTRICTED | 31.10.2026 / `b539399` |
| Netto Marken-Discount | LIVE_VERIFIED: Filial-Angebotskacheln; Prospekt-Zuordnung separat | ONLINE_LISTED live; stationärer Normalpreis nicht live | Prospektmarkt; Kachel-Preise ohne sichere Einzelmarktgeltung | Prospektwoche, Preiszuordnung nicht vollständig | 24/24 Kacheln einer Probe, kein Vollsortiment | UNVERIFIED | 31.10.2026 / `b539399` |
| PENNY | LIVE_VERIFIED | Kein Regalpreiskatalog | Selling-Region/NextWeek-Region | Folgewoche getestet | 193 Angebote aus 12 Kategorien, Teilmenge | UNVERIFIED | 31.10.2026 / `b539399` |
| Kaufland | LIVE_VERIFIED | Kein Regalpreiskatalog | klNr-Filialliste | veröffentlichte datierte Angebote | 511 Angebotsobjekte einer Testfiliale, Teilmenge | UNVERIFIED | 31.10.2026 / `b539399` |

Weitere Details: [Quellen- und Rechtsmatrix](SOURCES.md), alte `reports/` und [Tests](TEST_REPORT.md). **Für keinen der acht Händler liegt hier eine für die App verifizierte laufende Datenübernahme-/Redistributionsfreigabe vor.** Auch bei EDEKA ist eine zuvor berichtete Einzelfreigabe für Forschungs- oder Snapshot-Schritte nicht gleichbedeutend mit einer belegten allgemeinen App-Verwertungslizenz.


## Frühere Entwicklungsmeilensteine – ab Commit `b201eed8cd9b5ab5de0db54cfa1cefd43727f234`

- **Bis Commit `fe58001` 77/77 Tests grün**, inkl. 8-Händler-Offlinematrix, Architektur-JSON-Schema, alle bisherigen Händlerparser, Netto-Live-HTML-Fixures, negative Fehler- und Scope-Szenarien.
- Preisarten fachlich sauber getrennt: Lidl Plus und Netto App als **gesonderte konditionale Preisbelege ohne bestätigte Zugangsvoraussetzungen**, PENNY-Fußnotenpreis als Originaltext; Streich-/Referenzpreise keine früheren real bezahlten Preise.
- Der Fachkern erfasst Einzelpreise, Quellen-Grundpreisbelege, Pfand, bekannte Mengen und *unsichere* Mengen. Eine Netto-Grundpreisanzeige `1 kg = …` wird **nicht** fälschlich als Packungsgewicht 1 kg gedeutet.
- `storeSelections` und Reihenfilter verhindern Übernahme fremder Märkte/Verkaufsregionen; unterschiedliche Beobachtungszeitpunkte bleiben getrennte Beobachtungen. `shoppingDate` (nicht der Fensteranfang) ist für `targetDateStatus` ausschlaggebend.
- Ausgegeben: `matchedCount`, `outputTruncated`, Quellenfehler und abgelehnte Tiles; kein Scheinnachweis für Gesamtmarkt.
- Explizite Transportfehler `TIMEOUT/NETWORK_ERROR/TLS_ERROR/CANCELLED`, gesperrte/fehlerhafte HTTP- und Schema-Antworten; URLs mit Zugangsdaten oder tokenartigen Queryparametern werden abgelehnt.
- Gepinnte reproduzierbare CI-Dependency-Liste `requirements-dev.lock`; Lauf benötigt keinen externen kostenpflichtigen Dienst und keine Credentials.
- Offen: fehlende Nutzungsrechtsfreigaben und mehrere Händler-Livepfade; App-Komplettintegration und Kotlin-Portierung verbleiben ausschließlich bei Codex. **Kein `READY_FOR_INTEGRATION` für produktive Live-Daten**. Neu: explizite `gtin`- und `foodTypeId`-Filter ohne geratene Zuordnung sowie Quellen-Grundpreis-Plausibilitätsprüfung (mit Pfand- und Vergleichbarkeitsgrenzen).

## Neu implementiert

- `price_module/service.py` und `__main__.py`: eigenständiger, read-only `search`-, `search_offers`-, `search_catalog_prices`-, `lookup_price`-, `get_coverage`- und `resolve_stores`-Fachkern.
- Identifizierbare acht Händler; eine einheitliche Liste von `price.observation`-Vertrags-Umschlägen aus historischen, getrennten Liveparsern und synthetischen Snapshots.
- Ganzzahlige Cents, Null gegen Nullpreis, strikt nicht geratene GTIN-/Bio-Daten, explizite Mengenbasis, 2×500 g, Liter/Stück, Markt-/Region-/Kettenscope, unbekannte Zeitgeltung, Bedingungen/Pfand separat.
- Filialwechsel/fehlender Provenienzbeleg degradiert zu UNKNOWN; alte REWE-Referenzpreise separat; Netto-Onlinepreise als ONLINE; vollständige Lidl-Kategorie-Pagination strikt geprüft.
- Dataset-Import atomar; 403/429/204/502, unzulässiger Host, HTML statt JSON, Schemaänderung, ungültige Daten/Preise führen zu Fehlern ohne erfundene Beobachtungen.
- `usageMode=APP_DISPLAY` verweigert tatsächliche externe Händler-Snapshots ohne nachgewiesene Rechte (`RIGHTS_NOT_CLEARED`), synthetische Daten bleiben testbar. Kein Server/Token/Room/Sheets/OCR/Kauf- oder Bestandswrite.

## Tatsächlich ausgeführte Tests

CI: `pip install -r requirements-dev.lock; python3 -m compileall -q adapters catalogues price_module tests; python3 -m unittest discover -s tests -v; python3 -m price_module < examples/synthetic-price-query.json`.

| Code SHA | GitHub Actions | Ergebnis |
| --- | --- | --- |
| `c999f0f` | [41218368421](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218368421) | FAIL: 41 Tests, 1 fehlgeschlagener Mengen-Edgefall; behoben |
| `975a130` | [41218426005](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218426005) | PASS: 41 Tests |
| `c0d5d11` | [41218586900](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218586900) | PASS: 46 Tests |
| `dcd8aa9` | [41218729782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218729782) | PASS: 48 Tests |
| `b539399` | [41218842198](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218842198) | **PASS: 50 Tests, 0 Fehler; CLI-Check bestanden.** |

Zusätzliche Code- und CI-Meilensteine:
| Code-SHA | CI-Run | Ergebnis |
| --- | --- | --- |
| `0de9c92` | [#41219509257](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219509257) | PASS 53: Lidl-Plus-, Penny-Vorteils- und Netto-Apppreise getrennt |
| `10e84c5` | [#41219661169](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219661169) | FAIL 59: zu stark maskierte Mengenregex; behoben |
| `a6a03d4` | [#41219700996](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219700996) | PASS 59 |
| `78ccdd6` | [#41219866807](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219866807) | PASS 62: Quellenlücken und Transportfehler |
| `3735f21` | [#41220003723](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220003723) | PASS 65: historischer Referenzpreis getrennt, gepinnte Abhängigkeiten |
| `143d38b` | [#41220184464](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220184464) | PASS 68: Grundpreis-Quellbelege, credentialfreie URLs |
| `b201eed` | [#41220291373](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220291373) | **PASS 70/70: Filial- und Regionssperren** |

| `079c763` | [#41220508128](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220508128) | **PASS 72/72: GTIN-Prüfziffer und explizite FoodType-Filter** |
| `8e935b4` | [#41220671906](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220671906) | **PASS 74/74: Dezimalexakter Grundpreis-Plausibilitätscheck** |
| `fe58001` | [#41220821950](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220821950) | **PASS 77/77: ungültige Quellmetadaten, Anfragen und Extremmengen abgewehrt** |

**Keine neuen Live-GET-Abrufe in diesen Code-/Unit-Testläufen.** Historische Live-Nachweise liegen in den alten Research-Berichten und Actions; sie wurden nicht als neue Beobachtung deklariert. Die JSON-Schema-Tests wurden mit `jsonschema` Draft 2020-12 und Formatchecker tatsächlich ausgeführt; `requirements-dev.txt` installiert zusätzlich BeautifulSoup für den älteren Netto-Parser.

## Verbleibende Abnahmelücken / nächste konkrete Aktion

1. Acht Angebote produktiv: ALDI-Süd- und REWE-Angebotskanal nicht vollständig als separater live-typisierter Feed; Netto-Kachel Filialgeltung nicht bewiesen, PDF-Preiszuordnung unvollständig. Für jeden fehlenden Pfad nur mit rechtlich freigegebener, gezielter Live-Gegenprobe weiterarbeiten.
2. Allgemeine Nutzungsrechte: es fehlen dokumentierte, verifizierte Freigaben für fortlaufende App-Darstellung/Caching/Redistribution; kein Produktions-Freischalten unter `APP_DISPLAY`. EDEKA bleibt besonders gesperrt.
3. Mengen-/Grundpreisfelder aus Roh-APIs sind teilweise nicht genau genug strukturiert; mehr Paket-/Pfand-/Apppreis-Sonderfälle, nachweisbare Mengenbasis und eindeutige Quellenstatus ergänzen.
4. Unabhängige Kategorie-/Filialabdeckung nur für einige API-interne Teilmengen; keine Händler-Vollsortiment- oder Preisänderungs-/Kassentreue-Garantie. Eigenständiger Store-Lookup ist bisher nur ein exact-match-Port, kein zugelassener Live-Store-Directory-Client.
5. Android/Kotlin-Code, Hardware-/App-Regression und offizielle Vertragsfreigabe nur durch Architektursteuerung/Codex; für das externe Modul weiterhin offen.
6. **Unmittelbar nächste Aktion:** Die neuen ADR-016- und historischen Quellen-Zeit-Gates mit weiteren positiven/negativen Offline-Belegen für ALDI Süd/REWE/Lidl/ALDI Nord und die vier angebotsbeschränkten Händler härten; neue Verträge/Policy jeweils frisch lesen. Vor produktivem Live-Zugriff sind quellenindividuell dokumentierte Nutzungsrechte und technisch zulässige Zugangspfade erforderlich; Android-Einbau und `INTEGRATED` bleiben ausschließlich Codex vorbehalten.

**Kein Abschluss des Gesamtmandats:** `PARTIAL_READY`; nur synthetischer Offlinekern derzeit als Integrationstestvorlage geeignet. `INTEGRATED` nur Codex.
