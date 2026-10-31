import json
from urllib.request import Request,urlopen
from urllib.robotparser import RobotFileParser
from urllib.parse import urlencode
from pathlib import Path
ua="Ernaehrungsgedaechnis-Research/0.3 (read-only)"
host="https://endpoints.leaflets.schwarz"
url=host+"/v4/flyer?"+urlencode({"flyer_identifier":"aktionsprospekt-02-11-2026-07-11-2026-fbfd28","client":"lidl"})
try:
    with urlopen(Request(host+"/robots.txt",headers={"User-Agent":ua}),timeout=15) as f:
        r=RobotFileParser();r.parse(f.read(200000).decode("utf-8","replace").splitlines())
    assert r.can_fetch(ua,url),"robots disallows"
except HTTPError as e:
    if e.code != 404:raise
with urlopen(Request(url,headers={"User-Agent":ua}),timeout=20) as f:doc=json.load(f)
flyer=doc.get("flyer") or {}
ps=flyer.get("products") or {}
out={"product_root_type":type(ps).__name__,"product_count":len(ps)}
if isinstance(ps,dict):
    out["first_product_ids"]=list(ps)[:3]
    arr=[v for v in list(ps.values())[:3]]
elif isinstance(ps,list):
    arr=ps[:3]
else:arr=[]
out["samples"]=[]
for v in arr:
    if isinstance(v,dict):
        sample={"keys":list(v)[:55]}
        for key in ("name","title","price","priceValue","offerPrice","salePrice","brand","unit","quantity","startDate","endDate","validity","description","sku"):
            if key in v:sample[key]=v[key]
        out["samples"].append(sample)
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
Path("results").mkdir(exist_ok=True)
Path("results/lidl_product_fields.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
