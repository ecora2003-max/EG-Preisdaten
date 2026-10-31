#!/usr/bin/env python3
"""Read-only official GK self-scanning documentation evidence: store-specific
master-data downloads including prices and API authentication requirements.
Never probes a retailer's own gateway, performs store check-in, or fetches data.
"""
import json,re
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from html.parser import HTMLParser
from pathlib import Path

ua="Ernaehrungsgedaechtnis-Research/3.9 (public SDK architecture docs only)"
docroot="https://help.sap.com"
pages=[
 ("GK 6.0 self-scanning service architecture",
  "/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-backend/topics/clientsdk_self_scanning_using_self_scanning_service/architecture_overview.html"),
 ("GK store check-in context and master data format",
  "/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-client-bring-your-own-device/topics/customizingguide/general_configuration.html"),
 ("GK Self Scanning service general",
  "/doc/837c0d21848d4727919446d4dda976e6/6.0/en-US/submodules/self-scanning-backend/topics/clientsdk_self_scanning_using_self_scanning_service/general.html")
]
class Extract(HTMLParser):
    def __init__(self): super().__init__();self.t=[]
    def handle_data(self,x):
        if x.strip(): self.t.append(x.strip())
out={"timestamp":datetime.now(timezone.utc).isoformat(),"note":"Official public documentation, not actual protected customer-price databases","checks":[]}
try:
    with urlopen(Request(docroot+"/robots.txt",headers={"User-Agent":ua}),timeout=14) as r:
        rp=RobotFileParser();rp.parse(r.read(250000).decode("utf8","replace").splitlines())
except HTTPError as e:
    rp=None if e.code==404 else "unknown"
except Exception:
    rp="unknown"
for name,path in pages:
    url=docroot+path
    x={"source":name,"path":path}
    if rp=="unknown" or (rp is not None and not rp.can_fetch(ua,url)):
        x["result"]="SKIPPED robots inaccessible/disallows"
        out["checks"].append(x);continue
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html"}),timeout=20) as r:
            x["http"]=r.status
            html=r.read(1_500_000).decode("utf8","replace")
        parser=Extract();parser.feed(html)
        text=" ".join(parser.t)
        patterns={
           "store_scoped_master_data":r"(store specific|store-specific).{0,150}(master data|item information|prices)",
           "download_at_start_of_trip":r"download.{0,80}(master data|all necessary information|all.*information)",
           "prices_in_master_data":r"(item information\s*\+\s*prices|prices.{0,70}item|simplified master data)",
           "auth_headers_required":r"(authentication headers|authenticated devices|get access to internal components)",
           "in_store_qr_checkin_required":r"(scan a check.in code|entrance area of a store)",
           "store_identifying_key":r"(businessUnitId|store specific information)",
           "general_gk_product_service":r"(Basket Service|Self Scanning Service|Master Data Service)",
        }
        x["evidence"]={k:bool(re.search(p,text,re.I)) for k,p in patterns.items()}
        x["characters"]=len(text)
        x["result"]="DOCS_VERIFIED"
    except HTTPError as e:x["http"]=e.code;x["result"]="HTTP_ERROR"
    except Exception as e:x["result"]=type(e).__name__+":"+str(e)[:110]
    out["checks"].append(x)
Path("results").mkdir(exist_ok=True)
Path("results/gk_official_selfscan_docs.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2,ensure_ascii=False))
