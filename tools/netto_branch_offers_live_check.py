#!/usr/bin/env python3
"""Live verify retailer-published Netto branch offer price/ID/validity.

Cross-check embedded wishlist URL Price against price displayed on the tile.
Never invoke the wishlist endpoint (it mutates user state). Source is official
Netto category HTML. An offer price is not a normal shelf price.
"""
import json,sys,urllib.request,urllib.error
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalogues.netto_branch_offers import parse_branch_offers

URLS=[
 "https://www.netto-online.de/angebote/c-N07",
 "https://www.netto-online.de/lebensmittel-angebote/c-N07941",
]
UA="ErnaehrungsgedaechnisResearch/2.5 (public Netto weekly offer price consistency)"
OUT=Path("results/netto_branch_offer_live_check_20261031.json")

def offline():
 html='''<section class="store-offers">
 <header><h2>Filial-Angebote</h2>
 <p class="store-offers__header__date">gültig von Montag, 26.10.26 - Samstag, 31.10.26</p></header>
 <div class="tc-store-product-tile" data-ff-id="12345">
 <h3 class="tc-product-name">Gurken</h3>
 <div class="grid-top-price"><div class="product__current-price tc-product-price">0.<span class="product__current-price--digits-after-comma">89</span>*</div></div>
 <a href="https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPWishlist-AddStoreArticle?SKU=12345&amp;Name=Gurken&amp;Price=0.89&amp;BasePrice=&amp;ValidTo=2026-10-31+20%3A00%3A00"></a>
 </div></section>'''
 rows,meta=parse_branch_offers(html,"https://www.netto-online.de/angebote/c-N07")
 assert meta["candidate_tiles"]==1 and len(rows)==1, (meta,rows)
 assert str(rows[0].sale_price_eur)=="0.89"
 assert rows[0].valid_from_date=="2026-10-26"
 assert rows[0].valid_to_local=="2026-10-31 20:00:00"
 assert rows[0].advertised_app_price_eur is None
 wrong=html.replace("Price=0.89","Price=9.89")
 rows,meta=parse_branch_offers(wrong,"https://www.netto-online.de/angebote/c-N07")
 assert not rows and "PRICE_NAME_OR_SKU_MISMATCH" in meta["warnings"]
 return "PASS"

def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
 with urllib.request.urlopen(req,timeout=28) as f:return f.read(1500000).decode("utf8","replace")

def main():
 output={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
         "scope":"Netto chain-advertised branch offers as shown on public category HTML, selected store unknown",
         "offline_contract":offline(),"pages":[]}
 all_found={}
 for url in URLS:
  rec={"url":url}
  try:
   html=fetch(url)
   entries,meta=parse_branch_offers(html,url)
   rec.update(meta)
   rec["offer_samples"]=[x.to_dict() for x in entries[:6]]
   rec["app_price_item_count"]=sum(x.advertised_app_price_eur is not None for x in entries)
   rec["distinct_id_count"]=len({x.offer_id for x in entries})
   for item in entries:all_found.setdefault(item.offer_id,item)
  except urllib.error.HTTPError as e:rec.update({"status":"HTTP_ERROR","http":e.code})
  except Exception as e:rec.update({"status":"ERROR","error_class":type(e).__name__,"error":str(e)[:140]})
  output["pages"].append(rec)
 output["distinct_offer_ids_across_pages"]=len(all_found)
 output["all_verified_prices_numeric"]=all(x.sale_price_eur is not None for x in all_found.values())
 output["complete_case"]=all(x.get("status")=="PARSED" and x.get("candidate_tiles")==x.get("verified_sale_price_tiles") for x in output["pages"])
 output["result"]="LIVE_OFFER_PRICES_VERIFIED" if output["complete_case"] and len(all_found)>0 else "INCOMPLETE_OR_UNVERIFIED"
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(output,ensure_ascii=False))
 if output["result"]!="LIVE_OFFER_PRICES_VERIFIED":raise SystemExit(2)
if __name__=="__main__":main()
