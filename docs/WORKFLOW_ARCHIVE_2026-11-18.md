# Archivindex: 86 deaktivierte Händler-Rechercheworkflows (18.11.2026)

**Basis-Commit vor der Bereinigung:** [EG-Preisdaten@5c52bf708a3bfa91e5bfd309bbddc308b3d6766a](https://github.com/ecora2003-max/EG-Preisdaten/tree/5c52bf708a3bfa91e5bfd309bbddc308b3d6766a/.github/workflows).

**Änderung:** Alle alten Einzelrecherche-/Netzwerk-Workflows unten aus `.github/workflows/` der aktuellen Hauptlinie entfernt. **Nicht gelöscht wurden** Python-Adapter, `tools/`, Berichte, historische Ergebnisse, Modulverträge und Git-Historie. Jeder ursprüngliche YAML-Inhalt lässt sich aus dem oben verlinkten Commit oder Git-History wiederherstellen. Allein der Offline-`adapter-tests.yml`-Workflow bleibt aktiv.

**Grund:** Diese Skripte sollten ursprünglich API-/Katalog-Hypothesen einzeln prüfen, nicht als dauerhafte produktive Quellenpflege laufen. Viele reagierten auch auf Pushes und konnten unnötige Netzrequests und CI-Aufwand erzeugen. Bei einem alten EDEKA-Workflow wurde ein angebliches Berechtigungs-Flag selbst fest gesetzt und eine Snapshot-Schreibaktion nach Git vorgesehen: gerade dies ist **kein unabhängiger Nutzungsnachweis**. Kein aktiver Drittanbieter-Download allein aus einem früheren Analyseauftrag.

## Archivierte ursprüngliche Pfade

- `.github/workflows/aldi-assortment-index.yml`
- `.github/workflows/aldi-catalogue-parser.yml`
- `.github/workflows/aldi-navigation.yml`
- `.github/workflows/aldi-nord-data.yml`
- `.github/workflows/aldi-nord-sitemap-structure.yml`
- `.github/workflows/aldi-official-categories.yml`
- `.github/workflows/aldi-one-catalogue-page.yml`
- `.github/workflows/aldi-page-size-diagnostic.yml`
- `.github/workflows/aldi-price-serialization.yml`
- `.github/workflows/aldi-product-join.yml`
- `.github/workflows/aldi-product-json.yml`
- `.github/workflows/aldi-public-search.yml`
- `.github/workflows/aldi-regular-catalogue.yml`
- `.github/workflows/aldi-rendered-regular-prices.yml`
- `.github/workflows/aldi-sued-alternate-slicing.yml`
- `.github/workflows/aldi-sued-offset-edge.yml`
- `.github/workflows/aldi-sued-real-prices.yml`
- `.github/workflows/aldi-two-categories.yml`
- `.github/workflows/alternative-access.yml`
- `.github/workflows/apk-distribution-check.yml`
- `.github/workflows/apk-unit-tests.yml`
- `.github/workflows/broader-apk-discovery.yml`
- `.github/workflows/edeka-authorized-market-snapshot.yml`
- `.github/workflows/edeka-catalogue-discovery-authorized.yml`
- `.github/workflows/edeka-live-adapter.yml`
- `.github/workflows/edeka-netto-basic.yml`
- `.github/workflows/edeka-netto-store-study.yml`
- `.github/workflows/edeka-product-linkgraph-snapshot.yml`
- `.github/workflows/edeka-product-page-discovery.yml`
- `.github/workflows/edeka-product-pagination-probe.yml`
- `.github/workflows/edeka-product-sitemap-probe.yml`
- `.github/workflows/edeka-product-title-repair.yml`
- `.github/workflows/edeka-shop-prices.yml`
- `.github/workflows/edeka-source-check.yml`
- `.github/workflows/full-catalogue-access.yml`
- `.github/workflows/full-catalogue-feasibility.yml`
- `.github/workflows/full-catalogue-followup.yml`
- `.github/workflows/gk-scango-docs.yml`
- `.github/workflows/lidl-catalog-diagnose.yml`
- `.github/workflows/lidl-kaufland-deep.yml`
- `.github/workflows/lidl-nested-category.yml`
- `.github/workflows/lidl-product-fields.yml`
- `.github/workflows/lidl-product-linkage.yml`
- `.github/workflows/lidl-product-stores.yml`
- `.github/workflows/lidl-real-prices.yml`
- `.github/workflows/lidl-store-flyers.yml`
- `.github/workflows/lidl-stores-live.yml`
- `.github/workflows/live-adapter-smoke.yml`
- `.github/workflows/netto-branch-offers-validate.yml`
- `.github/workflows/netto-brochure-scope.yml`
- `.github/workflows/netto-category-offer-tiles.yml`
- `.github/workflows/netto-filialangebote-data-path.yml`
- `.github/workflows/netto-flyer-links.yml`
- `.github/workflows/netto-host-model-tracing.yml`
- `.github/workflows/netto-leaflet-host.yml`
- `.github/workflows/netto-links-smoke.yml`
- `.github/workflows/netto-more-price-sources.yml`
- `.github/workflows/netto-mpos-host-resolve.yml`
- `.github/workflows/netto-mpos-live-price.yml`
- `.github/workflows/netto-offer-dom-schema.yml`
- `.github/workflows/netto-offer-html-js.yml`
- `.github/workflows/netto-online-offer-adapter.yml`
- `.github/workflows/netto-online-price-signals.yml`
- `.github/workflows/netto-pdf-text.yml`
- `.github/workflows/netto-price-dto-inspect.yml`
- `.github/workflows/netto-product-api-static.yml`
- `.github/workflows/netto-product-search-live.yml`
- `.github/workflows/netto-products-page.yml`
- `.github/workflows/netto-search-to-price.yml`
- `.github/workflows/netto-shop-embedded-price.yml`
- `.github/workflows/netto-standard-chrome.yml`
- `.github/workflows/one-shot-price-probe.yml`
- `.github/workflows/open-de-prices.yml`
- `.github/workflows/other-chain-catalogue.yml`
- `.github/workflows/penny-category-coverage.yml`
- `.github/workflows/penny-kaufland-search.yml`
- `.github/workflows/price-completeness-freshness.yml`
- `.github/workflows/real-apk-research.yml`
- `.github/workflows/retailer-full-retrofit.yml`
- `.github/workflows/retailer-offers-probe.yml`
- `.github/workflows/rewe-pagination-control.yml`
- `.github/workflows/rewe-two-store-scope.yml`
- `.github/workflows/specific-applicability.yml`
- `.github/workflows/store-scoping.yml`
- `.github/workflows/targeted-jadx-apis.yml`
- `.github/workflows/vendor-scan-go.yml`

## Wiederaufnahme

Nur auf ausdrücklichen separaten Auftrag die konkret benötigten und zulässigen Tests aus Git-History übernehmen. Vor Aktivierung Netzwerkziele/Umfang/Timeouts/Tokenverwendung prüfen. Neue reguläre Preisquellen gehören in den aktiven Android-App-Anschluss, nicht in eine zweite parallele Datensammelautomatik.
