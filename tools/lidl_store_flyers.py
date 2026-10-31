#!/usr/bin/env python3
"""Compare Lidl leaflets explicitly published on different store pages."""
import json,re,hashlib
from html import unescape
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
ua="Ernaehrungsgedaechtnis-Research/0.4 (read-only)"
urlbase="https://www.lidl.de"
pages={
"Prenzlauer Berg Choriner Str":"https://www.lidl.de/s/de-DE/filialen/berlin-pankow-prenzlauer-berg/choriner-str-64-u-64-a/",
"Berlin Mitte Müllerstr":"https://www.lidl.de/s/de-DE/filialen/berlin-mitte/muellerstr-48-48a/",
"Berlin Wilmersdorf Berliner Str":"https://www.lidl.de/s/de-DE/filialen/berlin-charlottenburg-wilmersdorf/berliner-str-26-27/"
}
out=[]
try:
    with urlopen(Request(urlbase+"/robots.txt",headers={"User-Agent":ua}),timeout=15) as r:
        rp=RobotFileParser();rp.parse(r.read(250000).decode("utf-8","replace").splitlines())
except HTTPError as e:
    rp=None if e.code==404 else str(e.code)
except Exception as e:
    rp=str(e)
for name,url in pages.items():
    x={"name":name,"url":url}
    if rp is not None and (isinstance(rp,str) or not rp.can_fetch(ua,url)):
        x["error"]="robots restrict or unavailable";out.append(x);continue
    try:
        with urlopen(Request(url,headers={"User-Agent":ua}),timeout=20) as r:
            x["http_status"]=r.status
            html=r.read(7_000_000).decode("utf-8","replace")
        ids=list(dict.fromkeys(re.findall(r'aktionsprospekt-\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{4}-[a-f0-9]{4,12}',unescape(html),re.I)))
        x["flyer_identifiers"]=ids[:15]
        x["known_future_flyer"]=any("02-11-2026" in i for i in ids)
        x["raw_has_future_date"]="02.11.2026" in html
        x["length"]=len(html)
        x["has_store_context"]="10435" in html if "Choriner" in name else None
    except HTTPError as e:
        x["http_status"]=e.code
    except Exception as e:
        x["error"]=str(e)[:140]
    out.append(x)
Path("results").mkdir(exist_ok=True)
Path("results/lidl_store_flyers.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
