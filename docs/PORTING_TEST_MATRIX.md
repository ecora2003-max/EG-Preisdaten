# Android-/Codex-Portierungsmatrix (Stand 31.10.2026)

Architektur: 1.0.0-draft, SHA d22862739bd0e3ef8451ce029e54f7c33ee53e40.
Python-Fachkern: fe580013c619c366ec749ac98e1a630a91a86231; CI 41220821950: 77 Tests PASS.

Diese Matrix ist eine Testvorgabe für Codex, keine erfolgte Android-Integration.

| Prüfklasse | Invariante |
| --- | --- |
| Händler | Acht eindeutige Händler-IDs, Herkunft und Rechte getrennt |
| Preis | 0 von null unterscheiden; SALE, CURRENT_DISPLAYED, LISTED_REGULAR und ONLINE_LISTED nicht vermischen |
| Bedingung | Lidl Plus, Penny und Netto App nicht als frei verfügbare Normalpreise ausgeben |
| Menge | 500 g, 2×500 g, 0,75 l, Stück; Grundpreis nicht als Gebindemasse interpretieren |
| Markt | Zwei Märkte, regionale Ausnahmen, keine erdachte STORE_CONFIRMED-Geltung |
| Zeitraum | Aktuell, angekündigte Zukunft, abgelaufene Aktionen; beobachtet ist nicht aktualisiert |
| Vollständigkeit | Unvollständige Pagination und ausgelassene Angebotskacheln sichtbar halten |
| Fehler | 204/403/429/500, Timeout, TLS, HTML statt JSON, geänderte Schemas und atomarer Rollback |
| Identität | Korrekte GTIN-Prüfziffer, bestätigte FoodType-ID, keine geratene Zuordnung |
| Rechte | Ohne belegte Wiederverwendungsrechte APP_DISPLAY abweisen |
| Seiteneffekt | Keine Änderungen an Room, Beständen, Käufen, Bons, Rezepten oder Sheets |

Codex portiert die bestehenden JSON-Beispiele und Python-Tests auf pure Kotlin-JVM-Funktionen.
Money als ganzzahlige Cents und BigDecimal, ISO LocalDate/OffsetDateTime mit Zone, vollständiger Vertrag v1.
Kein Cloudserver, keine Bezahl-API und keine eigenständige zweite Datenbank.
Erst nach App-Regressions-, Migrations- und Gerätetests darf Codex INTEGRATED melden.
Bis rechtliche Quellenfreigaben vorliegen, bleiben produktive Live-Feeds gesperrt.
