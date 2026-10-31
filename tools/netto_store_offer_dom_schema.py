#!/usr/bin/env python3
"""Netto's public offers HTML: inspect exact offer-card price elements.

Read-only and one page. Only aggregate DOM structure and five public offers
are saved. Does not infer prices from 'UVP' or 'statt' without labeled field.
"""
import json,urllib.request,urllib.error,re
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup

URL="https://www.netto-online.de/angebote/c-N07"
UA="ErnaehrungsgedaechnisResearch/2.4 (public store-offer card structure test)"
OUT=Path("results/netto_store_offer_dom_schema_20261031.json")

def main():
 out={"url":URL,"checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"Netto HTML store offers; not all normal shelf prices"}
 try:
  with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=25) as f:
   src=f.read(1400000)
   out["http"]=f.status
  soup=BeautifulSoup(src,"html.parser")
  h=soup.find("h2",string=lambda s:s and s.strip()=="Filial-Angebote")
  out["offer_heading_present"]=bool(h)
  header=h.find_parent("header") if h else None
  out["header_text"]=header.get_text(" ",strip=True)[:130] if header else None
  # Product cards are outside online shop result cards and use their own ID.
  cards=soup.select(".tc-store-product-tile")
  out["offer_tile_count"]=len(cards)
  out["distinct_ff_ids"]=len(set(x.get("data-ff-id") for x in cards if x.get("data-ff-id")))
  out["samples"]=[]
  for tile in cards[:8]:
   row={"ff_id":tile.get("data-ff-id"),
        "name":tile.select_one(".tc-product-name").get_text(" ",strip=True) if tile.select_one(".tc-product-name") else None,
        "plain_text":tile.get_text(" | ",strip=True)[:800],
        "price_class_texts":[],
        "links":[]}
   for tag in tile.find_all(True):
    classes=" ".join(tag.get("class",[]))
    if re.search(r"price|strikethrough|saving|original|app-?",classes,re.I):
     val=tag.get_text(" ",strip=True)
     if val and len(val)<140:
      row["price_class_texts"].append({"classes":classes[:150],"value":val[:120]})
    if tag.name=="a" and tag.get("href"):
     row["links"].append({"href":tag.get("href","")[:250],"classes":classes[:120]})
   row["price_class_texts"]=row["price_class_texts"][:28]
   row["links"]=row["links"][:6]
   out["samples"].append(row)
  out["result"]="DOM_VERIFIED"
 except urllib.error.HTTPError as e:
  out["result"]="HTTP_ERROR";out["http"]=e.code
 except Exception as e:
  out["result"]="ERROR";out["error_class"]=type(e).__name__;out["error"]=str(e)[:140]
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
