#!/usr/bin/env python3
"""Netto price source discovery: HTML search form and permanent price reductions.

Bounded anonymous GETs to official retailer pages; only safe method/field/link
metadata and price candidate summaries are persisted. No cookies or credentials.
"""
import json,re,html,urllib.request,urllib.error
from urllib.parse import urljoin,urlsplit,urlencode
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path
BASE="https://www.netto-online.de"
UA="ErnaehrungsgedaechnisResearch/2.4 (targeted online price and nonoffer discovery)"
URLS=[
 ("home",BASE+"/"),
 ("permanent_reductions",BASE+"/ueber-netto/Preissenkung.chtm"),
 ("food",BASE+"/lebensmittel/c-N01"),
 ("muesli",BASE+"/cornflakes-muesli/c-N011501"),
 ("search_on_site",BASE+"/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPParametricSearch-SimpleOfferSearch?SearchTerm=Haferflocken"),
 ("search_browse",BASE+"/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewMMPParametricSearch-Browse?SearchTerm=Haferflocken"),
 ("search_legacy",BASE+"/search?q=Haferflocken"),
 ("search_intershop",BASE+"/search?query=Haferflocken"),
]
class Parser(HTMLParser):
 def __init__(self):
  super().__init__();self.forms=[];self.inputs=[];self.scripts=[];self.links=[];self.images=[];self.current=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="form":self.forms.append({k:a.get(k) for k in ("action","method","id","name","role")})
  if tag=="input" and len(self.inputs)<85:self.inputs.append({k:a.get(k) for k in ("name","type","id","placeholder")})
  if tag=="script" and a.get("src") and len(self.scripts)<130:self.scripts.append(a.get("src"))
  if tag=="a" and a.get("href"):
   self.links.append({"href":a.get("href"),"title":a.get("title"),"id":a.get("id")})
  if tag=="img" and a.get("src") and len(self.images)<350:self.images.append({"src":a.get("src"),"alt":a.get("alt")})
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
 with urllib.request.urlopen(req,timeout=23) as f:
  raw=f.read(2_000_000)
  return raw.decode("utf8","replace"),f.status
def inspect(name,url):
 d={"case":name,"url":url}
 try:
  doc,status=get(url); d["http"]=status;d["bytes"]=len(doc)
  p=Parser();p.feed(doc)
  d["search_forms"]=[f for f in p.forms if re.search("search|suche",json.dumps(f),re.I)][:10]
  d["search_inputs"]=[i for i in p.inputs if re.search("search|suche|suchbegriff|query|term",json.dumps(i),re.I)][:20]
  d["script_src_relevant"]=[urljoin(url,x) for x in p.scripts if re.search("search|suggest|price|offer|promo|site|main|shop",x,re.I)][:28]
  d["reduction_related_links"]=[{"url":urljoin(url,x["href"]),"label":x.get("title")} for x in p.links if re.search("Preissenkung|preis-senkung|dauerhaft|search|suchergeb",str(x["href"])+str(x.get("title")),re.I)][:50]
  d["reduction_related_images"]=[{"url":urljoin(url,x["src"]),"alt":x.get("alt")} for x in p.images if re.search("preissenkung|preis|dauerhaft",str(x["src"])+str(x.get("alt")),re.I)][:35]
  d["price_marker_counts"]={x:len(re.findall(x,doc,re.I)) for x in ["priceCurrency","product-price","product-tile","price__value","productPrice","searchString","SearchSuggest","preissenkung","data-ff-id"]}
  d["offers_markers"]=len(re.findall(r'"@type"\s*:\s*"Offer"',doc))
  d["product_links_count"]=len(set(x["href"] for x in p.links if re.search(r"/p-\d{6,15}",x["href"])))
  d["product_link_samples"]=[urljoin(url,x["href"]) for x in p.links if re.search(r"/p-\d{6,15}",x["href"])][:10]
  d["result"]="ANALYZED"
 except urllib.error.HTTPError as e:d.update({"http":e.code,"result":"HTTP_ERROR"})
 except Exception as e:d.update({"error":type(e).__name__,"result":"ERROR"})
 return d
def main():
 out={"checked_utc":datetime.now(timezone.utc).isoformat(),
      "tests":[inspect(name,url) for name,url in URLS]}
 Path("results").mkdir(exist_ok=True)
 p=Path("results/netto_more_price_sources_20261031.json")
 p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
