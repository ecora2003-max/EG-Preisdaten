#!/usr/bin/env python3
"""Resolve Netto productSearch actual client host and response model from APK.

Only safe class relations, public domain literals, method return type
and non-secret model property names are emitted. No app secrets or credentials.
"""
from __future__ import annotations
import collections,hashlib,json,re,subprocess,tempfile,zipfile
from datetime import datetime,timezone
from pathlib import Path
from targeted_jadx_retailer_apis import download,choose_base_apk,official_jadx
APP="com.valuephone.vpnetto"
TARGETS=[
"de.netto.b2c.core.common.data.network.di.RetrofitServiceFactory",
"de.netto.b2c.core.common.data.network.di.NetworkModuleKt",
"de.netto.plus.appservice.api.infrastructure.ApiClient",
"de.netto.plus.commons.api.infrastructure.ApiClient",
"org.openapitools.client.apis.ProductAPIApi",
"org.openapitools.client.models.ProductSearchResponse",
]
OUT=Path("results/netto_product_host_model_20261031.json")
HOST_RE=re.compile(r'\b(?:https?://)?(?:[a-z0-9-]+\.)+(?:de|com|net|org)(?::\d+)?\b',re.I)
BAD_RE=re.compile(r"auth|token|key|secret|password|bearer|cookie|signature",re.I)

def analyze(java):
    raw_lines=java.splitlines()
    annotated_fields=sorted(set(re.findall(r'@(?:SerializedName|JsonProperty)[\s\S]{0,65}?["\x27]([A-Za-z][A-Za-z0-9_-]{1,45})["\x27]',java)))
    getter_names=sorted(set(re.findall(r'\b(?:get|is)([A-Z][A-Za-z0-9]{1,45})\s*\(',java)))
    method_types=[]
    for line in raw_lines:
        if any(tag in line for tag in ("productSearch(", "getResult()", "getContent()", "getMessage()", "getPrice()", "getDefaultBasePath()", "baseUrl(", "createService(", "getBaseUrl()","Retrofit.Builder","ProductAPIApi.class")):
            # whitelist structural method signatures; suppress raw code expressions
            text=line.strip()
            if len(text)>240 or BAD_RE.search(text):continue
            if "https:" in text or "http:" in text:continue
            method_types.append(text[:200])
    # Only hostname portion of absolute URLs, not query strings or path tokens.
    public_hosts=sorted(set(v.lower().split("://",1)[-1] for v in HOST_RE.findall(java) if "." in v and not BAD_RE.search(v)))[:40]
    hosts=sorted(set(
        v.lower().replace("https://","").replace("http://","")
        for v in HOST_RE.findall(java) if "netto" in v.lower()
    ))
    return {"getter_names":getter_names[:65],
      "annotated_json_fields":annotated_fields[:70],
      "nonsecret_signature_lines":method_types[:32],
      "all_public_hostname_literals":public_hosts,
      "netto_public_hostname_literals":hosts[:20]}

def main():
    report={"checked_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"Static on-device Kotlin/Retrofit wiring, no API calls",
            "result":[]}
    try:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            apkzip=root/"app.zip"
            dl=download(f"https://d.apkpure.com/b/APK/{APP}?version=latest",apkzip)
            report["original_apk_sha256"]=dl["sha256"]
            base=root/"app.apk";choose_base_apk(apkzip,base)
            cli,stamp=official_jadx(root)
            for i,clazz in enumerate(TARGETS):
                fn=root/f"test_{i}.java"
                entry={"class":clazz}
                try:
                    cmd=[str(cli),"--no-res","--threads-count","2","--single-class",clazz,"--single-class-output",str(fn),str(base)]
                    sub=subprocess.run(cmd,capture_output=True,text=True,timeout=130)
                    entry["exit_code"]=sub.returncode
                    if fn.exists():
                        source=fn.read_text(encoding="utf8",errors="replace")
                        entry.update(analyze(source))
                    else:entry["missing_class"]=True
                except subprocess.TimeoutExpired:
                    entry["timeout"]=True
                report["result"].append(entry)
            report["status"]="DONE"
    except Exception as e:
        report["status"]="ERROR";report["error"]=type(e).__name__+": "+str(e)[:150]
    OUT.parent.mkdir(exist_ok=True,parents=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
