#!/usr/bin/env python3
"""Extract ALDI Nord's publicly rendered category navigation, without bulk crawling.

Unlike the simple HTML link test, inspect CMS/Next.js embedded navigation and
category metadata. Output only path/counts, no catalogue copied.
"""
import json,re
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
UA="Ernaehrungsgedaechtnis-Research/2.9 (one-shot taxonomy discovery)"
base="https://www.aldi-nord.de"
page=base+"/sortiment.html"
result={"path":"/sortiment.html"}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
        rp=RobotFileParser();rp.parse(f.read(300000).decode("utf8","replace").splitlines())
    if not rp.can_fetch(UA,page):raise ValueError("robots disallowed")
    with urlopen(Request(page,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=18) as f:
        html=f.read(850000).decode("utf8","replace");result["http"]=f.status
    match=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.I|re.S)
    if match:
        data=json.loads(match.group(1))
        p=data.get("props",{}).get("pageProps",{})
        result["pageProps_keys"]=list(p)[:28]
        found=[]
        def walk(node,path="",depth=0):
            if depth>12 or len(found)>120:return
            if isinstance(node,dict):
                for k,v in node.items():
                    if isinstance(v,str) and ("/sortiment/" in v or "sortiment/" in v):
                        if len(v)<300:found.append({"path":path+"."+k,"link":v[:180]})
                    if isinstance(v,(dict,list)):walk(v,path+"."+str(k),depth+1)
            elif isinstance(node,list):
                for i,v in enumerate(node[:150]):
                    walk(v,path+f"[{i}]",depth+1)
        walk(p)
        unique={x["link"]:x for x in found}
        result["found_link_count"]=len(unique)
        result["links"]=list(unique.values())[:30]
        result["route_keys"]={k:list(v)[:18] for k,v in p.items() if isinstance(v,dict) and re.search("navig|categor|sortiment|product",k,re.I)}
    else:result["result"]="No Next data"
except HTTPError as e:result["http"]=e.code
except Exception as e:result["error"]=type(e).__name__+":"+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_navigation_paths.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(result,indent=2,ensure_ascii=False))
