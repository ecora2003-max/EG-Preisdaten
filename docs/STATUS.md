# Preisdaten – Wiederaufnahmestand (31.10.2026)

**Grad:** `PARTIAL_READY / OFFLINE_VERIFIED` (Fachkern); **nicht** `READY_FOR_INTEGRATION` für produktive Händler-Livefeeds und nicht `INTEGRATED`. Das maßgebliche Ziel steht in `docs/ACCEPTANCE.md`.
**Letzter vollständig geprüfter Code-Commit:** `b5393999d99f5efeb3f2d738a213014ebfed0410`.
**Architekturvertrag:** `1.0.0-draft`, gelesen `d22862739bd0e3ef8451ce029e54f7c33ee53e40`; lokale Vertragsschema- und Beispiel-Fixures übernommen.
**Haupt-App:** nur gelesen, `6ba419ed2875c1988f45afee65e2708e7895cacf`; kein anderer Repo-Write.
**Historische Forschung:** ehemals `Try`, via GitHub-Redirect identisch mit `EG-Preisdaten`. Forschungsberichte bleiben erhalten.

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

## Neu implementiert

- `price_module/service.py` und `__main__.py`: eigenständiger, read-only `search`-, `search_offers`-, `search_catalog_prices`-, `lookup_price`-, `get_coverage`- und `resolve_stores`-Fachkern.
- Identifizierbare acht Händler; eine einheitliche Liste von `price.observation`-Vertrags-Umschlägen aus historischen, getrennten Liveparsern und synthetischen Snapshots.
- Ganzzahlige Cents, Null gegen Nullpreis, strikt nicht geratene GTIN-/Bio-Daten, explizite Mengenbasis, 2×500 g, Liter/Stück, Markt-/Region-/Kettenscope, unbekannte Zeitgeltung, Bedingungen/Pfand separat.
- Filialwechsel/fehlender Provenienzbeleg degradiert zu UNKNOWN; alte REWE-Referenzpreise separat; Netto-Onlinepreise als ONLINE; vollständige Lidl-Kategorie-Pagination strikt geprüft.
- Dataset-Import atomar; 403/429/204/502, unzulässiger Host, HTML statt JSON, Schemaänderung, ungültige Daten/Preise führen zu Fehlern ohne erfundene Beobachtungen.
- `usageMode=APP_DISPLAY` verweigert tatsächliche externe Händler-Snapshots ohne nachgewiesene Rechte (`RIGHTS_NOT_CLEARED`), synthetische Daten bleiben testbar. Kein Server/Token/Room/Sheets/OCR/Kauf- oder Bestandswrite.

## Tatsächlich ausgeführte Tests

CI: `pip install -r requirements-dev.txt; python3 -m compileall -q adapters catalogues price_module tests; python3 -m unittest discover -s tests -v; python3 -m price_module < examples/synthetic-price-query.json`.

| Code SHA | GitHub Actions | Ergebnis |
| --- | --- | --- |
| `c999f0f` | [41218368421](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218368421) | FAIL: 41 Tests, 1 fehlgeschlagener Mengen-Edgefall; behoben |
| `975a130` | [41218426005](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218426005) | PASS: 41 Tests |
| `c0d5d11` | [41218586900](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218586900) | PASS: 46 Tests |
| `dcd8aa9` | [41218729782](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218729782) | PASS: 48 Tests |
| `b539399` | [41218842198](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41218842198) | **PASS: 50 Tests, 0 Fehler; CLI-Check bestanden.** |

**Keine neuen Live-GET-Abrufe in diesen Code-/Unit-Testläufen.** Historische Live-Nachweise liegen in den alten Research-Berichten und Actions; sie wurden nicht als neue Beobachtung deklariert. Die JSON-Schema-Tests wurden mit `jsonschema` Draft 2020-12 und Formatchecker tatsächlich ausgeführt; `requirements-dev.txt` installiert zusätzlich BeautifulSoup für den älteren Netto-Parser.

## Verbleibende Abnahmelücken / nächste konkrete Aktion

1. Acht Angebote produktiv: ALDI-Süd- und REWE-Angebotskanal nicht vollständig als separater live-typisierter Feed; Netto-Kachel Filialgeltung nicht bewiesen, PDF-Preiszuordnung unvollständig. Für jeden fehlenden Pfad nur mit rechtlich freigegebener, gezielter Live-Gegenprobe weiterarbeiten.
2. Allgemeine Nutzungsrechte: es fehlen dokumentierte, verifizierte Freigaben für fortlaufende App-Darstellung/Caching/Redistribution; kein Produktions-Freischalten unter `APP_DISPLAY`. EDEKA bleibt besonders gesperrt.
3. Mengen-/Grundpreisfelder aus Roh-APIs sind teilweise nicht genau genug strukturiert; mehr Paket-/Pfand-/Apppreis-Sonderfälle, nachweisbare Mengenbasis und eindeutige Quellenstatus ergänzen.
4. Unabhängige Kategorie-/Filialabdeckung nur für einige API-interne Teilmengen; keine Händler-Vollsortiment- oder Preisänderungs-/Kassentreue-Garantie. Eigenständiger Store-Lookup ist bisher nur ein exact-match-Port, kein zugelassener Live-Store-Directory-Client.
5. Android/Kotlin-Code, Hardware-/App-Regression und offizielle Vertragsfreigabe nur durch Architektursteuerung/Codex; für das externe Modul weiterhin offen.
6. **Unmittelbar nächste Aktion:** `price_module/service.py` und `tests/test_price_module.py` prüfen: bedingte Apppreise und Mehrfachgebinde konsequent mit belegtem Rohfeld trennen; Abdeckung ohne Scheingewissheit. Danach vollständige CI erneut ausführen und getesteten SHA hier protokollieren. Keine Wiederholung bereits durchgeführter Try-Forschung ohne neuen konkreten Nachweisgrund.

**Kein Abschluss des Gesamtmandats:** `PARTIAL_READY`; nur synthetischer Offlinekern derzeit als Integrationstestvorlage geeignet. `INTEGRATED` nur Codex.
