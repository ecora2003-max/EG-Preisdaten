# Abnahmekriterien und Testpflicht – Preisdaten
## Nach jeder fachlichen Codeänderung
1. Alle betroffenen Offline-Unit-/Adaptertests ausführen; Testbefehl und Commit im `docs/STATUS.md` mit Ergebnis dokumentieren. Bestehende Tests nicht deaktivieren oder künstlich vereinfachen.
2. Contract-Fixtures aus `EG-Architecture/contracts/v1` für validen Preisdatensatz, unbekannten Preis/Menge und ungültige Quelle prüfen. JSON auf Vertrag validieren; fehlende Schema-Prüfung sichtbar melden.
3. Parser-Mockfälle mit Datumsgrenzen, Filialwechsel, nicht-200/HTML statt JSON, fehlenden Feldern, Mehrfachgebinde, Pfand, Bedingungen, Storno/Ausfällen, veränderten JSON-Schlüsseln und null/0 testen.
4. **Liveabhängige** Funktion nur nach einer realen, zulässigen, begrenzten GET-Gegenprobe als `LIVE_VERIFIED` bezeichnen. Bericht: genaue URL-/Parameterfamilie ohne Secrets, Zeitpunkt, tatsächliche Feldwerte und Antworttyp, Zahl Treffer, Fehlerfälle; Lizenz gesondert.
5. Bei Änderungen an Händlerparsern gezielte Regressionstests der übrigen Händler ausführen; keine stillen Verschlechterungen.
6. Preisdaten erlauben keine direkte Bestands-, Bon- oder Kaufbuchung – Test dafür ergänzen.

## Akzeptanzmatrix
| Kriterium | Nachweis |
| --- | --- |
| Alle acht Händler als Adapter/Provider identifiziert | Provider-Registry- und Fallback-Tests; pro Händler Status, Datum, Geltungsbereich |
| Aktuelle und zukünftige Angebotsdaten soweit von Quelle bereitgestellt | je Händler mindestens synthetischer Test für aktuell/zukünftig/abgelaufen; echter Beleg je beanspruchter Fähigkeit |
| Verkaufspreis ≠ Referenzpreis ≠ Onlinepreis ≠ historischer Preis | deterministische Typ-/Mappingtests |
| Mengenbasis, Pfand, bedingte Rabatte korrekt | Fixture mit 500g, 2×500g, Liter und Stückware |
| Marktbezug sicher | Test zweier Märkte und nationalem Fallback ohne falsches `STORE_CONFIRMED` |
| Fehler, Quellensperren und Teilabdeckung sichtbar | Timeout/403/429/204/HTML/Schemaänderung und unvollständige Pagination |
| Quellenstatus und erlaubte Nutzung explizit | datierte Quellenmatrix; `UNVERIFIED` nicht als Erlaubnis darstellen |
| Offline-Integration möglich | Adapter-/Fixture-Provider, maschinenlesbare Beispielantwort und Android-Einbauplan |
| Reproduzierbar | Testbefehle, Lock-/Dependency-Liste, CI ohne geheime Daten, SHA/Testbericht |

## Wann gilt das Gesamtziel als erreicht?
**Nur wenn** alle vorhandenen, rechtmäßig nutzbaren Live-Quellen tatsächlich getestet, Vertrags- und Negativtests grün, Abdeckung und rechtliche Grenzen eindeutig dokumentiert und die Daten ohne bestehende App-DB als eigenständiges Produkt lesbar sind. Falls einzelne der acht Händler noch keinen belastbaren Live-Pfad haben, Modulstatus **`PARTIAL_READY`** mit genauer Händlerliste; volle acht-Händler-Quellenabdeckung **nicht** behaupten. Ein Forschungsnachweis statischer API-Signaturen ist nicht einmal ein Live-Preisbeweis. **`INTEGRATED` nur Codex.**

## Pflicht-Statusdatei
`docs/STATUS.md` mit Tabelle Anbieter | Angebote-Live | reguläre Preise-Live | Filialgenauigkeit | Zukunft | Vollständigkeit | Rechte | letzter Test/Commit; getrennt davon offene Issues und tatsächlich ausgeführte Tests. Ohne nachprüfbaren Status kein Abnahmevotum.

## Zusätzliche Abnahme aufgrund Architektur ADR-014 / ADR-016 (31.10.2026)

Die bisherige fachliche Acht-Händler-Matrix ist durch die ausdrücklich entschiedene Funktionsmatrix `EG-Architecture/policies/retailer-source-capabilities.v1.json` (Version 1.0.1) **eingeschränkt**, ohne historische Forschungsergebnisse zu löschen: Gezielte Produktpreise nur ALDI_NORD/ALDI_SUED/REWE/LIDL; veröffentlichte Angebote alle acht. Kein fachlich ausgeschlossener Netto-/Penny-/Kaufland-/EDEKA-Normalpreis darf über `search_catalog_prices`, `search_product_prices` oder `search(BOTH)` durchschlüpfen. Testpflicht: vier Negativhändler, vier Positivhändler, gemischte Suchergebnisse, begrenzte gezielte Abfrage und Provenienzbeleg, **zweites separates Rechte-Gate** für `APP_DISPLAY`.

Die Entscheidung ist eine **Funktionsfreigabe, keine Quellen-/Lizenz-/Sammelrechtsfreigabe**. Erst quellen- und nutzungsartbezogener Nachweis für zulässigen Abruf, Speichern, Anzeigen plus reale Gegenprobe darf eine produktive Quelle freigeben. Fehlende ALDI-Süd-/REWE-Angebotslivepfade und unklare Rechte bleiben ausdrücklich Abnahmelücken, auch bei grünen Offline-Tests. Private bestätigte Bonhistorie ist Sache der App, kein Händler-Livepreis. Android- und echte Gerätetests bleiben ausschließlich Codex vorbehalten.
