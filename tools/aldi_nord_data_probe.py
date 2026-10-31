#!/usr/bin/env python3
import json, re
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError
from datetime import datetime, timezone
from pathlib import Path
UA="Ernaehrungsgedaechtnis-Research/0.1 (public offer API validation)"
base="https://www.aldi-nord.de"
page=base+"/angebote-vorschau.html"
result={"source":page,"fetched_at_utc":datetime.now(timezone.utc).isoformat()}
try:
    with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as r:
        robots=r.read(300000).decode("utf-8","replace")
    p=RobotFileParser();p.parse(robots.splitlines())
    if not p.can_fetch(UA,page):
        result["status"]="skipped_robots_disallows"
    else:
        with urlopen(Request(page,headers={"User-Agent":UA}),timeout=15) as r:
            html=r.read(2_500_000).decode("utf-8","replace")
            result["http_status"]=r.status
        m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.S|re.I)
        if not m:result["status"]="no_next_data"
        else:
            next_data=json.loads(m.group(1))
            v=next_data.get("props",{}).get("pageProps",{}).get("apiData")
            result["api_data_type"]=type(v).__name__
            result["api_data_length"]=len(v) if isinstance(v,(str,list,dict)) else None
            if isinstance(v,str):
                result["api_data_prefix"]=v[:170]
                try:
                    v=json.loads(v)
                    result["api_data_parsed"]="json"
                except (ValueError,TypeError):
                    result["api_data_parsed"]="not_json"

            if isinstance(v,list):
                result["api_data_entries"]=len(v)
                result["query_types"]=[entry[0] for entry in v[:20] if isinstance(entry,list) and entry]
                offer_entries=[entry for entry in v if isinstance(entry,list) and len(entry)>1 and entry[0]=="OFFER_GET"]
                result["offer_get_entries"]=len(offer_entries)
                if offer_entries:
                    body=offer_entries[0][1]
                    result["offer_request"]=body.get("req") if isinstance(body,dict) else None
                    response=body.get("res") if isinstance(body,dict) else None
                    result["offer_response_keys"]=list(response)[:25] if isinstance(response,dict) else []
                    if isinstance(response,dict):
                        amap=response.get("algoliaDataMap")
                        if isinstance(amap,dict):
                            result["algolia_products_count"]=len(amap)
                            sample=[]
                            for sku,prod in list(amap.items())[:3]:
                                if isinstance(prod,dict):
                                    item={"product_key":sku,"keys":list(prod)[:45]}
                                    for field in ("name","title","productName","price","priceValue",
                                                  "priceNew","sellingSize","quantity","unit",
                                                  "productTitle","subHeadline","headline"):
                                        if field in prod:item[field]=str(prod[field])[:140]
                                    sample.append(item)
                            result["product_samples"]=sample

            if isinstance(v,dict):
                result["api_data_root_keys"]=list(v)[:30]
                found=[]
                offer_paths=[]
                def recurse(node,path="root",depth=0):
                    if depth>24 or len(found)>=10:return
                    if isinstance(node,dict):
                        if any(k.upper()=="OFFER_GET" for k in node):
                            offer_paths.append(path)
                        for k,x in node.items():
                            if any(t in k.lower() for t in ("offer","price","artikel","product")):
                                if len(offer_paths)<30:offer_paths.append(path+"."+str(k))
                            recurse(x,path+"."+str(k),depth+1)
                    elif isinstance(node,list) and node:
                        if isinstance(node[0],dict):
                            keys=set(node[0])
                            if len(keys & {"price","name","title","productName","sellingSize","itemPrice"})>=2:
                                found.append({"path":path,"count":len(node),"first_item_keys":list(node[0])[:30],
                                              "sample":{k:node[0].get(k) for k in ("name","title","productName","price","sellingSize") if k in node[0]}})
                        for x in node[:3]:recurse(x,path+"[]",depth+1)
                recurse(v)
                result["offer_paths"]=offer_paths[:20]
                result["candidate_offer_arrays"]=found[:8]
            result["status"]="analyzed"
except HTTPError as e:
    result["status"]="http_error";result["http_status"]=e.code
except Exception as e:
    result["status"]="error";result["reason"]=type(e).__name__+": "+str(e)[:180]
Path("results").mkdir(exist_ok=True)
Path("results/aldi-nord.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,ensure_ascii=False))
