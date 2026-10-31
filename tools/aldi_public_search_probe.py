#!/usr/bin/env python3
"""One read-only Algolia product-search query using the website's public search-only config.

No app secrets written to disk, no auth bypass, and no bulk catalog download.
If credentials are absent, query is skipped. Results are metadata and 2 samples.
"""
import json,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import quote
from pathlib import Path
from datetime import datetime,timezone
UA="Ernaehrungsgedaechtnis-Research/2.2 (single public product-search integration test)"
site="https://www.aldi-nord.de"
source=site+"/sortiment/milchprodukte/joghurt-quark-milchdesserts.html"
out={"checked_utc":datetime.now(timezone.utc).isoformat(),"source":source}
try:
    with urlopen(Request(site+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
        rp=RobotFileParser();rp.parse(f.read(250000).decode("utf-8","replace").splitlines())
    if not rp.can_fetch(UA,source):
        raise ValueError("site robots disallows")
    with urlopen(Request(source,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=18) as f:
        html=f.read(450000).decode("utf8","replace")
    m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.I|re.S)
    if not m:raise ValueError("no Next hydration")
    p=json.loads(m.group(1))["props"]["pageProps"]
    cfg=p.get("algoliaConfig",{})
    out["config_keys"]=list(cfg)[:30] if isinstance(cfg,dict) else []
    initial=p.get("algoliaState",{}).get("initialResults",{})
    out["index_names"]=list(initial)[:5]
    index=next(iter(initial))
    if isinstance(cfg,dict):
        appid=next((cfg[k] for k in ("appId","applicationId","appID") if isinstance(cfg.get(k),str)),None)
        key=next((cfg[k] for k in ("apiKey","searchApiKey","searchKey") if isinstance(cfg.get(k),str)),None)
        if not (appid and key):
            # Nested algoliaConfig can have config/client references, but do not guess any credentials.
            out["status"]="public search-only credentials not at expected config keys"
        else:
            host=f"https://{appid}-dsn.algolia.net"
            api=f"{host}/1/indexes/{quote(index,safe='')}/query"
            try:
                with urlopen(Request(host+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
                    bot=RobotFileParser();bot.parse(f.read(150000).decode("utf8","replace").splitlines())
                allowed=bot.can_fetch(UA,api)
            except HTTPError as e:
                allowed=e.code==404
            except Exception:allowed=False
            if not allowed:out["status"]="Algolia robots restrictions/unknown"
            else:
                body=json.dumps({"query":"Tofu","hitsPerPage":5,"page":0}).encode()
                req=Request(api,data=body,method="POST",
                            headers={"User-Agent":UA,"Content-Type":"application/json",
                                     "X-Algolia-Application-Id":appid,
                                     "X-Algolia-API-Key":key})
                try:
                    with urlopen(req,timeout=18) as f:
                        obj=json.load(f);out["status"]=f.status
                    out["result"]="one search queried"
                    out["pagination"]={k:obj.get(k) for k in ("nbHits","nbPages","page","hitsPerPage")}
                    items=obj.get("hits") or []
                    out["item_keys"]=list(items[0])[:35] if items and isinstance(items[0],dict) else []
                    out["samples"]=[{"objectID":x.get("objectID"),"name":x.get("name"),
                                     "price":x.get("currentPrice",{}).get("priceValue"),
                                     "pack":x.get("salesUnit")} for x in items[:2] if isinstance(x,dict)]
                except HTTPError as e:out["status"]="HTTP "+str(e.code)
                except Exception as e:out["status"]=type(e).__name__+":"+str(e)[:120]
except Exception as e:
    out["error"]=type(e).__name__+":"+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_public_search_probe.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
