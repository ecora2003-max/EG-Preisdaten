#!/usr/bin/env python3
"""One-shot official Netto prospect-domain access/schema test.

No cookie impersonation, fingerprint spoofing, or anti-bot bypass. Do not
download entire PDFs yet; inspect only published page links.
"""
import json,re
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin,urlparse
from html import unescape
from pathlib import Path
from datetime import datetime,timezone
ua="Ernaehrungsgedaechtnis-Research/1.0 (public leaflet research)"
rows=[]
root="https://wochenprospekt.netto-online.de"
try:
    with urlopen(Request(root+"/robots.txt",headers={"User-Agent":ua}),timeout=14) as r:
        rp=RobotFileParser();rp.parse(r.read(200000).decode("utf8","replace").splitlines());robots="defined"
except HTTPError as e:
    rp=None;robots="absent" if e.code==404 else "unknown HTTP "+str(e.code)
except Exception as e:
    rp=None;robots="unknown "+type(e).__name__
for url in (root+"/hz45_besb/?storeid=7679",root+"/hz45_wrse/?storeid=8135"):
    row={"url":url,"robots_status":robots}
    if robots.startswith("unknown") or (rp is not None and not rp.can_fetch(ua,url)):
        row["outcome"]="skipped restricted/unknown robots";rows.append(row);continue
    try:
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"text/html"}),timeout=20) as r:
            row["http"]=r.status;row["content_type"]=r.headers.get("Content-Type","")[:90]
            html=r.read(2_500_000).decode("utf-8","replace")
        row["size"]=len(html)
        row["title"]=re.search(r'<title[^>]*>(.*?)</title>',html,re.I|re.S).group(1)[:150] if re.search(r'<title[^>]*>(.*?)</title>',html,re.I|re.S) else None
        row["pdf_hrefs"]=[urljoin(url,unescape(x)) for x in dict.fromkeys(
            re.findall(r'<a[^>]*href=["\x27]([^"\x27]*\.pdf[^"\x27]*)["\x27]',html,re.I))][:10]
        row["downloadAsPdf_tag"]=(re.search(r'<a\b[^>]*id=["\x27]downloadAsPdf["\x27][^>]*>',html,re.I).group(0)[:1000]
                                  if re.search(r'<a\b[^>]*id=["\x27]downloadAsPdf["\x27][^>]*>',html,re.I) else None)
        row["pdf_urls_in_html"]=[unescape(x)[:300] for x in dict.fromkeys(
            re.findall(r'https?://[^"\x27\s<>\\]+\.pdf(?:\?[^"\x27\s<>\\]*)?',html,re.I))][:8]
        row["blocked"]=bool(re.search(r'access denied|captcha|request rejected|forbidden',html,re.I))
        row["product_json_signals"]={k:html.count(k) for k in ("products","articles","prices","downloadAsPdf","offer","validFrom")}
    except HTTPError as e:row["http"]=e.code;row["outcome"]="HTTPError"
    except Exception as e:row["outcome"]=type(e).__name__+":"+str(e)[:120]
    rows.append(row)
Path("results").mkdir(exist_ok=True)
Path("results/netto_leaflet_host.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(rows,indent=2,ensure_ascii=False))
