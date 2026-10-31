#!/usr/bin/env python3
"""Minimal live check of independent EDEKA merchant webshops.

Checks only publicly exposed search pages on distinct independent seller domains,
with no borrowed session token; never treats online order prices as verified till
prices. Robots fail-closed, no authentication or evasion.
"""
import json,re
from urllib.parse import urlencode,urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime,timezone
ua="Ernaehrungsgedaechtnis-Research/3.6 (one-shot independent shop price access check)"
shops=["seidl-kulmbach.edeka.shop","ec-offenburg.edeka.shop"]
out={"checked_utc":datetime.now(timezone.utc).isoformat(),"checks":[]}
for domain in shops:
    base="https://"+domain
    row={"host":domain}
    url=base+"/index.php?"+urlencode({"cl":"search","searchparam":"Milch"})
    try:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
                robot=RobotFileParser();robot.parse(f.read(250000).decode("utf8","replace").splitlines())
        except HTTPError as e:robot=None if e.code==404 else "unknown"
        except Exception:robot="unknown"
        if robot=="unknown" or (robot is not None and not robot.can_fetch(ua,url)):
            row["status"]="SKIPPED robots inaccessible or disallow"
        else:
            with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html"}),timeout=20) as r:
                row["http"]=r.status;row["final_hostname"]=urlparse(r.geturl()).hostname
                page=r.read(900000).decode("utf-8","replace")
            row["bytes"]=len(page)
            row["price_indicators"]={name:len(re.findall(pattern,page,re.I)) for name,pattern in {
               "oxid_price":r'class=["\x27][^"\x27]*(?:price|product-price)[^"\x27]*["\x27]',
               "formatted_eur":r'\d{1,3}[.,]\d{2}\s*(?:€|&euro;)',
               "schema_org_offer":r'schema.org/Offer',
               "product_article":r'class=["\x27][^"\x27]*(?:productBox|product-item|productData)[^"\x27]*["\x27]'
            }.items()}
            row["has_product_titles"]=bool(re.search("Vollmilch|fettarme Milch|H-Milch",page,re.I))
            row["blocked"]=bool(re.search("captcha|access denied|403 forbidden",page,re.I))
            row["price_samples"]=list(dict.fromkeys(re.findall(r'(?:\d{1,3}[,.])?\d{1,3}[,.]\d{2}\s*(?:€|&euro;)',page,re.I)))[:5]
    except HTTPError as e:row["http"]=e.code
    except Exception as e:row["error"]=type(e).__name__+":"+str(e)[:120]
    out["checks"].append(row)
Path("results").mkdir(exist_ok=True)
Path("results/edeka_shop_real_prices.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(out,ensure_ascii=False,indent=2))
