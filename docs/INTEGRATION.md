# Adapter-Vertrag und Integration – Preisdaten
Ein Zulieferprodukt mit getrennten **Ports**:
- `searchOffers(request): Result<PriceObservation[], DataSourceError>`
- `searchCatalogPrices(request): Result<PriceObservation[], DataSourceError>`
- `resolveStores(retailerId, location): Result<StoreRef[], DataSourceError>`
- `getCoverage(request): CoverageReport`

Dies sind **fachliche Beispielsignaturen**, keine Vorgabe bestimmter Kotlin-/Python-Klassen. Query strikt nach erlaubter Quelle, `retailerId`, `storeId`, Datum, Suchbegriff. `PriceObservation` lässt sich auf `EG-Architecture/contracts/v1/contract.schema.json` abbilden; alle Feldverluste und nicht unterstützten Felder dokumentieren.

Die App/Codex stellt Netzwerkberechtigung, vom Nutzer gewählte Filialen und Datenspeicherung bereit. Das Modul führt weder persönliche Datenabfragen noch Kaufbuchungen aus. Der Code muss mit synthetischen/statischen Test-Fixtures ohne Netzwerk laufen. Zu jeder Antwort gehören Herkunft, beobachteter Zeitpunkt, Preisart, Abdeckung und Warnungen. Bei fehlendem Preis oder Markt `UNKNOWN` zurückgeben, nicht erraten. Der Modulbericht benennt den Stand des Vertrags, verwendete Referenzimplementation, Portierungsaufwand (falls Python) und Beispiel-Testbefehl.
