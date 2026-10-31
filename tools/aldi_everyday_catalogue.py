#!/usr/bin/env python3
"""Inspect one official ALDI Nord everyday assortment page for structured regular prices."""
import json,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime, timezone
ua="Ernaehrungsgedaechtnis-Research/1.4 (ALDI Nord ordinary item price schema)"
base="https://www.aldi-nord.de"
url=base+"/sortiment/milchprodukte/joghurt-quark-milchdesserts.html"
report={"page":url}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=15) as f:
        rp=RobotFileParser();rp.parse(f.read(250000).decode("utf8","replace").splitlines())
    if not rp.can_fetch(ua,url):
        report["result"]="SKIPPED robots disallows"
    else:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html","Accept-Language":"de-DE"}),timeout=20) as r:
            html=r.read(2_000_000).decode("utf-8","replace")
            report["http"]=r.status
        report["html_length"]=len(html)
        m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.S|re.I)
        if not m:report["result"]="no structured NEXT data"
        else:
            nextd=json.loads(m.group(1))
            data=nextd.get("props",{}).get("pageProps",{}).get("apiData")
            data=json.loads(data) if isinstance(data,str) else data
            report["api_data_type"]=type(data).__name__
            if isinstance(data,list):
                report["operations"]=[str(r[0]) for r in data if isinstance(r,list) and r]
                for v in data:
                    if not isinstance(v,list) or len(v)<2 or not isinstance(v[1],dict):continue
                    resp=v[1].get("res")
                    operation=str(v[0])
                    item={"operation":operation,"response_type":type(resp).__name__}
                    if isinstance(resp,dict):item["root_keys"]=list(resp)[:35]
                    if isinstance(resp,list):item["list_length"]=len(resp);item["first_keys"]=list(resp[0])[:40] if resp and isinstance(resp[0],dict) else []
                    matches=[]
                    def discover(node,path="res",depth=0):
                        if depth>10 or len(matches)>=7:return
                        if isinstance(node,dict):
                            if {"currentPrice","price","priceValue","regularPrice","promotionPrices"} & set(node):
                                matches.append({"path":path,"keys":list(node)[:35],
                                                "name":node.get("name") or node.get("title"),
                                                "price":node.get("currentPrice",node.get("price",node.get("priceValue")))})
                            for k,val in list(node.items())[:30]:
                                discover(val,path+"."+str(k),depth+1)
                        elif isinstance(node,list):
                            for i,el in enumerate(node[:4]):discover(el,path+f"[{i}]",depth+1)
                    discover(resp)
                    item["price_records"]=matches[:5]
                    report.setdefault("operations_detail",[]).append(item)
                report["result"]="NEXT data parsed"
except HTTPError as e:report["result"]="HTTP error";report["status"]=e.code
except Exception as e:report["result"]=type(e).__name__+":"+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_everyday_catalogue.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf8")
print(json.dumps(report,ensure_ascii=False,indent=2,default=str))
