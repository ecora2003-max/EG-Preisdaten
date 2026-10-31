#!/usr/bin/env python3
"""Feasibility probe for actual EDEKA store prices vs EDEKA24 shipping prices.

One-time request set; no downloading complete products without validating what
the catalogue represents. Save raw diagnostics, not false 'full shelf prices'.
"""
from __future__ import annotations
import json, re, urllib.request, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA="ErnaehrungsgedaechnisResearch/2.0 (catalogue source identification)"
URLs={
 "edeka_reference_product":"https://www.edeka.de/sortiment/4311596029167/",
 "edeka24_robots":"https://www.edeka24.de/robots.txt",
 "edeka24_sitemap":"https://www.edeka24.de/sitemap.xml",
 "edeka24_shop_category":"https://www.edeka24.de/Lebensmittel/Fertiggerichte/",
 "edeka_gateway":"https://b2c-gw.api.edeka/",
}
report={"checked_utc":datetime.now(timezone.utc).isoformat(),
        "purpose":"Check if a complete EDEKA retail-price catalogue exists; do not confuse with EDEKA24 webshop.",
        "probes":[]}
for key,url in URLs.items():
    rec={"name":key,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xml;q=0.9,*/*;q=0.7"})
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read(1_000_000)
            rec["http"]=r.status;rec["bytes_sampled"]=len(raw)
            rec["content_type"]=r.headers.get("Content-Type")
        txt=raw.decode("utf8","replace")
        rec["eur_symbol_present"]="€" in txt or "&euro;" in txt
        rec["price_eur_patterns"]=len(re.findall(r"\b\d{1,3},\d{2}\s*(?:€|&euro;)",txt))
        rec["sitemap_url_samples"]=(re.findall(r"<loc>\s*([^<]+)\s*</loc>",txt,re.I)[:8])
        rec["product_tiles"]=len(re.findall(r'id=["\x27]listitem_\d+',txt))
        rec["catalogue_match"]=(re.findall(r"\b(\d[\d.,]*)\s+Produkte\b",txt,re.I)[:3])
        rec["price_jsonld"]=len(re.findall(r'"price"\s*:',txt,re.I))
        rec["gateway_access_required"]="contact EDEKA" in txt or "get access" in txt
    except urllib.error.HTTPError as e:
        rec["http"]=e.code;rec["result"]="HTTP_ERROR"
    except Exception as e:
        rec["result"]=type(e).__name__
        rec["error"]=str(e)[:100]
    report["probes"].append(rec)
dest=Path("results/edeka_catalogue_source_probe_20261031.json")
dest.parent.mkdir(exist_ok=True)
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False))
