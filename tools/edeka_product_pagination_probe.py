#!/usr/bin/env python3
"""Probe EDEKA /sortiment/suche/ pagination of the public ~6000-product index."""
from __future__ import annotations
import os, json,re,html,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,urljoin
if os.environ.get("EDEKA_PERMISSION_CONFIRMED")!="1":raise SystemExit("missing authorization flag")
BASE="https://www.edeka.de/sortiment/suche/"
UA="ErnaehrungsgedaechtnisResearch/3.1 (EDEKA authorized product pagination)"
PARAMS=[
{},
{"page":"2"},{"page":"3"},{"p":"2"},
{"offset":"24"},{"start":"24"},{"currentPage":"2"},
{"pageSize":"100"},{"size":"100"},{"q":"Haferflocken"},
]
def one(args):
    url=BASE+("?"+urlencode(args) if args else "")
    rec={"url":url,"query":args}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=25) as f:
            doc=f.read(2_000_000).decode("utf8","replace")
            rec["http"]=f.status
        links=re.findall(r'href=["\x27]([^"\x27]*?/sortiment/\d{10,15}/[^"\x27]*)["\x27]',doc,re.I)
        # Relative and absolute href references
        links += re.findall(r'href=["\x27](/\d{11,15}/)["\x27]',doc,re.I)
        rec["product_ids"]=list(dict.fromkeys(re.findall(r"/sortiment/(\d{10,15})/",doc)))[:28]
        rec["product_id_count"]=len(set(re.findall(r"/sortiment/(\d{10,15})/",doc)))
        rec["count_texts"]=re.findall(r'Suchergebnisse[^<]{0,130}',doc,re.I)[:3]
        rec["paging_references"]=len(re.findall(r'pagination|nextPage|next-page|load-more|mehr.laden|n.chste.Seite',doc,re.I))
        for marker in ("Nächste Seite","N&auml;chste Seite","next-page","load-more","pagination","pageSize","paginator","data-current-page"):
            m=re.search(re.escape(marker),doc,re.I)
            if m and not rec.get("pagination_context"):
                rec["pagination_context"]=re.sub(r'\s+',' ',doc[max(0,m.start()-260):m.end()+480])[:800]
        rec["form_openings"]=re.findall(r'<form\b[^>]{0,300}>',doc,re.I)[:6]
        rec["result"]="OK"
    except urllib.error.HTTPError as e:
        rec["http"]=e.code;rec["result"]="HTTP_ERROR"
    except Exception as e:
        rec["result"]="ERROR";rec["error_type"]=type(e).__name__
    return rec
result={"tested_at_utc":datetime.now(timezone.utc).isoformat(),"pages":[]}
for args in PARAMS:
    row=one(args);result["pages"].append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
p=Path("results/edeka_product_pagination_probe_20261031.json");p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
