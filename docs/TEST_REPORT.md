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
