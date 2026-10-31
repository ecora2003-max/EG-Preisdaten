#!/usr/bin/env python3
"""Netto+ APK: identify the true host and response fields for productSearch.

Static APK inspection ONLY; no login or price-service calls. Extracts
Retrofit GET method declarations, public hostnames, non-secret model field
names and references to the matching API type. No decompiled code uploaded.
"""
from __future__ import annotations
import collections
import json
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from targeted_jadx_retailer_apis import download,choose_base_apk,official_jadx
import subprocess

PACKAGE="com.valuephone.vpnetto"
OUT=Path("results/netto_product_api_static_20261031.json")
CLASS_TERMS=("ProductAPIApi","ProductSearch","ProductScan","ProductPrice","ProductDTO","ProductResponse","ApiClient","NetworkModule","Retrofit","NettoConfig","NettoApi","BaseUrl","MPOSApi")
EXACT_CLASSES=(
 "org.openapitools.client.apis.ProductAPIApi",
 "org.openapitools.client.apis.MPOSApi",
 "org.openapitools.client.models.ProductSearchResponse",
 "org.openapitools.client.models.ProductSearchDto",
 "org.openapitools.client.models.ProductScanResponse",
 "org.openapitools.client.infrastructure.ApiClient",
 "org.openapitools.client.ApiClient",
)
ALLOWED_HOST=re.compile(r"^(?:[A-Za-z0-9.-]*\.)?(?:netto-online\.de|netto\.de|valuephone\.com|vpserverapp\.com|netto\.com)$",re.I)

def dex_inspection(apk):
    urls=collections.Counter()
    names=set()
    relevant_context=[]
    strings=set()
    with zipfile.ZipFile(apk) as z:
        for nm in z.namelist():
            if not re.fullmatch(r"classes\d*\.dex",nm):continue
            b=z.read(nm)
            # Full Java class descriptors from bytecode. Never emit secrets.
            for m in re.finditer(rb"L(?:[A-Za-z0-9_/$]{8,170});",b):
                name=m.group()[1:-1].decode("ascii","ignore").replace("/",".")
                if any(term.lower() in name.lower() for term in CLASS_TERMS):
                    if (name.startswith("org.openapitools.") or name.startswith("de.netto.") or name.startswith("com.valuephone.")):
                        names.add(name)
            # Product API endpoint is a known safe structural string; sample nearby
            # printable words to identify base URL configuration class names.
            for m in re.finditer(rb"(?:https?://|[a-z0-9.-]*netto-online\.de|[a-z0-9.-]*valuephone\.com)[^\x00\s\"<>]{0,180}",b,re.I):
                s=m.group(0).decode("utf8","ignore")
                s=s.split("?")[0]
                if len(s)<220 and not any(x in s.lower() for x in ("token","secret","key=","password","oauth","session=")):
                    if m2:=re.search(r"(?i)(?:https?://)?([a-z0-9.-]+\.(?:de|com|net))(?::\d{1,5})?(?:/|$)",s):
                        host=m2.group(1).lower()
                        if ALLOWED_HOST.fullmatch(host):
                            urls[host]+=1
                            if len(relevant_context)<12 and "/rest/" in s:
                                relevant_context.append(s[:120])
    return {"api_related_class_names":sorted(names)[:160],
            "known_netto_host_appearances":dict(urls),
            "safe_rest_url_literals":relevant_context}

def parse_java(java):
    routes=[]
    for m in re.finditer(r'@(GET|HEAD)\s*\(\s*"([^"]{1,160})"',java):
        if re.fullmatch(r"/?[A-Za-z0-9_{}./-]{2,150}",m.group(2)):
            routes.append({"verb":m.group(1),"path":m.group(2)})
    query=sorted(set(re.findall(r'@Query\(\s*"([A-Za-z][A-Za-z0-9_-]{0,45})"',java)))
    fields=sorted(set(re.findall(r'@(?:SerializedName|JsonProperty)\s*\(\s*(?:value\s*=\s*)?"([A-Za-z0-9_-]{1,55})"',java)))
    # Collect no literal credentials. Only hostnames from absolute base URL calls.
    host_hits=[]
    for v in re.findall(r'https?://[A-Za-z0-9.-]{3,160}',java):
        h=v.split("://",1)[1].lower()
        if ALLOWED_HOST.fullmatch(h):host_hits.append(h)
    method_refs=sorted(set(re.findall(r'\b(?:productSearch|productScan|categoryList|itemInfo|setBaseUrl|baseUrl)\b',java)))
    return {"get_routes":routes[:18],"query_param_names":query[:35],
            "json_field_names":fields[:80],
            "api_method_refs":method_refs,
            "netto_host_literals":sorted(set(host_hits)),
            "source_chars":len(java)}

def run():
    record={"checked_utc":datetime.now(timezone.utc).isoformat(),
            "source":"current public Android package com.valuephone.vpnetto",
            "method":"targeted static JADX/DEX, no network requests to retailer APIs",
            "classes":[]}
    try:
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            dl=download(f"https://d.apkpure.com/b/APK/{PACKAGE}?version=latest",root/"apk_container.zip")
            record["apk_sha256"]=dl["sha256"]
            base=root/"base.apk"
            record["base_apk_entry"]=choose_base_apk(root/"apk_container.zip",base)
            record.update(dex_inspection(base))
            cli,version=official_jadx(root)
            record["jadx"]="1.5.6"
            names=set(record["api_related_class_names"])
            chosen=[x for x in EXACT_CLASSES if x in names]
            chosen += [x for x in sorted(names) if (x.startswith("org.openapitools.client.models.") and
                    any(t in x for t in ("ProductSearch","ProductScan","ProductPrice")))][:8]
            chosen += [x for x in sorted(names) if "Product" in x and "Service" in x and x.startswith("de.netto.")][:4]
            for i,cl in enumerate(dict.fromkeys(chosen)):
                fn=root/f"class_{i}.java"
                try:
                    task=subprocess.run([str(cli),"--no-res","--threads-count","2","--single-class",cl,
                         "--single-class-output",str(fn),str(base)],timeout=110,capture_output=True,text=True)
                    row={"class_name":cl,"decompilation_returncode":task.returncode}
                    if fn.exists():row.update(parse_java(fn.read_text(errors="replace")[:900000]))
                    else:row["no_java_output"]=True
                    record["classes"].append(row)
                except subprocess.TimeoutExpired:
                    record["classes"].append({"class_name":cl,"error":"TIMEOUT"})
            record["status"]="COMPLETE"
    except Exception as e:
        record["status"]="ERROR"
        record["error"]=type(e).__name__+": "+str(e)[:180]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(record,ensure_ascii=False))
if __name__=="__main__":run()
