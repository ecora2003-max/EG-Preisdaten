#!/usr/bin/env python3
"""Inspect one ALDI Nord assortment page's rendered product tiles and regular prices."""
import json,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from pathlib import Path
url="https://www.aldi-nord.de/sortiment/milchprodukte/joghurt-quark-milchdesserts.html"
UA="Ernaehrungsgedaechtnis-Research/1.5 (read-only rendered regular prices)"
root="https://www.aldi-nord.de"
report={"url":url}
try:
    with urlopen(Request(root+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
        rp=RobotFileParser();rp.parse(f.read(250000).decode("utf-8","replace").splitlines())
    if not rp.can_fetch(UA,url):
        report["result"]="SKIPPED robots"
    else:
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=20) as f:
            raw=f.read(600_000).decode("utf8","replace")
            report["http"]=f.status
        report["total_length"]=len(raw)
        for product in ("Topi Maxi","Bio-Quark","Joghurt mit der Ecke","Aktiv-Joghurt"):
            match=re.search(re.escape(product),raw,re.I)
            if not match:
                report.setdefault("product_mentions",[]).append({"product":product,"in_html":False})
                continue
            at=match.start();section=raw[max(0,at-1800):at+1400]
            report.setdefault("product_mentions",[]).append({"product":product,"in_html":True,
                "nearby_price_strings":list(dict.fromkeys(re.findall(r'\b\d+[,.]\d{2}\b',section)))[:12],
                "nearby_css_price_selectors":list(dict.fromkeys(re.findall(r'class=["\x27]([^"\x27]*(?:price|product|tile)[^"\x27]*)',section,re.I)))[:20],
                "nearby_article_fields":list(dict.fromkeys(re.findall(r'data-([a-z-]*(?:product|article|price|ean)[a-z-]*)=',section,re.I)))[:20]})
        report["markup_signals"]={name:len(re.findall(name,raw,re.I)) for name in
            ("product-grid","product-teaser","product-tile","price__value","currentPrice","productId","objectID","productName","product-card")}
        report["ldjson_products"]=len(re.findall(r'["\x27]@type["\x27]\s*:\s*["\x27]Product',raw,re.I))
        report["result"]="analyzed"
except HTTPError as e:report["result"]="HTTP_ERROR";report["http"]=e.code
except Exception as e:report["result"]=type(e).__name__+":"+str(e)[:150]
Path("results").mkdir(exist_ok=True)
Path("results/aldi_rendered_regular_prices.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(report,ensure_ascii=False,indent=2))
