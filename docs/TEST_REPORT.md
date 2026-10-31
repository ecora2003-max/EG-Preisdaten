# CI-Testbericht – Preisdaten-Fachkern

**31.10.2026 · Architektur `1.0.0-draft`, commit `d22862739bd0e3ef8451ce029e54f7c33ee53e40`; getesteter Code `b5393999d99f5efeb3f2d738a213014ebfed0410`.**

```sh
python3 -m pip install -r requirements-dev.lock
python3 -m compileall -q adapters catalogues price_module tests
python3 -m unittest discover -s tests -v
python3 -m price_module < examples/synthetic-price-query.json
```

Ergebnis [Actions #41218842198](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218842198): **50/50 Tests erfolgreich**, 0 failures, 0 errors; Compile und Beispiel-CLI erfolgreich. Formal validiert: Architektur-`contract.schema.json` (Draft 2020-12 mit FormatChecker), Architekturbeispiele und die emittierten gültigen Preisnachrichten. Ungültige Quellrechte, fehlende Filialkennung bei `STORE_CONFIRMED`, negativer Preis werden vom Schema abgelehnt.

Suite: acht synthetische Händler mit aktuellen/zukünftigen/verfallenen Angeboten; Normalpreis/Referenzpreis/Onlinepreis getrennt; Preis-Cents, Nullpreis/unbekannt, 500g/2×500g/0,75l/Stück, Pfand, Datumsgrenzen, Filialwechsel; 403/429/204/502, HTML- statt JSON-Antwort, gebrochene Schemafelder und Pagination; EDEKA-Berechtigungssperre; Netto-Preisprüfung anhand sichtbarer und eingebetteter Felder; REWE zwei Märkte, ALDI Süd/Pagination, Lidl-Filialkatalog und Mehrseiten-Merge, ALDI-Nord-Kategorie; unveränderte Eingabedaten und atomare Import-Rücknahme.

Vorheriger Fehler [Run #41218368421](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218368421): 41 Tests, ein falscher Teil-Regex-Match bei `3,1234 kg`. Fix `975a130`, nächster Lauf [#41218426005](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218426005) PASS 41. Weitere grüne Läufe: [#41218586900](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218586900) (46 Tests) und [#41218729782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218729782) (48).

**Limitierung:** 50 grüne Offline-Tests beweisen nicht aktuelle Live-GET-Erreichbarkeit, Lizenzen, Vollständigkeit eines physischen Supermarkts, Kassenpreistreue oder Android-Kotlin-Integration. Keine neuen externen GET-Tests in diesem Implementierungslauf. Historische Nachweise verbleiben in `reports/` und älteren GitHub Actions.

## Folgeprüfung: 31.10.2026, `b201eed8cd9b5ab5de0db54cfa1cefd43727f234`

**[GitHub Actions #41220291373](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220291373): 70 von 70 Offline-Tests bestanden, keine Fehler; Compile + CLI-JSON-Demonstration bestanden.** CI-Python 3.12 mit `requirements-dev.lock` als gepinnter Dependency-Liste. Ältere Regressionen und JSON-Schema-Formatprüfung laufen weiterhin in derselben Suite.

Nachweise: 53/53 [#41219509257](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219509257), fehlgeschlagener Mengenregex-Negativtest 59er [#41219661169](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219661169) (korrigiert), 59/59 [#41219700996](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219700996), 62/62 [#41219866807](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41219866807), 65/65 [#41220003723](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220003723), 68/68 [#41220184464](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220184464), 70/70 [#41220291373](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220291373).

Neue fachliche Invarianten: bedingte und unbedingte Preise nicht vertauschen; Referenz-Streichpreise nicht als Kaufpreis schreiben; Grundpreisauszeichnungen nicht zu Packmengen machen; Regionen nur mit nachgewiesener Zuordnung dem Filialwunsch zuordnen; Fehler/übersprungene Prospektkarten, Limits, veraltete Zeitbasis und leere Felder transparent machen. Keine neuen Live-GET-Abrufe; historische Live-Befunde und Lizenzrisiken bleiben getrennt.

## Weiterer geprüfter Commit `079c7638effee3f0729391ae173ca2dd11d538f9`

[CI #41220508128](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220508128): **72/72 Offline-Tests erfolgreich**, 0 Failures/Errors; Kompilierung/CLI erfolgreich. Zwei neue Negativ-/Positivtests: exakt gültiger GTIN-Filter ohne Annahmen aus ungültigen Barcodes; ausschließlich explizit übermittelter `foodTypeId`-Filter, ungültige FoodType-Werte mit atomarer Ablehnung. Kein neuer Händler-Live-GET, kein Rechtsstatuswechsel.

## Folgelauf: Grundpreis-Konsistenz, Commit `8e935b4844d55261c393f0d3bef338cb3fc66437`

[GitHub Actions #41220671906](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220671906): **74/74 Tests PASS**, Kompilierung und CLI PASS. Zwei neue Tests: unveränderte Grundpreis-Quellenwerte werden bei nachweisbar kompatiblen Einheiten mit exakter Decimal-Arithmetik und 1-Cent-Toleranz gegen den beobachteten Verkaufspreis geprüft; widersprüchliche Beträge werden als `MISMATCH` markiert, ohne Preiswerte zu erfinden. Fehlen Preis/Menge/kompatible Basis oder ist Pfand bekannt, wird das Ergebnis bewusst nicht als konsistent behauptet. Ungültige Grundpreisfelder führen zu atomarer Ablehnung. Kein neuer Live-GET.

## 31.10.2026 – defensive Eingabevalidierung

Code-Commit `fe580013c619c366ec749ac98e1a630a91a86231`. [CI-Lauf #41220821950](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41220821950): **77/77 Offline-Tests bestanden**, Compile und synthetische CLI bestanden. Neue Tests für ungültige Artikel-/Markenfelder, fehlerhafte IDs, ungültige Anfragen, Herkunft und Scope sowie extreme Packmengen. Bei beschädigten Datensätzen erfolgt vollständiger Rollback der betroffenen Quelle. Keine neuen Live-GET-Tests und keine produktive Nutzungsrechtsfreigabe.

## 31.10.2026 – Portierbare Paritätsvektoren und Pagination-Härtung

- `a85dc60056248a600a10c95000e59b77dfc8873c`, [CI #41223722580](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223722580): **82/82 PASS**; Beobachtungsidentität, ALDI-Nord-Gültigkeit, Kanal-/Preisart-/Cents-Validierung.
- `0c959c59d4a7b33ad33b7e5c8d2ca6db49a10dee`, [CI #41223829550](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223829550): **83/83 PASS**, zusätzlich 16 eigenständig erwartete synthetische JSON-Paritätsvektoren (`tests/fixtures/porting_vectors.json`), Schema-Draft-2020-12-Validierung, unveränderte Eingaben, Compile/CLI.
- `a60359c8ca11f95330e51ff4e1129ff191f1868a`, [CI #41223853921](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223853921): **85/85 PASS**, ALDI-Süd-Seitenvollständigkeit und Lidl-bool-Pagination-Negativtests; Paritätsvektoren weiter grün. Keine Fehler oder übersprungenen Tests in den ausgewiesenen Suites.

Prüfbefehl in GitHub Actions (Python 3.12): `pip install -r requirements-dev.lock; python3 -m compileall -q adapters catalogues price_module tests; python3 -m unittest discover -s tests -v; python3 -m price_module < examples/synthetic-price-query.json`. **Keine neuen Live-GETs, keine rechtliche Quellenfreigabe, keine Kotlin-JVM- oder Android-Gerätetests.**

### Nachprüfung der Mengenbasis, Code `6f907892c018e8e66ba2624ae577044c05493a05`

[GitHub Actions #41223933684](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41223933684): **88/88 Offline-Tests PASS**, Python-Compile + CLI PASS. Drei zusätzliche Negativ-/Positivtests für explizites Abtropf-/Bruttogewicht, Original-Gebindetext und Nichtvergleichbarkeit mit NET-Grundpreis. Die 16 JSON-Paritätsvektoren bleiben grün. Keine neuen Live-GETs, Rechte- oder Android-Tests.

### 31.10.2026 – Kein synthetisches Rechte-Bypass durch Quellmetadaten

Code `5fefd76299612b0d5559cca771744a58409a5502`; [GitHub Actions #41224039268](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41224039268): **89/89 Offline-Tests PASS**, Compile + CLI PASS. Ein neuer Unit-Test und zwei JSON-Paritätsfälle (nun 18) prüfen, dass `APP_DISPLAY` echte Händlerherkunft oder externe Händler-`sourceUrl` nicht über `fixture=true` als synthetische Demo akzeptiert. Synthetische Testdaten bleiben zugelassen; der Nachweis ist eine Metadatenprüfung, keine Herkunftsauthentisierung. Kein neuer Händler-Live-GET, keine Lizenz- oder App-Freigabe.

## 31.10.2026 – Architekturaktualisierung ADR-014/016, Händlerfunktions-Gates

Architektur `3cfd591543ea4b8836992b1269de4db5e20a929f`, Vertragsmodell `1.0.0-draft` (v1-Schema- und Beispiele exakt identisch zu lokalen Fixtures), Funktionspolicy `1.0.1`. GitHub CI [#41227542690](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227542690): 93/93 erfolgreich (`bcca8ff`). Erster neuer On-Demand-Lauf [#41227630314](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227630314): 95 Testfälle mit 8 Fehlern durch nicht angepasste Aufrufgrenze (100 statt 20), Fehler korrigiert. [#41227677782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227677782): 95/95 bestanden (`13dcac61ba8a49dc0963074eccc25c7b763b55d7`). [Neuester CI #41227740061](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227740061): **95/95 PASS, 0 Fehlfälle, 0 übersprungen**, `6a45e460a3e85859504587ef1af562f77ce21e30`, Compile, vollständige Unit-/Legacy-/Kontraktsuite und synthetische CLI erfolgreich.

Erweiterung: Alle vier erlaubten Zielhändler können nur über gezielte, limitierte Preisabfrage gelesen werden, die vier Angebots-only-Händler bei `REGULAR` per `CAPABILITY_NOT_ALLOWED` abgewiesen; acht veröffentlichte Angebotskanäle durch synthetische Testfälle funktional erlaubt, nicht alle real live-adaptiert. Fünf zusätzliche maschinenlesbare Kotlin-Portierungsfälle (insgesamt 23) decken gemischte Händler, denied REGULAR und erlaubte Angebote ab. Keine neuen externen GET-Abrufe, keine Händlerrechte bewiesen, keine Android-Integration behauptet.

## 31.10.2026 – historische Zukunfts-/Rückblickssperre

`c78dcb393e8aa89f403953f0473d1149281c09d8` auf [GitHub Actions #41227915355](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227915355): **97/97 PASS**, 2 positive/negative Historien-Zeitfälle einschließlich Deutschland-/UTC-Datumsübergang. Nach Hinzufügen des 24. maschinenlesbaren Paritätsvektors: `46e40ed97f06e43b319a64ee02233ffeff27bee7` [CI #41227950088](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227950088) **97/97 PASS**, Schema-/Legacy-/Portierungs-/Kompilierungstest und CLI erfolgreich. Aktuell gelesener Architektur-Commit: `d7aa7dda1f0a34b52102b35785195e7ade26ceb4`; v1 Schema und Beispiele exakt unverändert. Keine Live-GETs, keine Lizenzfreigaben und keine Kotlin/Android-Integrationsprüfung.
