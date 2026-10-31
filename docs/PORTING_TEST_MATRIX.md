# Android-/Codex-Portierungsmatrix (Stand 31.10.2026)

Architektur: 1.0.0-draft, SHA d22862739bd0e3ef8451ce029e54f7c33ee53e40.
Python-Fachkern: 5fefd76299612b0d5559cca771744a58409a5502; CI 41224039268: 89 Tests PASS.

Diese Matrix ist eine Testvorgabe für Codex, keine erfolgte Android-Integration.

| Prüfklasse | Invariante |
| --- | --- |
| Händler | Acht eindeutige Händler-IDs, Herkunft und Rechte getrennt |
| Preis | 0 von null unterscheiden; SALE, CURRENT_DISPLAYED, LISTED_REGULAR und ONLINE_LISTED nicht vermischen |
| Bedingung | Lidl Plus, Penny und Netto App nicht als frei verfügbare Normalpreise ausgeben |
| Menge | 500 g, 2×500 g, 0,75 l, Stück; NET/DRAINED/GROSS strikt trennen, Original-Gebindetext bewahren; Grundpreis nicht als Gebindemasse interpretieren |
| Markt | Zwei Märkte, regionale Ausnahmen, keine erdachte STORE_CONFIRMED-Geltung |
| Zeitraum | Aktuell, angekündigte Zukunft, abgelaufene Aktionen; beobachtet ist nicht aktualisiert |
| Vollständigkeit | Unvollständige Pagination und ausgelassene Angebotskacheln sichtbar halten |
| Fehler | 204/403/429/500, Timeout, TLS, HTML statt JSON, geänderte Schemas und atomarer Rollback |
| Identität | Korrekte GTIN-Prüfziffer, bestätigte FoodType-ID, keine geratene Zuordnung |
| Rechte | Ohne belegte Wiederverwendungsrechte APP_DISPLAY abweisen; `fixture=true` darf nur explizit synthetische Provenienz ohne externe `sourceUrl` besitzen |
| Seiteneffekt | Keine Änderungen an Room, Beständen, Käufen, Bons, Rezepten oder Sheets |

Codex portiert die bestehenden JSON-Beispiele und Python-Tests auf pure Kotlin-JVM-Funktionen.
Money als ganzzahlige Cents und BigDecimal, ISO LocalDate/OffsetDateTime mit Zone, vollständiger Vertrag v1.
Kein Cloudserver, keine Bezahl-API und keine eigenständige zweite Datenbank.
Erst nach App-Regressions-, Migrations- und Gerätetests darf Codex INTEGRATED melden.
Bis rechtliche Quellenfreigaben vorliegen, bleiben produktive Live-Feeds gesperrt.

## Maschinenlesbare Portierungsfälle

Die Datei [`tests/fixtures/porting_vectors.json`](../tests/fixtures/porting_vectors.json) enthält **24 unabhängige synthetische Fälle** mit `request`, `datasets` und `expect`. `expect.observations` enthält **Teilprojektionen** der Vertrags-`payload`s; die angegebenen Felder sind exakt zu vergleichen, zusätzliche optionale/namespaced Felder sind erlaubt. `matchedCount`, `errorCodes`, Reihenfolge/Anzahl der Beobachtungen und bei Bedarf `coverageStatuses` sowie eindeutige `observationId` sind ebenfalls verbindliche Erwartungen. Diese Tests werden von `tests/test_porting_vectors.py` in der Python-CI ausgeführt, nicht von Kotlin.

**Kotlin-JVM-Übernahme:** JSON als Ressourcen laden; `PriceService.search(request,datasets)` semantisch portieren; jede erwartete Teilprojektion rekursiv prüfen, vollständige Ausgaben gegen `contracts/v1/contract.schema.json` der Architektur validieren und Eingabeimmutabilität sicherstellen. Fehlercodes statt lokalisierter Fehlermeldungen vergleichen. `observationId`-Eindeutigkeit ist verpflichtend, sprachübergreifend identische Hash-Bytes sind nicht spezifiziert; dies ist eine interne Implementierungsentscheidung, kein Architektur-Vertragsfeld. Erst echte Kotlin-Tests und App-/Gerätetests gelten als Integrationsnachweis.

Testbefehl: `python3 -m unittest tests.test_porting_vectors -v` oder vollständige Suite `python3 -m unittest discover -s tests -v`. Die Vektoren enthalten keine Live-Händlerpreise und sind keine Rechtefreigabe.

## ADR-016: zusätzlich verpflichtende Android-Negativtests

Die [24 Paritätsfälle](../tests/fixtures/porting_vectors.json) enthalten fünf neue, gezielt portierbare Händlerfunktionsfälle aus der Architekturrevision `3cfd591543ea4b8836992b1269de4db5e20a929f`. Der Android-Host muss unabhängig vom Preisadapter die vier `REGULAR`-Verbote (Penny, Kaufland, EDEKA, Netto Marken-Discount) erzwingen, ebenso das Fremdquellen-Rechtegate für `APP_DISPLAY`; unbestätigte eigene Bons bleiben `PRIVATE_USER_HISTORY`-undokumentiert, keine automatische Historie. `REWE`, `LIDL`, `ALDI_NORD`, `ALDI_SUED` dürfen nur gezielt/on-demand und bis 50 Ergebnisse pro Anfrage angefragt werden, keine Vollsortimentsabfrage. Historische technische Netto-Onlineparser sind nicht produktiv zugelassen. [Python-Parität CI #41227740061](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227740061) ersetzt keinen Kotlin-JVM-/Gerätetest.

### Historische Quellenzeit (Code `c78dcb393e8a`)

Zusätzlicher Portierungsfall `historical-hindsight-snapshot-postdates-shopping-day`: Händler-Beobachtung 2026-10-31 23:30 UTC ist in `Europe/Berlin` bereits der **01.11.2026**. Für Einkaufsdatum **31.10.2026** muss `eg-preisdaten:targetDateStatus` daher `OBSERVED_AFTER_TARGET_DATE` sein, selbst wenn `validFrom/validUntil` den Einkaufstag einschließen. [Nachweis CI #41227950088](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41227950088). Kotlin-JVM-Port muss diesen Fall ohne implizite lokale Geräteeinstellungen reproduzieren.

## Neue ADR-016-/ADR-014-Paritätsfälle (Code `79df4094`, CI #41228924705)

**28 statt 24 JSON-Fälle** in `tests/fixtures/porting_vectors.json`, Python-CI **103/103 PASS**. Vier neue Fälle mit exakt erwarteten `matchedCount`, `errorCodes`, `coverageStatuses` und Projektionen: `rights-untrusted-permitted-claim-still-blocked`, `app-display-synthetic-and-external-rights-mixed`, `regional-feed-without-store-region-proof-rejected`, `offer-only-netto-regular-price-kind-in-sale-rejected`. Die zusätzlichen sechs Unit-Tests in `tests/test_policy_edgecases.py` variieren Rechte, Händler und zwei Filialen über alle acht Anbieter. Die Portierung muss in Kotlin die gleichen Ausgaben/Fehler reproduzieren, nicht bloß die Python-JSON-Beispiele lesen. **Kotlin nicht ausgeführt; App-Rechtefreigabe weiterhin gesperrt.** [CI-Run #41228924705](https://github.com/ecora2003-max/EG-Preisdaten/actions/runs/41228924705).

## 31.10.2026 – zusätzliche Source-/Scope-/ADR-016-Paritätsfälle

Die maschinenlesbare Matrix enthält nun **34 statt 28** synthetische JSON-Fälle. Sechs neue Namen: `regular-foreign-retailer-source-url-denied`, `regular-credential-alias-in-url-denied`, `regular-allowed-four-synthetic-targeted-snapshots`, `regular-excluded-four-with-netto-sale-still-visible`, `regular-store-claimed-without-scope-proof-is-unknown`, `penny-region-feed-does-not-prove-store-applicability`. Das zusätzliche Python-Testmodul `tests/test_source_policy_hardening.py` prüft außerdem URL-Host-/Credential-Varianten, alle acht Händler, vier erlaubte REGULAR- und vier Angebots-only-Händler, APP_DISPLAY-Rechte und Filialbelege. Der Android-/Kotlin-Port muss diese Fälle unabhängig nachbilden; JSON-Parität in Python ist **kein** Kotlin-JVM-/Gerätetest und keine Händlerlizenz.
