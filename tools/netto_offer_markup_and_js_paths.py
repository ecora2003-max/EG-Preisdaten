#!/usr/bin/env python3
"""Netto category page: inspect store-offer card markup and public JS route names.

This checks only already publicly linked retailer pages/scripts; no bypass of
blocked /filialangebote page. Capture bounded public offer markup, route names
and JS source size, not entire source code or cookies.
"""
import re,json,urllib.request,urllib.error,html
from datetime import datetime,timezone
from pathlib import Path
UA="ErnaehrungsgedaechnisResearch/2.4 (public branch offer markup/API path research)"
PAGE="https://www.netto-online.de/angebote/c-N07"
JS="https://www.netto-online.de/INTERSHOP/static/WFS/Plus-NettoDE-Site/-/-/de_DE/js/theme.min.js?lastModified=1793444455748"
OUT=Path("results/netto_offer_markup_and_js_paths_20261031.json")
def get(url,limit):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript"}),timeout=30) as f:
  data=f.read(limit+1)
  if len(data)>limit:raise ValueError("Max bytes exceeded")
  return data.decode("utf-8","replace"),f.status

def run():
 o={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"cases":[]}
 p={"asset":"offer-category-html","url":PAGE}
 try:
  text,status=get(PAGE,1200000)
  p["http"]=status;p["length"]=len(text)
  h=re.search(r'<h2[^>]*>\s*Filial-Angebote\s*</h2>',text,re.I)
  if h:
   section=text[h.end():h.end()+90000]
   p["date"]=re.search(r'gültig\s+von\s+([^<]{10,100})',section,re.I).group(1) if re.search(r'gültig\s+von\s+([^<]{10,100})',section,re.I) else None
   p["section_length_analyzed"]=len(section)
   for name in ("Gurken","Grünländer Scheiben","Zewa Toilettenpapier","Coca-Cola oder Zero"):
    m=re.search(re.escape(name),section,re.I)
    if m:
     p.setdefault("offer_markup_examples",[]).append({
      "name":name,
      "around":section[max(0,m.start()-1050):m.end()+1250].replace("\n"," ")[:2350]
     })
   refs=sorted(set(re.findall(r'(?i)(?:Offers|Store)-[A-Za-z0-9_/-]{5,110}',text)))
   p["intershop_route_literals"]=refs[:65]
   p["offer_data_attributes"]=sorted(set(re.findall(r'\b(data-[a-z0-9_-]+)=',section,re.I)))[:80]
  else:p["missing_offer_heading"]=True
 except Exception as e:p["error"]=type(e).__name__+":"+str(e)[:100]
 o["cases"].append(p)
 q={"asset":"netto-theme-js","url":JS}
 try:
  text,status=get(JS,8500000)
  q["http"]=status;q["length"]=len(text)
  expr=r'(?i)(?:Offers|StoreOffers|Filialangebote|Store)-[A-Za-z][A-Za-z0-9_/-]{4,125}'
  q["intershop_route_literals"]=sorted(set(re.findall(expr,text)))[:160]
  for term in ("store-offers","storeOffers","filialangebote","Offers-Get","StoreOffers-","GetStoreOffer","storeId","store-offers-navigation"):
   hits=list(re.finditer(re.escape(term),text,re.I))
   q.setdefault("term_occurrences",{})[term]=len(hits)
   if hits:
    q.setdefault("contexts",{})[term]=[
      re.sub(r'https?://[^\s"\'\\]+','[URL]',text[max(0,m.start()-90):m.end()+150])[:260]
      for m in hits[:3]
    ]
 except Exception as e:q["error"]=type(e).__name__+":"+str(e)[:100]
 o["cases"].append(q)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(o,ensure_ascii=False))
if __name__=="__main__":run()
