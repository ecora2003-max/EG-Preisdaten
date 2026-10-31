#!/usr/bin/env python3
"""EDEKA sitemap product-catalogue inventory; bounded live discovery.

Permission has been asserted by the user for downloading and GitHub storage.
This diagnostic checks official sitemap nodes and *sample* Product page schema.
"""
import os,json,re,urllib.request,urllib.error,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":raise SystemExit("Authorization flag missing")
UA="ErnaehrungsgedaechtnisResearch/3.0 (authorized EDEKA product catalogue)"
BASE="https://www.edeka.de"
def req(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=30) as r:
  body=r.read(9_000_000)
  return body.decode("utf8","replace"),r.status
def urls(doc):
 try:
  root=ET.fromstring(doc)
  return root.tag.rsplit("}",1)[-1],[x.text for x in root.iter() if x.tag.rsplit("}",1)[-1]=="loc" and isinstance(x.text,str)]
 except ET.ParseError:return "UNPARSEABLE",re.findall(r"<loc>\s*([^<]+)</loc>",doc,re.I)
r={"checked_utc":datetime.now(timezone.utc).isoformat(),"checks":[]}
candidate=BASE+"/_sitemap.xml"
try:
 raw,status=req(candidate);tag,links=urls(raw)
 r["checks"].append({"url":candidate,"http":status,"root_tag":tag,"count":len(links),"first_urls":links[:65]})
 selections=[]
 if tag=="sitemapindex":
  selected=[x for x in links if re.search(r'produkt|sortiment|product|artikel',x,re.I)]
  selections=selected[:6] if selected else links[:8]
 else:selections=[]
 for url in selections:
  rec={"url":url}
  try:
   xml,status=req(url);tag2,links2=urls(xml)
   rec.update({"http":status,"root_tag":tag2,"count":len(links2),
     "example_product_urls":[x for x in links2 if re.search(r"/sortiment/|/produkt",x,re.I)][:15],
     "first_urls":links2[:7]})
  except urllib.error.HTTPError as e:rec["http"]=e.code
  except Exception as e:rec["error"]=type(e).__name__
  r["checks"].append(rec)
 sample=[]
 for x in r["checks"]:
  for u in x.get("example_product_urls",[]):
   if u.startswith(BASE) and u not in sample:sample.append(u)
 for url in sample[:4]:
  rec={"product_url":url}
  try:
   doc,status=req(url)
   rec.update({"http":status,"html_bytes":len(doc),"jsonld_product":bool(re.search(r'"@type"\s*:\s*"Product"',doc)),
    "ld_count":doc.count('application/ld+json'),"numeric_price_json":bool(re.search(r'"(?:price|offers)"\s*:',doc,re.I)),
    "title":(re.search(r"<title[^>]*>(.*?)</title>",doc,re.I|re.S).group(1)[:120] if re.search(r"<title[^>]*>(.*?)</title>",doc,re.I|re.S) else None)})
  except urllib.error.HTTPError as e:rec["http"]=e.code
  except Exception as e:rec["error"]=type(e).__name__
  r["checks"].append(rec)
except urllib.error.HTTPError as e:r["error_http"]=e.code
except Exception as e:r["error"]=type(e).__name__+":"+str(e)[:150]
out=Path("results/edeka_product_sitemap_probe_20261031.json");out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(r,ensure_ascii=False))
