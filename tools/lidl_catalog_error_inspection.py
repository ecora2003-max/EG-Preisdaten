#!/usr/bin/env python3
"""Conservative one-shot Lidl full-catalogue API error diagnostics.

Two documented endpoints, authentic store key. Inspect only status and sanitized
error fields; do not attempt credentials, proxying, WAF bypass or retries.
"""
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from datetime import datetime,timezone
from pathlib import Path
import json,re
UA="Ernaehrungsgedaechtnis-Research/2.4 (read-only full-price access validation)"
domain="https://product-catalog.lidlplus.com"
urls=[
    domain+"/api/app/v1/DE/store/DE7434/startingpage?date=2026-10-31",
    domain+"/api/app/v1/DE/store/DE7434/categories"
]
results=[]
try:
    with urlopen(Request(domain+"/robots.txt",headers={"User-Agent":UA}),timeout=13) as r:
        robot=RobotFileParser();robot.parse(r.read(250000).decode("utf8","replace").splitlines())
except HTTPError as e:robot=None if e.code==404 else "unknown"
except Exception:robot="unknown"
for url in urls:
    row={"path":url[len(domain):]}
    if robot=="unknown" or (robot is not None and not robot.can_fetch(UA,url)):
        row["result"]="skipped, robots not allowing";results.append(row);continue
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/json",
             "Accept-Language":"de-DE,de;q=0.9",
             "X-Client-Version":"17.0.5","X-Client-Platform":"android"})
    try:
        with urlopen(req,timeout=17) as resp:
            raw=resp.read(1000);row["status"]=resp.status
    except HTTPError as e:
        row["status"]=e.code;raw=e.read(1000)
    except Exception as e:
        row["result"]=type(e).__name__+":"+str(e)[:120];results.append(row);continue
    try:
        obj=json.loads(raw)
        row["json_keys"]=list(obj)[:14] if isinstance(obj,dict) else []
        # Prevent dumping potential credentials or sensitive request IDs
        row["public_error_info"]={k:str(obj[k])[:180] for k in ("error","code","message","status","title","detail")
                                  if k in obj and isinstance(obj[k],(str,int))}
    except Exception:
        row["response_type"]="non-JSON"
    results.append(row)
Path("results").mkdir(exist_ok=True)
Path("results/lidl_product_catalog_error.json").write_text(json.dumps({"date":datetime.now(timezone.utc).isoformat(),"checks":results},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(results,indent=2,ensure_ascii=False))
