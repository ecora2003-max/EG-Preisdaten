#!/usr/bin/env python3
"""Netto /filialangebote: identify real data pathway for displayed offer products.

Four plain GETs only; no auth, cookies, browser spoofing, challenge bypass.
Records metadata, links, script names and candidate API route *paths*.
No HTML bodies or JavaScript source are retained.
"""
import json,re,html,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse

UA="ErnaehrungsgedaechtnisResearch/2.3 (Netto filialangebote API source identification)"
BASE="https://www.netto-online.de"
ROUTES=[
 "/filialangebote",
 "/filialangebote?stores_id=7679",
 "/filialangebote?stores_id=8135",
 "/filialangebote/preissenkung",
]
MAX=2_300_000
OUT=Path("results/netto_filialangebote_data_path_20261031.json")

def between(tag,attrs):return re.search(r'\b'+attrs+r'\s*=\s*["\x27]([^"\x27]*)',tag,re.I)

def test(url):
    out={"url":url,"checked_utc":datetime.now(timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req,timeout=25) as response:
            body=response.read(MAX+1)
            out["http"]=response.status
            out["effective_url"]=response.geturl()
            out["content_type"]=response.headers.get("Content-Type")
        if len(body)>MAX:out["result"]="OVERSIZE";return out
        doc=body.decode("utf-8","replace")
        out["length"]=len(doc)
        out["is_challenge"]=bool(re.search(r"<title>\s*Access Denied|CAPTCHA|Request Rejected|bot verification",doc,re.I))
        out["title"]=(re.search(r'<title[^>]*>(.*?)</title>',doc,re.S|re.I).group(1).strip()[:110] if re.search(r'<title[^>]*>(.*?)</title>',doc,re.S|re.I) else None)
        out["selected_store_id_counts"]={id:len(re.findall(r'stores_id\s*["\x27:= ]+\s*'+id+r'\b',doc,re.I)) for id in ("7679","8135")}
        out["price_markers"]={k:len(re.findall(p,doc,re.I)) for k,p in {
            "offerPrice":r'offerPrice',"amount":r'"amount"\s*:',
            "currency":r'"priceCurrency"',"eur_symbols":r'€|&euro;',
            "price_class":r'class=["\x27][^"\x27]{0,90}\bprice',
            "product_object":r'product(?:Id|Name|Title)',
            "offer_id":r'offer(?:Id|Title|Price)',
            "filial_data":r'filialangebote|filial-angebote',
            "store_context":r'stores_id|storeId|selectedStore|selectedMarket',
            "ajax":r'ajax|\.rest/|/api/|\.json',
            "product_url":r'/p-\d{6,15}',"offer_article":r'article-card|offer-tile|offer-card|product-tile'
        }.items()}
        scripts=[]
        for m in re.finditer(r'<script\b[^>]*>',doc,re.I):
            v=between(m.group(),"src")
            if v:
                source=html.unescape(v.group(1))
                scripts.append(urljoin(url,source) if source.startswith("/") else source)
        out["scripts"] = list(dict.fromkeys(scripts))[:70]
        forms=[]
        for m in re.finditer(r'<form\b[^>]*>',doc,re.I):
            a=between(m.group(),"action")
            forms.append(urljoin(url,html.unescape(a.group(1))) if a else "")
        out["form_actions"]=list(dict.fromkeys(forms))[:35]
        urls=[]
        for m in re.finditer(r'<a\b[^>]*\bhref\s*=\s*["\x27]([^"\x27]+)',doc,re.I):
            ref=html.unescape(m.group(1))
            if re.search(r'filialangebote|angebote|preissenkung|(?i:produkt)',ref,re.I):
                urls.append(urljoin(url,ref))
        out["related_anchor_links"]=list(dict.fromkeys(urls))[:75]
        route_hints=set()
        for m in re.finditer(r'["\x27]((?:https?:)?//[^"\x27<>\s]{6,160}|/(?:api/|\.rest/|filialangebote/|offers/|angebote/)[^"\x27<>\s]{2,160})["\x27]',doc,re.I):
            path=m.group(1).split("?",1)[0]
            if re.search(r'netto|api|filial|offer|produkt|product|angebot',path,re.I):
                route_hints.add(path[:155])
        out["candidate_endpoint_literals"]=sorted(route_hints)[:70]
        out["inline_script_tags"]=len(re.findall(r'<script\b',doc,re.I))
        out["result"]="HTML_ANALYZED"
    except urllib.error.HTTPError as e:
        out["http"]=e.code;out["result"]="HTTP_ERROR"
    except Exception as e:
        out["error_class"]=type(e).__name__;out["result"]="ERROR"
    return out

def main():
    out={"source":"Netto official filialangebote pages","checked_utc":datetime.now(timezone.utc).isoformat(),
        "cases":[test(BASE+path) for path in ROUTES],
        "scope":"Retailer offers page, not a proven all-item price search",
        "limitations":"DOM script endpoints may be relative or dynamically constructed"}
    OUT.parent.mkdir(exist_ok=True,parents=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
