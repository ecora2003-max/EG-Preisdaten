#!/usr/bin/env python3
"""Test public store_id selection on official Netto brochure overview without stealth.

Only a few ordinary GETs. No bypass of HTTP403, anti-bot challenge or authentication.
"""
import re,json,hashlib
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.parse import urlparse,urljoin
from urllib.error import HTTPError
from pathlib import Path
from datetime import datetime,timezone

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.current={"href":dict(attrs).get("href",""),"text":""}
    def handle_data(self,txt):
        if self.current is not None:self.current["text"]+=txt
    def handle_endtag(self,tag):
        if tag=="a" and self.current is not None:
            if self.current["href"]:
                self.current["text"]=self.current["text"].strip()[:80]
                self.links.append(self.current)
            self.current=None

UA="Ernaehrungsgedaechtnis-Research/0.9 (read-only public flyer URL study)"
url="https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm"
urls=[
    url,
    url+"?stores_id=7679",
    url+"?stores_id=8135",
]
rows=[]
for u in urls:
    item={"url":u}
    try:
        with urlopen(Request(u,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"}),timeout=18) as response:
            item["status"]=response.status
            item["final_url"]=response.geturl()
            text=response.read(1_500_000).decode("utf-8","replace")
        item["sha256"]=hashlib.sha256(text.encode()).hexdigest()
        item["size"]=len(text)
        item["contains_access_denied"]=bool(re.search("Access Denied|Request Rejected|CAPTCHA",text,re.I))
        item["selected_store_id"] = re.findall(r'stores_id["\x27=: ]+([0-9]{3,6})',text,re.I)[:6]
        item["netto_prospect_pdf_urls"] = [x[:160] for x in
             dict.fromkeys(re.findall(r'(?:https?:)?//[^"\x27\s<>]+\.pdf(?:\?[^"\x27\s<>]*)?',text,re.I))][:12]
        links=Anchors();links.feed(text)
        chosen=[x for x in links.links if re.search(r"prospekt|blätter|filialangebot|angebote|\.pdf",x["href"]+" "+x["text"],re.I)]
        item["relevant_links"] = [{**x,"href":urljoin(u,x["href"])} for x in chosen[:15]]
        item["json_ld"]=text.count("application/ld+json")
        item["current_week_mentions"]=text.count("KW44")
        item["next_week_mentions"]=text.count("KW45")
        item["market_related_fields"]=list(dict.fromkeys(
            re.findall(r'"([a-zA-Z][A-Za-z0-9]*[Mm]arket[A-Za-z0-9]*)"\s*:',text)))[:15]
    except HTTPError as e:item["status"]=e.code
    except Exception as e:item["error"]=type(e).__name__+":"+str(e)[:170]
    rows.append(item)
Path("results").mkdir(exist_ok=True)
Path("results/netto_public_brochure_store_scope.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(rows,ensure_ascii=False,indent=2))
