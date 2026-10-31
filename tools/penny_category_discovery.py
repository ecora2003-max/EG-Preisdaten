#!/usr/bin/env python3
import json,time
from urllib.request import Request,urlopen
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError
from urllib.parse import urlencode
from pathlib import Path
ua="Ernaehrungsgedaechtnis-Research/0.5 (one-shot category discovery)"
host="https://www.penny.de"
with urlopen(Request(host+"/robots.txt",headers={"User-Agent":ua}),timeout=15) as f:
    rp=RobotFileParser();rp.parse(f.read(300000).decode("utf-8","replace").splitlines())
slugs=["fleisch-und-wurst","drogerie-und-haushalt","suessigkeiten-und-snacks","penny-ready","puda","best-moments","pflanzen","xxl-lebensmittel-fuer-alle","milprima","kuehlregal"]
result=[]
for slug in slugs:
    url=host+"/.rest/offers/by-category/2026-45/"+slug+"?"+urlencode({"region":"15A-01-56"})
    item={"category_slug":slug}
    if not rp.can_fetch(ua,url):
        item["status"]="robots disallows";result.append(item);continue
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"application/json"}),timeout=15) as f:
            item["status"]=f.status;obj=json.load(f)
        rows=obj.get("offerTiles",[]) if isinstance(obj,dict) else []
        item["response_keys"]=list(obj)[:12] if isinstance(obj,dict) else []
        item["items"]=len(rows) if isinstance(rows,list) else None
        item["examples"]=[{"title":x.get("title"),"price":x.get("price")} for x in rows[:2] if isinstance(x,dict)]
    except HTTPError as e:item["status"]=e.code
    except Exception as e:item["status"]="error";item["reason"]=str(e)[:120]
    result.append(item);time.sleep(.55)
Path("results").mkdir(exist_ok=True)
Path("results/penny_all_categories.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
