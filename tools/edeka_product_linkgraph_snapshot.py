#!/usr/bin/env python3
"""Snapshot bounded publicly visible EDEKA product details via linked product pages.

The official product search page advertises about 6000 products, but the
automated listing endpoint responded HTTP 403. This crawler requests only
direct public product pages linked from an initial official sample. It cannot
claim complete product catalog coverage. Stops on 403/429 and uses a delay.
"""
from __future__ import annotations
import json,re,html,os,time,collections,urllib.request,urllib.error
from urllib.parse import urljoin,urlparse
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone

if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":raise SystemExit("Missing authorization flag")
ROOT=Path("data/edeka/2026-10-31")
ROOT.mkdir(parents=True,exist_ok=True)
UA="ErnaehrungsgedaechtnisResearch/3.1 (authorized bounded EDEKA product snapshot)"
SEEDS=["4311596029167","4311501006382","4311501170885","4311501025062"]
MAX_PAGES=240
SLEEP_SEC=0.45
PRODUCT_RE=re.compile(r"^https://www\.edeka\.de/sortiment/(\d{12,14})/$")
class ProductParser(HTMLParser):
 def __init__(self):
  super().__init__();self.h1=[];self.inside_h1=False;self.links=[];self.og_title=None
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="h1":self.inside_h1=True
  if tag=="a" and d.get("href"):self.links.append(d["href"])
  if tag=="meta" and d.get("property")=="og:title":self.og_title=d.get("content")
 def handle_data(self,v):
  if self.inside_h1:self.h1.append(v)
 def handle_endtag(self,tag):
  if tag=="h1":self.inside_h1=False
def fetch(gtin):
 u=f"https://www.edeka.de/sortiment/{gtin}/"
 with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=25) as r:
  data=r.read(450000)
  if r.status!=200:raise RuntimeError("non-200 product page")
 return data.decode("utf8","replace")
def main():
 started=datetime.now(timezone.utc).isoformat()
 queue=collections.deque(SEEDS)
 seen=set();items=[];errors=[];edges=0;stop=None
 while queue and len(seen)<MAX_PAGES:
  ean=queue.popleft()
  if ean in seen:continue
  seen.add(ean)
  try:
   raw=fetch(ean)
   parser=ProductParser();parser.feed(raw)
   name=html.unescape(re.sub(r"\s+"," "," ".join(parser.h1))).strip()
   # The retailer uses site-dialog headings before its actual product heading.
   site_chrome="Mein EDEKA: Praktische Infos und Angebote Durchsuche EDEKA.de "
   if name.startswith(site_chrome):name=name[len(site_chrome):].strip()
   if not name and parser.og_title:name=html.unescape(parser.og_title).strip()
   if name:
    items.append({"product_page_id":ean,"gtin":ean,
                  "name":name,"source_url":f"https://www.edeka.de/sortiment/{ean}/",
                  "price_eur":None,"price_kind":"NOT_PUBLISHED",
                  "source":"EDEKA_PUBLIC_PRODUCT_PAGE","market_id":None})
   links=set()
   for href in parser.links:
    link=urljoin(f"https://www.edeka.de/sortiment/{ean}/",href)
    m=PRODUCT_RE.fullmatch(link)
    if m:links.add(m.group(1))
   for found in sorted(links):
    if found not in seen and found not in queue:queue.append(found)
   edges+=len(links)
  except urllib.error.HTTPError as exc:
   errors.append({"id":ean,"http":exc.code})
   if exc.code in (403,429):stop=f"HTTP_{exc.code}_STOP";break
  except Exception as exc:
   errors.append({"id":ean,"error":type(exc).__name__})
  if len(seen)%30==0:print(f"PROGRESS pages={len(seen)} products={len(items)} queued={len(queue)}",flush=True)
  time.sleep(SLEEP_SEC)
 if not stop:
  stop="REACHED_MAX_PAGE_CAP" if len(seen)>=MAX_PAGES else "DISCOVERY_GRAPH_EXHAUSTED"
 manifest={
  "checked_utc":datetime.now(timezone.utc).isoformat(),
  "retrieved_from":"https://www.edeka.de/sortiment/{gtin}/",
  "start_utc":started,
  "data_type":"PUBLIC_PRODUCT_PAGE_SUBSET",
  "all_products_complete":False,
  "real_prices_present":False,
  "published_full_search_size":"about 6000 products, not tested as a stable complete count",
  "reason_not_complete":"Product search pages were HTTP 403 in GitHub Actions; link-graph crawl is partial.",
  "pages_attempted":len(seen),"products_parsed":len(items),"links_seen":edges,
  "queue_remaining":len(queue),"stopped_due_to":stop,
  "errors":errors[:40],
  "public_snapshot_permission":"User reported authorization to download and publish EDEKA catalogues; terms not independently checked."
 }
 (ROOT/"product_page_subset.json").write_text(json.dumps({"manifest":manifest,"products":items},ensure_ascii=False,indent=2)+"\n")
 (ROOT/"product_page_subset_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
 print("DONE="+json.dumps(manifest,ensure_ascii=False),flush=True)
 if not items:raise SystemExit(2)
if __name__=="__main__":main()
