#!/usr/bin/env python3
"""Independent alternate 48-item slicing of the ALDI Süd public catalogue."""
import json
from pathlib import Path
import full_catalogue_access_aldi_sued as scan

scan.LIMIT=48
scan.MAX_PAGES=80
scan.DELAY=0.85
scan.main()
source=Path("results/full_catalogue_access_20261031/aldi_sued.json")
dest=source.with_name("aldi_sued_48.json")
source.replace(dest)
obj=json.loads(dest.read_text())
print("ALTERNATE_PAGING_RESULT",json.dumps({
    k:v for k,v in obj.items() if k in (
        "status","first_error","total_counts_seen",
        "unique_products_retrieved","sum_rows","priced_rows",
        "duplicate_ids","coverage_vs_reported_total",
        "all_reported_items_retrieved_exactly_once"
    )
},ensure_ascii=False))
