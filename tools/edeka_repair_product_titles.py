#!/usr/bin/env python3
"""Correct EDEKA public product detail title extraction in stored snapshot.

The first HTML h1 tags are site dialogs ("Mein EDEKA...", "Durchsuche
EDEKA.de"). The proper product h1 is the last title on item pages. This
repair is deterministic and offline; no retailer requests are made.
"""
from pathlib import Path
import json,re
p=Path("data/edeka/2026-10-31/product_page_subset.json")
obj=json.loads(p.read_text(encoding="utf8"))
items=obj["products"]
PREFIX="Mein EDEKA: Praktische Infos und Angebote Durchsuche EDEKA.de "
changed=0
for item in items:
    name=item.get("name")
    if not isinstance(name,str):raise RuntimeError("Missing product title")
    if name.startswith(PREFIX):
        n=name[len(PREFIX):].strip()
        if not n or len(n)>180 or n.startswith("Mein EDEKA"):
            raise RuntimeError("Unexpected name, refusing corruption")
        item["name"]=n
        changed+=1
    elif "Durchsuche EDEKA.de" in name:
        raise RuntimeError("Unexpected site chrome in product title")
if len(items)!=240 or changed!=240:
    raise RuntimeError(f"Expected to repair 240 known records, got {changed}/{len(items)}")
if len(set(x["product_page_id"] for x in items))!=len(items):
    raise RuntimeError("Duplicate EDEKA product page ids")
if any(x.get("price_eur") is not None for x in items):
    raise RuntimeError("Unexpected undocumented regular price")
obj["manifest"]["product_titles_normalized"]=True
obj["manifest"]["title_repair_method"]="Removed exact initial site-dialog h1 text from each name; 240 of 240 verified."
p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
manifest=Path("data/edeka/2026-10-31/product_page_subset_manifest.json")
m=json.loads(manifest.read_text(encoding="utf8"))
m.update({"product_titles_normalized":True,
          "title_repair_method":"Removed exact site-dialog h1 prefix; 240/240 products checked."})
manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({"status":"PASS","corrected_names":changed,"unique_ids":len(items),
                  "examples":[{"id":x["product_page_id"],"name":x["name"]} for x in items[:4]]},ensure_ascii=False))
