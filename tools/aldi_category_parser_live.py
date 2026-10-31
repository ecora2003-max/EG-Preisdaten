#!/usr/bin/env python3
"""Two official ALDI Nord category pages, once each, verify priced catalogue parser."""
import json,sys
from datetime import datetime,timezone
from urllib.request import urlopen,Request
from urllib.robotparser import RobotFileParser
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalogues.aldi_nord import aldi_nord_catalogue_from_html
UA="Ernaehrungsgedaechtnis-Research/2.0 (bounded normal price catalogue live test)"
root="https://www.aldi-nord.de"
urls=[
 root+"/sortiment/milchprodukte/joghurt-quark-milchdesserts.html",
 root+"/sortiment/milchprodukte/milch-milchgetraenke.html"
]
with urlopen(Request(root+"/robots.txt",headers={"User-Agent":UA}),timeout=15) as r:
    rp=RobotFileParser();rp.parse(r.read(250000).decode("utf8","replace").splitlines())
data=[]
for url in urls:
    row={"url":url}
    try:
        if not rp.can_fetch(UA,url):raise ValueError("Blocked by robots")
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=20) as r:
            html=r.read(500000).decode("utf8","replace");row["status"]=r.status
        products,coverage=aldi_nord_catalogue_from_html(html)
        row["result"]="PASS"
        row["coverage"]=coverage
        row["samples"]=[p.to_dict() for p in products[:2]]
    except Exception as e:
        row["result"]="FAIL"
        row["reason"]=type(e).__name__+": "+str(e)[:140]
    data.append(row)
Path("results").mkdir(exist_ok=True)
Path("results/aldi_category_parser_live.json").write_text(json.dumps({"timestamp":datetime.now(timezone.utc).isoformat(),"tests":data},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(data,indent=2,ensure_ascii=False))
if any(x["result"]!="PASS" for x in data):raise SystemExit(1)
