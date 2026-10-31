#!/usr/bin/env python3
"""Netto official product search -> matching official detail page -> validated EUR price.

A targeted search and small number of item pages, no full scraping. Test three
ordinary shopping terms. The product price is a NETTO_ONLINE_SHOP price, not a
cash-register price. Normal inventory/store access unproven.
"""
from __future__ import annotations
import sys,json,re,urllib.parse,urllib.request,urllib.error
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalogues.netto_online import prices_from_product_html
BASE="https://www.netto-online.de"
SEARCH=BASE+"/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPParametricSearch-SimpleOfferSearch"
UA="ErnaehrungsgedaechnisResearch/2.4 (Netto official targeted product price search)"
TERMS=("Haferflocken","Mandeln","Reis")
MAX_ITEMS_EACH=5
MAX_BODY=900000
OUT=Path("results/netto_search_to_online_price_20261031.json")
class Links(HTMLParser):
 def __init__(self):
  super().__init__();self.found=[]
 def handle_starttag(self,tag,attributes):
  if tag not in ("a",):return
  a=dict(attributes); href=a.get("href")
  if isinstance(href,str):
   path=urllib.parse.urlparse(urllib.parse.urljoin(BASE,href))
   if path.netloc=="www.netto-online.de" and re.search(r"/p-\d{7,15}(?:$|[/?])",path.path):
    self.found.append(urllib.parse.urlunparse((path.scheme,path.netloc,path.path,"","","")))
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html","Accept-Language":"de-DE,de;q=0.9"})
 with urllib.request.urlopen(req,timeout=25) as r:
  body=r.read(MAX_BODY+1);status=r.status
 if len(body)>MAX_BODY:raise ValueError("Body max exceeded")
 return body.decode("utf8","replace"),status
def term_check(term):
 result={"term":term}
 url=SEARCH+"?"+urllib.parse.urlencode({"SearchTerm":term})
 result["search_url"]=url
 try:
  page,status=get(url);result["search_http"]=status
  parser=Links();parser.feed(page)
  links=list(dict.fromkeys(parser.found))
  result["linked_product_pages"]=len(links)
  result["items"]=[]
  for link in links[:MAX_ITEMS_EACH]:
   item={"detail_url":link}
   try:
    doc,http=get(link);item["http"]=http
    hits=prices_from_product_html(doc,link)
    item["valid_price_count"]=len(hits)
    if len(hits)==1:
     x=hits[0]
     item.update(x.as_dict())
     item["verified_eur_price"]=True
     # HTML may contradict structured availability; signal but do not hide this conflict.
     item["html_appears_out_of_stock"]=bool(re.search(r"Produkt aktuell ausverkauft",doc,re.I))
    else:item["verified_eur_price"]=False
   except urllib.error.HTTPError as e:item.update({"http":e.code,"verified_eur_price":False})
   except Exception as e:item.update({"error":type(e).__name__,"verified_eur_price":False})
   result["items"].append(item)
  result["verified_price_items"]=sum(x.get("verified_eur_price",False) for x in result["items"])
  result["status"]="READ"
 except urllib.error.HTTPError as e:
  result["search_http"]=e.code;result["status"]="HTTP_ERROR"
 except Exception as e:
  result["error_type"]=type(e).__name__;result["status"]="ERROR"
 return result
def main():
 res={"checked_utc":datetime.now(timezone.utc).isoformat(),
      "retailer":"Netto Marken-Discount","source":"Netto Online-Shop search and product Offer",
      "not_store_prices":True,"terms":[term_check(t) for t in TERMS]}
 res["total_priced_products"]=sum(x.get("verified_price_items",0) for x in res["terms"])
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(res,ensure_ascii=False))
 if res["total_priced_products"]==0:raise SystemExit(2)
if __name__=="__main__":main()
