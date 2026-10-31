#!/usr/bin/env python3
"""Trace branch-offer tiles and links on official Netto category HTML.

Netto /filialangebote itself returns HTTP 403 from GitHub Actions, so this
checks product-category pages that also display 'Filial-Angebote' tiles.
Read-only. Does not bypass 403 or carry session cookies.
"""
from __future__ import annotations
import html, json,re,urllib.request,urllib.error
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin

UA="ErnaehrungsgedaechnisResearch/2.3 (Netto public category and offers data analysis)"
BASE="https://www.netto-online.de"
URLS=[
 BASE+"/angebote/c-N07",
 BASE+"/lebensmittel-angebote/c-N07941",
 BASE+"/milch/c-N01010206",
]
OUT=Path("results/netto_offer_tiles_from_category_20261031.json")
class Texts(HTMLParser):
 def __init__(self):
  super().__init__();self.parts=[]
 def handle_data(self,value):
  value=" ".join(value.split())
  if value:self.parts.append(value)

def clean_excerpt(s):
 s=re.sub(r"\s+"," ",html.unescape(s))
 s=re.sub(r"https?://\S+","[URL]",s)
 return s[:650]
def get(url):
 rec={"url":url,"checked_utc":datetime.now(timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=24) as resp:
   body=resp.read(2_200_000)
   rec["http"]=resp.status
  doc=body.decode("utf8","replace")
  rec["bytes"]=len(body)
  rec["root_offer_term_count"]=len(re.findall(r"Filial-Angebote",doc,re.I))
  rec["live_offer_date_strings"]=list(dict.fromkeys(re.findall(
   r"(?:gültig\s+von|gültig\s+ab|Montag,\s*\d\d\.\d\d\.\d\d|Samstag,\s*\d\d\.\d\d\.\d\d)",doc,re.I)))[:20]
  rec["candidate_fields"]={k:len(re.findall(x,doc,re.I)) for k,x in {
   "valid_from":r"validFrom|validityStart|valid_from",
   "valid_to":r"validTo|validUntil|validityEnd",
   "offer_price":r"offerPrice|salePrice|priceReduced",
   "former_price":r"formerPrice|oldPrice|originalPrice",
   "store":r"stores_id|storeId|storeIdentifier",
   "filialangebot":r"filialangebote|filial-angebote",
   "sku":r'"sku"\s*:|productId|articleId',
   "embedded_api":r'(?:["\x27])/api/|(?:["\x27])/\.rest/|/services/',
  }.items()}
  rec["script_sources"]=list(dict.fromkeys(
    urljoin(url,html.unescape(v)) for v in re.findall(r'<script\b[^>]*\bsrc=["\x27]([^"\x27]+)',doc,re.I)
  ))[:70]
  rec["filial_offer_urls"]=list(dict.fromkeys(
    urljoin(url,html.unescape(v)) for v in re.findall(
      r'<a\b[^>]*href=["\x27]([^"\x27]+)',doc,re.I) if "filialangebote" in v.lower()
  ))[:35]
  # Capture text specifically from near the largest product-section heading.
  parser=Texts();parser.feed(doc)
  rec["text_token_count"]=len(parser.parts)
  indices=[i for i,t in enumerate(parser.parts) if t.casefold()=="filial-angebote"]
  rec["exact_filial_title_occurrences"]=len(indices)
  rec["filial_text_windows"]=[
   {"index":i,"before":parser.parts[max(0,i-5):i],"after":parser.parts[i:i+100]}
    for i in indices[-3:]
  ]
  rec["html_near_filial_heading"]=[
   clean_excerpt(doc[max(0,m.start()-80):m.start()+450]) for m in list(re.finditer("Filial-Angebote",doc,re.I))[-5:]
  ]
  # Non-secret, sanitized names of HTML script chunks with API URLs embedded.
  rec["literal_api_paths"]=list(dict.fromkeys(re.findall(
   r'["\x27]((?:/api/|/\.rest/|/services/)[A-Za-z0-9_./{}-]{3,125})["\x27]',doc,re.I)))[:35]
  rec["result"]="HTML_ANALYZED"
 except urllib.error.HTTPError as e:
  rec["http"]=e.code;rec["result"]="HTTP_ERROR"
 except Exception as e:
  rec["error_type"]=type(e).__name__;rec["error"]=str(e)[:125];rec["result"]="ERROR"
 return rec

def main():
 out={"observed_at_utc":datetime.now(timezone.utc).isoformat(),
      "cases":[get(x) for x in URLS],
      "warning":"Webshop category promo tiles do not prove any selected branch has these exact prices."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
