#!/usr/bin/env python3
"""Sitemap structural counts to test ALDI Nord category enumeration coverage."""
import collections,json,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from full_catalogue_access_aldi_nord import sitemap_links,valid_category

links,sitemap=sitemap_links()
counts=collections.Counter()
samples={}
for u in links:
    path=urllib.parse.urlparse(u).path
    parts=[x for x in path.split("/") if x]
    typ=parts[0] if parts else "/"
    counts[typ]+=1
    if len(samples.setdefault(typ,[]))<3:samples[typ].append(path)
product_patterns={
    "produkt":sum(urllib.parse.urlparse(u).path.startswith("/produkt/") for u in links),
    "produkte":sum(urllib.parse.urlparse(u).path.startswith("/produkte/") for u in links),
    "sortiment":sum(urllib.parse.urlparse(u).path.startswith("/sortiment/") for u in links),
}
out={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
     "sitemap":sitemap,"total_urls":len(links),
     "path_prefix_counts":dict(counts),
     "examples":samples,"product_path_guess":product_patterns,
     "listing_urls":len(set(x for u in links if (x:=valid_category(u))))}
p=Path("results/full_catalogue_access_20261031/aldi_nord_sitemap_structure.json")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(out,ensure_ascii=False))
