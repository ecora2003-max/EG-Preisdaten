#!/usr/bin/env python3
"""Follow up on assortment APIs with normal version / locale headers and a real ALDI category.

Queries at most 2 pages per source. No authentication, no rate escalation.
"""
import json,re,time
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse,urljoin,quote
from pathlib import Path
from datetime import datetime,timezone
UA="Ernaehrungsgedaechtnis-Research/1.3 (catalogue feasibility study)"
robots={}
checks=[]
def get(label,url,extra=None):
    u=urlparse(url);base=f"{u.scheme}://{u.netloc}"
    row={"test":label,"url":url}
    if base not in robots:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
                rp=RobotFileParser();rp.parse(f.read(200000).decode("utf-8","replace").splitlines());robots[base]=rp
        except HTTPError as e:robots[base]="allow" if e.code==404 else f"unknown robots {e.code}"
        except Exception as e:robots[base]="unknown robots "+type(e).__name__
    rule=robots[base]
    if (isinstance(rule,str) and rule!="allow") or (not isinstance(rule,str) and not rule.can_fetch(UA,url)):
        row["status"]="skipped robots";checks.append(row);return None
    try:
        headers={"User-Agent":UA,"Accept":"application/json,text/html;q=0.9,*/*;q=0.5","Accept-Language":"de-DE,de;q=0.9"}
        headers.update(extra or {})
        with urlopen(Request(url,headers=headers),timeout=18) as f:
            row["http"]=f.status;row["content_type"]=f.headers.get("Content-Type","")
            raw=f.read(3_000_000)
        try:
            obj=json.loads(raw)
            row["type"]=type(obj).__name__
            if isinstance(obj,dict):
                row["keys"]=list(obj)[:30]
                for k in ("categories","products","results","items","data"):
                    v=obj.get(k)
                    if isinstance(v,list):
                        row["array_key"]=k;row["count"]=len(v)
                        row["first_keys"]=list(v[0])[:45] if v and isinstance(v[0],dict) else []
                        row["first_sample"]={k:v[0][k] for k in ("id","title","name","price","categoryId","regularPrice","priceValue") if v and isinstance(v[0],dict) and k in v[0]}
                        break
            checks.append(row);time.sleep(.4);return obj
        except ValueError:
            html=raw.decode("utf8","replace");row["type"]="html";row["bytes"]=len(raw)
            m=re.search(r'<script[^>]*id=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',html,re.S|re.I)
            if m:
                data=json.loads(m.group(1))
                api=data.get("props",{}).get("pageProps",{}).get("apiData")
                if isinstance(api,str):
                    try:api=json.loads(api)
                    except ValueError:pass
                if isinstance(api,list):
                    row["ops"]=[x[0] for x in api if isinstance(x,list) and x]
                    row["response_keys_by_op"]=[{str(x[0]):list(x[1].get("res",{}))[:15] if isinstance(x[1].get("res"),dict) else type(x[1].get("res")).__name__} for x in api if isinstance(x,list) and len(x)>1 and isinstance(x[1],dict)][:10]
            checks.append(row);time.sleep(.4);return html
    except HTTPError as e:
        row["http"]=e.code;row["status"]="HTTP error"
    except Exception as e:row["status"]=type(e).__name__+":"+str(e)[:120]
    checks.append(row);return None

headers={"X-Client-Version":"17.0.5","X-Client-Platform":"android"}
for store in ("DE7434","7434"):
    base=f"https://product-catalog.lidlplus.com/api/app/v1/DE/store/{store}"
    get("Lidl product catalog with documented client compatibility headers "+store,base+"/categories",headers)
    get("Lidl product catalog search with compatibility headers "+store,base+"/search?q=Milch",headers)

raw=get("ALDI Nord assortment landing categories","https://www.aldi-nord.de/sortiment.html")
if isinstance(raw,str):
    # Inspect official on-page section links, select ONE genuine linked Sortiment category page.
    urls=list(dict.fromkeys(re.findall(r'href=["\x27]([^"\x27]*?/sortiment/[^"\x27#]*?\.html)',raw,re.I)))
    filtered=[]
    for u in urls:
        p=urljoin("https://www.aldi-nord.de",u)
        if p.startswith("https://www.aldi-nord.de/") and "/sortiment/" in p and "angebote" not in p:
            filtered.append(p)
    checks.append({"test":"ALDI Nord publicly linked assortment category pages","count_candidates":len(filtered),"sample_paths":[urlparse(u).path for u in filtered[:12]]})
    if filtered:
        get("ALDI Nord linked regular assortment category",filtered[0])

out={"checked_utc":datetime.now(timezone.utc).isoformat(),"checks":checks}
Path("results").mkdir(exist_ok=True)
Path("results/full_catalogue_followup.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
