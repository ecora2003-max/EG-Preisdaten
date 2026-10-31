# CI-Testbericht – Preisdaten-Fachkern

**31.10.2026 · Architektur `1.0.0-draft`, commit `d22862739bd0e3ef8451ce029e54f7c33ee53e40`; getesteter Code `b5393999d99f5efeb3f2d738a213014ebfed0410`.**

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m compileall -q adapters catalogues price_module tests
python3 -m unittest discover -s tests -v
python3 -m price_module < examples/synthetic-price-query.json
```

Ergebnis [Actions #41218842198](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218842198): **50/50 Tests erfolgreich**, 0 failures, 0 errors; Compile und Beispiel-CLI erfolgreich. Formal validiert: Architektur-`contract.schema.json` (Draft 2020-12 mit FormatChecker), Architekturbeispiele und die emittierten gültigen Preisnachrichten. Ungültige Quellrechte, fehlende Filialkennung bei `STORE_CONFIRMED`, negativer Preis werden vom Schema abgelehnt.

Suite: acht synthetische Händler mit aktuellen/zukünftigen/verfallenen Angeboten; Normalpreis/Referenzpreis/Onlinepreis getrennt; Preis-Cents, Nullpreis/unbekannt, 500g/2×500g/0,75l/Stück, Pfand, Datumsgrenzen, Filialwechsel; 403/429/204/502, HTML- statt JSON-Antwort, gebrochene Schemafelder und Pagination; EDEKA-Berechtigungssperre; Netto-Preisprüfung anhand sichtbarer und eingebetteter Felder; REWE zwei Märkte, ALDI Süd/Pagination, Lidl-Filialkatalog und Mehrseiten-Merge, ALDI-Nord-Kategorie; unveränderte Eingabedaten und atomare Import-Rücknahme.

Vorheriger Fehler [Run #41218368421](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218368421): 41 Tests, ein falscher Teil-Regex-Match bei `3,1234 kg`. Fix `975a130`, nächster Lauf [#41218426005](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218426005) PASS 41. Weitere grüne Läufe: [#41218586900](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218586900) (46 Tests) und [#41218729782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218729782) (48).

**Limitierung:** 50 grüne Offline-Tests beweisen nicht aktuelle Live-GET-Erreichbarkeit, Lizenzen, Vollständigkeit eines physischen Supermarkts, Kassenpreistreue oder Android-Kotlin-Integration. Keine neuen externen GET-Tests in diesem Implementierungslauf. Historische Nachweise verbleiben in `reports/` und älteren GitHub Actions.
