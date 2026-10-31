#!/usr/bin/env python3
"""Check actual product-ID overlap between ALDI regular catalogue and next-week offers."""
import sys,json
from urllib.request import Request,urlopen
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalogues.aldi_nord import aldi_nord_catalogue_from_html
from adapters.retailer_offers import aldi_nord_next
ua="Ernaehrungsgedaechtnis-Research/2.1 (one-shot exact ID match test)"
urls=[
    "https://www.aldi-nord.de/sortiment/milchprodukte/joghurt-quark-milchdesserts.html",
    "https://www.aldi-nord.de/sortiment/milchprodukte/milch-milchgetraenke.html",
    "https://www.aldi-nord.de/angebote-vorschau.html"
]
snap=[]
for url in urls:
    with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html"}),timeout=20) as resp:
        snap.append(resp.read(600000).decode("utf-8","replace"))
a=[]
for s in snap[:2]:
    items,counts=aldi_nord_catalogue_from_html(s)
    a.extend(items)
b=aldi_nord_next(snap[2])
base={x.product_id:x for x in a}
promos={x.product_id:x for x in b}
ids=sorted(set(base)&set(promos))
result={"checked_utc":datetime.now(timezone.utc).isoformat(),
        "regular_category_products":len(base),
        "future_week_offer_products":len(promos),
        "matching_identical_product_ids":len(ids),
        "matched_examples":[{"id":v,"name":base[v].name,
            "displayed_baseline_eur":str(base[v].displayed_price_eur),
            "upcoming_offer_eur":str(promos[v].price_eur),
            "valid_from":promos[v].valid_from,
            "valid_to":promos[v].valid_to} for v in ids[:5]],
        "note":"Only two ordinary-price categories checked. Matching objectID does not itself prove a store-specific selling price."}
Path("results").mkdir(exist_ok=True)
Path("results/aldi_catalogue_offers_join.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(result,indent=2,ensure_ascii=False))
