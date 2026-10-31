#!/usr/bin/env python3
"""ALDI Nord official site navigation: count real assortment categories from Next.js.

No product harvesting, one ordinary page GET. Inspect the navigation tree recursively,
distinguish category paths from marketing pages, show 20 routes for follow-up.
"""
import json,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
UA="Ernaehrungsgedaechnis-Research/3.2 (one-shot navigation coverage)"
base="https://www.aldi-nord.de"
uri=base+"/sortiment.html"
out={}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=10) as f:
        robot=RobotFileParser();robot.parse(f.read(250000).decode("utf-8","replace").splitlines())
    if not robot.can_fetch(UA,uri):raise ValueError("robots restricted")
    with urlopen(Request(uri,headers={"User-Agent":UA}),timeout=18) as f:
        raw=f.read(950000).decode("utf-8","replace")
    m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',raw,re.S|re.I)
    p=json.loads(m.group(1))["props"]["pageProps"]["page"]
    top=p.get("header",[])
    names=[]
    def walk(node,depth=0):
        if depth>20:return
        if isinstance(node,dict):
            v=node.get("path")
            if isinstance(v,str) and "/sortiment/" in v and v.endswith(".html"):
                names.append(v)
            for child in node.values():walk(child,depth+1)
        elif isinstance(node,list):
            for x in node:walk(x,depth+1)
    for h in top:walk(h.get("sideDrawerNavigation") or [])
    cats=sorted(set(names))
    out={"links":len(cats),"examples":cats[:60],
         "leaf_like":len([x for x in cats if x.count("/")>=5]),
         "top_level":len([x for x in cats if x.count("/")==4]),
         "nav_count":len(top)}
except Exception as e:out["error"]=type(e).__name__+": "+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_official_categories.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
