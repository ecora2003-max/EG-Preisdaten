#!/usr/bin/env python3
"""One-shot EDEKA market coverage and Netto store-page structure diagnostics."""
import json,re,hashlib,time

# Website content terms prohibit automated collection absent explicit permission.
import os
if os.environ.get("EDEKA_PERMISSION_CONFIRMED") != "1":
    print("SKIPPED: EDEKA.de requires prior explicit permission for automated retrieval.")
    raise SystemExit(0)
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.parse import urlencode,urlparse
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
UA="Ernaehrungsgedaechtnis-Research/0.8 (single-shot public market offers)"
report={"utc":datetime.now(timezone.utc).isoformat(),"checks":[]}
class LinkParser(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.item=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            a=dict(attrs);self.item={"href":a.get("href"),"text":""}
        if tag=="script":
            self.script_attrs=dict(attrs)
    def handle_data(self,data):
        if self.item is not None:self.item["text"]+=data.strip()+" "
    def handle_endtag(self,tag):
        if tag=="a" and self.item is not None:
            self.item["text"]=self.item["text"].strip()[:120]
            self.links.append(self.item);self.item=None
def request(label,url,maxbytes=7_000_000):
    meta={"label":label,"url":url}
    try:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/html;q=0.9"}),timeout=20) as r:
            meta["http"]=r.status;meta["final_url"]=r.geturl()
            meta["type"]=r.headers.get("Content-Type","")
            b=r.read(maxbytes+1)
        meta["bytes"]=len(b)
        if len(b)>maxbytes:meta["outcome"]="limit exceeded";report["checks"].append(meta);return None
        meta["sha256"]=hashlib.sha256(b).hexdigest()
        report["checks"].append(meta);time.sleep(.4)
        return b.decode("utf-8","replace")
    except HTTPError as e:meta["http"]=e.code
    except Exception as e:meta["error"]=type(e).__name__+":"+str(e)[:140]
    report["checks"].append(meta);return None
url="https://www.edeka.de/api/marketsearch/markets?"+urlencode({"searchstring":"10405","size":4})
raw=request("EDEKA exact Berlin market search",url)
if raw:
    try:
        data=json.loads(raw);markets=data.get("markets",[])
        report["checks"].append({"label":"EDEKA candidate stores","total_count":data.get("totalCount"),
             "stores":[{"id":m.get("id"),"name":m.get("name"),"postal":m.get("zipCode_keyword"),
                        "region":m.get("region"),"url":m.get("url")} for m in markets[:4]]})
        for m in markets[:2]:
            market_id=str(m.get("id",""))
            if not market_id:continue
            u="https://www.edeka.de/eh/service/eh/offers?"+urlencode({"marketId":market_id,"limit":5})
            o=request("EDEKA offers actual market "+market_id,u)
            if not o:continue
            payload=json.loads(o)
            offers=payload.get("docs") or []
            report["checks"].append({"label":"EDEKA market-specific payload","market_id":market_id,
                 "national":payload.get("national"),"anzahl":payload.get("anzahl"),
                 "gueltig_von":payload.get("gueltig_von"),"gueltig_bis":payload.get("gueltig_bis"),
                 "docs_count":len(offers),
                 "sample": [{k:p.get(k) for k in ("angebotid","titel","preis","beschreibung","basicPrice","gueltig_bis","national")} for p in offers[:2]]})
    except Exception as e:report["checks"].append({"label":"EDEKA decode","error":str(e)[:160]})
for sid,slug in [
    ("7679","berlin-charlottenburg/wilmersdorfer-str-46"),
    ("5666","berlin/siemensdamm-43-44"),
]:
    url="https://www.netto-online.de/filialen/"+slug+"/"+sid+"/"
    html=request("Netto official market page "+sid,url)
    if not html:continue
    lp=LinkParser();lp.feed(html)
    links=[l for l in lp.links if re.search(r"angebote|prospekt|aktion|filial",l.get("href","") or "",re.I)]
    products=[]
    for phrase in ("Haribo Fruchtgummi","Giovanni Ferrari","Frosta Fertiggerichte","Filial-Angebote","ab Montag, 02.11.26"):
        at=html.find(phrase)
        if at<0:continue
        section=html[max(0,at-650):at+750]
        products.append({"phrase":phrase,"around_html":re.sub(r'\s+',' ',section)[:1100]})
    report["checks"].append({"label":"Netto market page structure","market_id":sid,
       "title_marker": "Netto Marken-Discount" in html,
       "anchors":links[:22],
       "nextweek_text": bool(re.search(r"02[.]11[.]26|02[.]11[.]2026",html)),
       "script_flags":{"json_ld":"application/ld+json" in html,"embedded_offers":"\"offers\"" in html,"product_list":"product-list" in html},
       "html_excerpts":products[:4]})
Path("results").mkdir(exist_ok=True)
Path("results/edeka_netto_market_source.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2,default=str))
