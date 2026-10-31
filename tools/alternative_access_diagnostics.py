#!/usr/bin/env python3
"""Conservative provider-access diagnostics, no authentication or fingerprint bypass."""
import json,re,hashlib,time
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlencode,urlparse
from datetime import datetime, timezone
from pathlib import Path
UA="Ernaehrungsgedaechtnis-Research/0.6 (public read-only diagnostics)"
checks=[]
robots={}
def probe(label,url,headers=None,limit=3_000_000,parse_json=False):
    base=f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    row={"source":label,"url":url}
    if base not in robots:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
                rp=RobotFileParser();rp.parse(f.read(300000).decode("utf-8","replace").splitlines());robots[base]=rp
        except HTTPError as exc:
            robots[base]="allowed" if exc.code==404 else f"robots HTTP {exc.code} - unknown"
        except Exception as exc:robots[base]="robots inaccessible: "+type(exc).__name__
    rp=robots[base]
    if (isinstance(rp,str) and rp!="allowed") or (not isinstance(rp,str) and not rp.can_fetch(UA,url)):
        row["outcome"]="SKIPPED robots unknown/restricted"
        checks.append(row);return None
    try:
        hs={"User-Agent":UA,"Accept":"application/json,text/html;q=0.9,*/*;q=0.5","Accept-Language":"de-DE,de;q=0.9"}
        hs.update(headers or {})
        with urlopen(Request(url,headers=hs),timeout=18) as response:
            row["status"]=response.status
            row["content_type"]=response.headers.get("Content-Type","")[:60]
            row["final_url"]=response.geturl()
            if urlparse(response.geturl()).netloc!=urlparse(url).netloc:
                row["outcome"]="redirect to other hostname; not parsed"
                checks.append(row);return None
            raw=response.read(limit+1)
        row["bytes"]=len(raw)
        if len(raw)>limit:row["outcome"]="too_large";checks.append(row);return None
        row["outcome"]="SUCCESS"
        if parse_json:
            try:
                obj=json.loads(raw)
                row["json_type"]=type(obj).__name__
                row["keys"]=list(obj)[:20] if isinstance(obj,dict) else []
                row["count"]=len(obj) if isinstance(obj,list) else None
            except ValueError:row["json_type"]="not_json"
        checks.append(row)
        time.sleep(.35)
        return raw.decode("utf-8","replace")
    except HTTPError as exc:
        row["status"]=exc.code
        row["outcome"]="HTTP ERROR"
        # Only sanitized error categories, not credentials/body.
        try:
            snippet=exc.read(400).decode("utf-8","replace")
            row["body_flags"]={"invalid_store":bool(re.search("storekey|store.key|store not found",snippet,re.I)),
                "missing_headers":bool(re.search("missing|header|version|client",snippet,re.I)),
                "challenge":bool(re.search("captcha|challenge|access denied",snippet,re.I))}
        except Exception:pass
    except Exception as exc:row["outcome"]="ERROR";row["error"]=type(exc).__name__+":"+str(exc)[:140]
    checks.append(row);return None

catalog=probe("Lidl public stores","https://stores.lidlplus.com/api/v4/DE",parse_json=True)
if catalog:
    try:
        lst=json.loads(catalog)
        in_berlin=[x for x in lst if isinstance(x,dict) and str(x.get("locality","")).casefold()=="berlin" and x.get("storeKey")]
        sample=in_berlin[0]
        key=str(sample["storeKey"])
        checks.append({"source":"Lidl selected Berlin store", "name":sample.get("name"),"storeKey":key,"postalCode":sample.get("postalCode")})
        path="https://offers.lidlplus.com/app/api/v4/DE/"+key+"/offers"
        # Explicit app compatibility headers as published by community clients,
        # transparent research UA, no cookies, OAuth tokens, or browser fingerprinting.
        probe("Lidl offers documented v4 (compatibility headers)",path,
              headers={"X-Client-Version":"17.0.5","X-Client-Platform":"android"},parse_json=True)
        # Compare with a known real store outside of Berlin.
        other=next((x for x in lst if isinstance(x,dict) and x.get("storeKey") and str(x.get("locality","")).casefold()!="berlin"),None)
        if other:
            checks.append({"source":"Lidl other store example","storeKey":other.get("storeKey"),"locality":other.get("locality")})
    except Exception as exc:checks.append({"source":"Lidl extract","error":type(exc).__name__+":"+str(exc)[:160]})
for label, url in (
    ("Marktguru public homepage","https://www.marktguru.de/"),
    ("Marktguru public offers search","https://www.marktguru.de/angebote"),
    ("KaufDA public Netto prospect","https://www.kaufda.de/Netto-Marken-Discount/Prospekt"),
    ("KaufDA public EDEKA prospect","https://www.kaufda.de/Edeka/Prospekt"),
    ("EDEKA prospect off-site regional page","https://www.edeka.de/angebote/"),
    ("Netto official leaflet info","https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm/1013"),
):
    raw=probe(label,url,limit=3_000_000)
    if raw:
        checks.append({"source":label+" public HTML markers",
                       "contains_offer":bool(re.search("angebot|prospekt",raw,re.I)),
                       "embedded_json":bool(re.search('application/json|__NEXT_DATA__|__NUXT_DATA__',raw,re.I)),
                       "postcode_field":bool(re.search('postalcode|zipcode|postcode|postleitzahl',raw,re.I)),
                       "length":len(raw)})
Path("results").mkdir(exist_ok=True)
out={"timestamp":datetime.now(timezone.utc).isoformat(),"description":"one-shot, no auth and no bypass, public endpoint diagnostics","checks":checks}
Path("results/alternative_access_diagnostics.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
