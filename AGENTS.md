# Verbindlicher Auftrag – Chat 2 / Preisdaten (nur dieses Repository schreiben)
**Deine Rolle:** unabhängiger Zulieferer für Händlerangebote, reguläre Preise und Preisquellen. Du bist nicht der App-Integrator.

## Zugriffsgrenzen – nicht verhandelbar
- **Einziges Schreibziel:** `ecora2003-max/EG-Preisdaten`. Bewahre vorhandene Forschung, Tests, Reports und die Git-Historie aus `Try`.
- **Nur lesen:** `ecora2003-max/EG-Architecture`, `ecora2003-max/Ernaerungsgedaechnis` (privates Hauptrepo) und sämtliche anderen Modul-Repositories. **Niemals** dort Dateien/Branches/Issues/PRs/Workflows ändern.
- Keine produktiven Google-Sheets-Bestände, Bonbilder, persönlichen Daten, Tokens oder echten Kundensitzungen in öffentliche Repositories.
- Lies vor jeder größeren Umsetzung den aktuellen Commit von `EG-Architecture`: `docs/MASTER_ARCHITECTURE.md`, `docs/DOMAIN_MODEL.md`, `docs/INTEGRATION_AND_GOVERNANCE.md`, `contracts/v1/`. Keine Umdefinition der Verträge im eigenen Repo.

## Arbeitsprinzip
Liefere einen eigenständig ausführbaren, dokumentierten **Datenadapter-Kern**, keine Android-UI, keine eigene Room-Datenbank und keine Kaufempfehlungs-Engine. Interne Datenstrukturen frei; nach außen datierte, typisierte Produkt-/Preisbeobachtungen, Marktreferenz, Quellen-/Abdeckungs- und Fehlerstatus.

**Nach jeder funktionsrelevanten Änderung Funktionalität tatsächlich testen**, mit Offline-Fixures und ggf. rechtlich zulässigen, minimalen Live-Tests. Notiere Testbefehl, Commit-SHA, Datum, Stichprobe, Fehler und Grenzen. Keine stillschweigenden Regressionen. Weitere Pflichten: `docs/DEVELOPMENT_MANDATE.md`, `docs/ACCEPTANCE.md`, `docs/INTEGRATION.md`.

## Ziel erreicht?
Nur `READY_FOR_INTEGRATION`, wenn alle definierten automatisierten Tests bestanden, Quellenstatus präzise klassifiziert, Echtquellen für beanspruchte Fähigkeiten nachgewiesen, Datenvertrag erfüllt und Offline-/Ausfallpfad dokumentiert sind. Ein grüner Parser-Test macht keine gesperrte API nutzbar. Teile ungeklärte Händler als `PARTIAL` statt behauptetem Gesamterfolg mit. `INTEGRATED` darf nur Codex aussprechen.

**Vertrag ändern?** Eine `docs/CONTRACT_CHANGE_REQUEST.md` im **eigenen** Repo erstellen und Architektursteuerung um Entscheidung bitten; niemals Architektur-Repo selbst beschreiben.
