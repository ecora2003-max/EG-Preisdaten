#!/usr/bin/env python3
"""Discover actual EDEKA product search and price endpoints from official pages.

The public offer API is not a complete product catalogue. Probe only a few
official catalogue pages; persist structural diagnostics, not HTML or cookies.
"""
from __future__ import annotations
import json,re,urllib.request,urllib.error,html,os
from urllib.parse import urljoin
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":raise SystemExit("Authorization flag missing")
UA="ErnaehrungsgedaechtnisResearch/3.1 (user-authorized EDEKA product catalog discovery)"
URLS=[
 "https://www.edeka.de/sortiment/",
 "https://www.edeka.de/sortiment/marken/",
 "https://www.edeka.de/sortiment/?query=Haferflocken",
 "https://www.edeka.de/sortiment/4311596029167/",
]
class Extract(HTMLParser):
 def __init__(self):
  super().__init__();self.forms=[];self.scripts=[];self.links=[];self.iframe=[];self.inputs=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="form":self.forms.append({k:a.get(k) for k in ("action","method","id","role")})
  if tag=="script" and a.get("src"):self.scripts.append(a.get("src"))
  if tag=="iframe" and a.get("src"):self.iframe.append(a.get("src"))
  if tag=="input":self.inputs.append({k:a.get(k) for k in ("name","type","id","placeholder")})
  if tag=="a" and a.get("href"):self.links.append(a.get("href"))
def inspect(url):
 r={"url":url}
 try:
  q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
  with urllib.request.urlopen(q,timeout=30) as f:
   buf=f.read(2_400_000);r["http"]=f.status
  doc=buf.decode("utf8","replace");r["length"]=len(doc)
  parser=Extract();parser.feed(doc)
  r["forms"]=parser.forms[:16]
  r["search_inputs"]=[x for x in parser.inputs if re.search(r"suche|search|query|artikel",str(x),re.I)][:30]
  r["iframes"]=parser.iframe[:20]
  r["scripts"]=[urljoin(url,x) for x in parser.scripts[:28]]
  r["product_links"]=[urljoin(url,x) for x in parser.links if re.search(r"/sortiment/[0-9]{7,15}/|/produkt[e]?(?:/|\.html)",x,re.I)][:20]
  r["endpoint_literal_samples"]=list(dict.fromkeys(
    re.findall(r'["\x27](/(?:[a-zA-Z0-9_-]+/){1,6}(?:search|products?|productsearch|artikel|sortiment)[^"\x27<>\s]{0,80})["\x27]',doc,re.I)))[:30]
  r["search_related_marker_counts"]={x:len(re.findall(x,doc,re.I)) for x in ("searchTerm","searchQuery","productSearch","productsApi","api.edeka","prodsearch","/search","artikelsuche","produktfinder","gtin","ean","preis","application/ld+json")}
  r["json_keys_samples"]=list(dict.fromkeys(re.findall(r'"(ean|gtin|sku|productId|productName|articleId|price|productSearch|products|items|hits|results)"\s*:',doc,re.I)))[:25]
  r["outcome"]="ANALYZED"
 except urllib.error.HTTPError as e:r["http"]=e.code;r["outcome"]="HTTP_ERROR"
 except Exception as e:r["outcome"]="ERROR";r["error"]=type(e).__name__
 return r
def main():
 data={"checked_utc":datetime.now(timezone.utc).isoformat(),"pages":[inspect(url) for url in URLS]}
 p=Path("results/edeka_product_page_discovery_20261031.json");p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(data,ensure_ascii=False))
if __name__=="__main__":main()
