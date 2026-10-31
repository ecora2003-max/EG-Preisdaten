#!/usr/bin/env python3
"""Check whether official PENNY & Kaufland assortment pages expose *non-offer* shelf prices.

One brand/category page per store, no site crawling. Results are only structural
counts and named examples. Technical access is not a permission for reuse.
"""
import re,json
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from html import unescape
from urllib.parse import urljoin,urlparse
from pathlib import Path
from datetime import datetime,timezone

UA="Ernaehrungsgedaechnis-Research/3.3 (read-only assortment price check)"
targets={
    "PENNY":"https://www.penny.de/sortiment/",
    "Kaufland":"https://filiale.kaufland.de/sortiment.html",
    "Netto Marken":"https://www.netto-online.de/"
}
result=[]
for merchant,url in targets.items():
    row={"retailer":merchant,"category_url":url}
    base=f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    try:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
                robot=RobotFileParser();robot.parse(f.read(250000).decode("utf8","replace").splitlines())
        except HTTPError as e:robot=None if e.code==404 else "unknown"
        except Exception:robot="unknown"
        if robot=="unknown" or (robot is not None and not robot.can_fetch(UA,url)):
            row["result"]="SKIP unknown robots or disallowed";result.append(row);continue
        with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=17) as f:
            row["status"]=f.status;html=f.read(900000).decode("utf-8","replace")
        row["length"]=len(html)
        row["json_ld_product_count"]=len(re.findall(r'["\x27]@type["\x27]\s*:\s*["\x27]Product',html,re.I))
        row["price_fields"]={s:len(re.findall(s,html,re.I)) for s in
                              (r'"regularPrice"',r'"currentPrice"',r'"offerPrice"',r'"price"',r'"sellingPrice"',r'"itemPrice"')}
        row["product_ids"]=len(re.findall(r'data-(?:product|article|ean)-id=',html,re.I))
        if merchant=="PENNY":
            urls=list(dict.fromkeys(urljoin(url,unescape(x)) for x in
                     re.findall(r'<a[^>]+href=["\x27]([^"\x27]+)',html,re.I)))
            choices=[u for u in urls if urlparse(u).netloc=="www.penny.de"
                     and "/sortiment/" in urlparse(u).path and urlparse(u).path!="/sortiment/"]
            row["sortiment_links_count"]=len(choices)
            row["sample_paths"]=[urlparse(u).path for u in choices[:7]]
            if choices:
                sub=choices[0]
                if robot is None or robot.can_fetch(UA,sub):
                    with urlopen(Request(sub,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=17) as f:
                        data=f.read(900000).decode("utf8","replace")
                    row["first_subcategory"]={"url_path":urlparse(sub).path,
                                              "price_marker_count":len(re.findall(r'(?:regularPrice|currentPrice|offerPrice|schema.org/Offer)',data,re.I)),
                                              "jsonld_products":len(re.findall(r'"@type"\s*:\s*"Product"',data)),
                                              "eur_display_count":len(re.findall(r'\d[,.]\d{2}\s*€',data))}
        row["result"]="SUCCESS"
    except HTTPError as e:row["status"]=e.code;row["result"]="HTTP_ERROR"
    except Exception as e:row["result"]=type(e).__name__+":"+str(e)[:125]
    result.append(row)
Path("results").mkdir(exist_ok=True)
Path("results/other_chain_catalogue_price_check.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(result,indent=2,ensure_ascii=False))
