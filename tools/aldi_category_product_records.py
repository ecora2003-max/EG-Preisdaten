#!/usr/bin/env python3
"""Verify ALDI Nord normal-price product records in official server-provided page JSON."""
import json,re
from collections import Counter
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime,timezone
UA="Ernaehrungsgedaechtnis-Research/1.6 (read-only product-list JSON validation)"
base="https://www.aldi-nord.de"
url=base+"/sortiment/milchprodukte/joghurt-quark-milchdesserts.html"
out={"url":url,"date":datetime.now(timezone.utc).isoformat()}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as resp:
        parser=RobotFileParser();parser.parse(resp.read(300000).decode("utf-8","replace").splitlines())
    if not parser.can_fetch(UA,url):
        out["status"]="SKIPPED robots"
    else:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=20) as resp:
            raw=resp.read(1_500_000).decode("utf8","replace")
            out["status"]=resp.status
        m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',raw,re.S|re.I)
        if not m:out["result"]="No __NEXT_DATA__"
        else:
            node=json.loads(m.group(1))
            page=node.get("props",{}).get("pageProps",{})
            price_records=[]
            sampled_paths=[]
            kinds=Counter()
            def walk(n,path="page",depth=0):
                if depth>32:return
                if isinstance(n,dict):
                    if "currentPrice" in n or "promotionPrices" in n:
                        kinds["priced_nodes"]+=1
                        if len(price_records)<5:
                            price_records.append({"path":path,"keys":list(n)[:45],
                                "name":n.get("name") or n.get("title"),
                                "brandName":n.get("brandName"),
                                "objectID":n.get("objectID"),
                                "currentPrice":n.get("currentPrice"),
                                "promotionPrices_count":len(n.get("promotionPrices",[])) if isinstance(n.get("promotionPrices"),list) else None})
                    if "objectID" in n:kinds["object_id_nodes"]+=1
                    for k,v in n.items():walk(v,path+"."+str(k),depth+1)
                elif isinstance(n,list):
                    if n and isinstance(n[0],dict) and len(sampled_paths)<15:
                        sampled_paths.append({"path":path,"array_length":len(n),"first_keys":list(n[0])[:20]})
                    for i,v in enumerate(n):walk(v,path+f"[{i}]",depth+1)
            walk(page)
            out["page_keys"]=list(page)[:28] if isinstance(page,dict) else None
            out["counts"]=dict(kinds)
            out["sample_records"]=price_records
            out["object_list_paths"]=sampled_paths
            out["result"]="parsed"
except HTTPError as e:out["status"]=e.code
except Exception as e:out["status"]=type(e).__name__+":"+str(e)[:140]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_category_product_records.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
