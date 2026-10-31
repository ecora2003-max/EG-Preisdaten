#!/usr/bin/env python3
import json,re
from urllib.request import Request,urlopen
from pathlib import Path
url="https://www.aldi-nord.de/sortiment/milchprodukte/joghurt-quark-milchdesserts.html"
with urlopen(Request(url,headers={"User-Agent":"Ernaehrungsgedaechtnis-Research/1.7 (single page price serialization inspect)"}),timeout=18) as f:
    page=f.read(500000).decode("utf8","replace")
out={}
for term in ('"currentPrice"','\\"currentPrice\\"','currentPrice','objectID','Topi Maxi'):
    start=page.find(term)
    before=page.rfind("<script",0,start) if start>=0 else -1
    after=page.rfind("</script",0,start) if start>=0 else -1
    out[term]={"at":start,"near":page[max(0,start-150):start+360] if start>=0 else None,
               "script_tag":page[before:before+200] if before>after else "not in script"}
Path("results").mkdir(exist_ok=True)
Path("results/aldi_price_serialization.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
