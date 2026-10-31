#!/usr/bin/env python3
"""One-shot ordinary-product-search pages: PENNY and Kaufland.

Determines whether published search is a *current regular-price* listing
or offers/marketing only. At most four public HTML GETs; no guesses about
private endpoints, authentication tricks or access bypass.
"""
import json,re
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from datetime import datetime,timezone
from pathlib import Path
ua="Ernaehrungsgedaechtnis-Research/3.4 (read-only normal-price search feasibility)"
checks=[]
urls={
"PENNY search?q=Milch":"https://www.penny.de/suche?q=Milch",
"PENNY search?query=Milch":"https://www.penny.de/suche?query=Milch",
"Kaufland retail homepage search":"https://filiale.kaufland.de/suche.html?q=Milch",
"Kaufland retail product search":"https://filiale.kaufland.de/suche.html?search=Milch"
}
robots={}
for label,url in urls.items():
    base=f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    row={"test":label,"url":url}
    if base not in robots:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
                p=RobotFileParser();p.parse(f.read(250000).decode("utf8","replace").splitlines());robots[base]=p
        except HTTPError as e:robots[base]=None if e.code==404 else "blocked"
        except Exception:robots[base]="blocked"
    rp=robots[base]
    if rp=="blocked" or (rp is not None and not rp.can_fetch(ua,url)):
        row["result"]="SKIPPED robots";checks.append(row);continue
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html,application/json;q=0.9"}),timeout=17) as f:
            row["status"]=f.status
            row["final_path"]=urlparse(f.geturl()).path
            body=f.read(600000).decode("utf-8","replace")
        row["bytes"]=len(body)
        row["mentions_milch"]=len(re.findall(r"milch",body,re.I))
        row["structured_product_count"]=len(re.findall(r'"@type"\s*:\s*"Product"',body,re.I))
        row["price_field_occurrences"]={k:len(re.findall(k,body,re.I)) for k in
           (r'"currentPrice"',r'"regularPrice"',r'"price"',r'"productId"',r'"basePrice"')}
        row["currency_in_html"]=len(re.findall(r"\b\d+[,.]\d{2}\s*€",body))
        row["title"]=(re.search(r"<title[^>]*>(.*?)</title>",body,re.I|re.S).group(1)[:120]
                      if re.search(r"<title[^>]*>(.*?)</title>",body,re.I|re.S) else None)
        row["result"]="HTML inspected, individual store regular prices not yet proven"
    except HTTPError as e:row["status"]=e.code
    except Exception as e:row["error"]=type(e).__name__+":"+str(e)[:140]
    checks.append(row)
Path("results").mkdir(exist_ok=True)
Path("results/penny_kaufland_normal_search.json").write_text(json.dumps(
 {"checked_utc":datetime.now(timezone.utc).isoformat(),"tests":checks},
 ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(checks,ensure_ascii=False,indent=2))
