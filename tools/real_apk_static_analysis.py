#!/usr/bin/env python3
"""Original, offline static APK/XAPK analysis of public Android retailer releases.

- Fetch public package bytes through a normal endpoint (no login/bypass).
- Do not execute or install the APK.
- Scan DEX / native binary and selected assets for API *route names* and hosts.
- Record only sanitized public hostnames/path templates. No tokens, API keys,
  certificate blobs, APK binaries or customer data enter logs or artifacts.
- Store downloads only in a temporary, automatically deleted runner directory.
- Report "found in binary", not "API works", store-price access or permissions.
"""
from __future__ import annotations
import hashlib,io,json,re,sys,tempfile,zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from datetime import datetime,timezone
from collections import Counter

UA="Ernaehrungsgedaechtnis-Research/4.0 (public APK binary strings, no execution)"
PACKAGES={
    "edeka_current":"de.edeka.genuss",
    "netto_marken_discount":"com.valuephone.vpnetto",
    "penny":"de.penny.app",
    "penny_scan_go":"de.penny.scango",
    "kaufland":"com.kaufland.Kaufland",
}
MAX_DOWNLOAD=240_000_000
MAX_ARCHIVE_ENTRY=120_000_000
MAX_SCAN_BYTES=240_000_000
URL_RE=re.compile(rb'https?://[a-zA-Z0-9_.-]{4,120}(?::[0-9]{2,5})?(?:/[a-zA-Z0-9._~/%+{}\[\]:;!?=&-]{0,140})?',re.I)
PATH_RE=re.compile(rb'/(?:api|v[0-9]|mpos|items?|products?|catalog(?:ue)?|search|prices?|offers?|scan(?:-and-go|go)?|stores?|baskets?|checkouts?|markets?|ean|barcodes?|master-data)[a-zA-Z0-9._~/%+{}?=&/-]{2,160}',re.I)
INTEREST=re.compile(r'price|product|catalog|mpos|iteminfo|barcode|ean|scan|store|market|basket|search|master|offer|artikel|preis',re.I)
HOST_RE=re.compile(r'^[a-z0-9-]+(?:\.[a-z0-9-]+)+$',re.I)
SIGNALS=[b"itemInfo",b"itemEAN",b"analyzeBarcode",b"product-search",b"productcatalog",
         b"products/search",b"priceValue",b"regularPrice",b"storePrice",b"storePrices",
         b"basePrice",b"salesPrice",b"mpos",b"basket/evaluate",b"scanAndGo",
         b"barcode-mapping",b"offerfinder",b"valuephone",b"shopreme",b"kaufland",
         b"penny",b"edeka",b"intershop",b"gk-software",b"b2c-gw.api.edeka"]
SENSITIVE=re.compile(r'(?i)auth|token|apikey|api_key|secret|password|certificate|private|oauth|jwt|bearer|refresh|session|login|sign-?in|checkout|pay|user|account')

def clean_host(url:bytes)->str|None:
    try:
        p=urlparse(url.decode("ascii","ignore"))
        host=p.hostname or ""
        if (p.scheme not in ("http","https") or not HOST_RE.match(host)
                or host.endswith((".example",".local",".internal"))):
            return None
        return host.lower()
    except Exception:return None

def clean_path(raw:bytes)->str|None:
    try:s=raw.decode("ascii","ignore")
    except Exception:return None
    # Query values may contain credentials. Never save them.
    s=s.split("?",1)[0].split("#",1)[0]
    s=s.rstrip(".,;\\x00")
    if len(s)<7 or len(s)>160 or " " in s or SENSITIVE.search(s):return None
    if re.search(r'/[A-Za-z0-9_-]{55,}',s):return None
    if s.count("/")<1:return None
    if not INTEREST.search(s):return None
    return s[:140]

def inspect_bytes(data:bytes,stats:dict,label:str):
    stats["scanned_bytes"]+=len(data)
    stats["scanned_files"]+=1
    # Print only names of APIs; URLs stripped to host, no path query/credentials.
    hosts=stats["hosts"]; paths=stats["paths"]; hits=stats["signal_hits"]
    for u in URL_RE.findall(data):
        host=clean_host(u)
        if host: hosts[host]+=1
        try:pa=urlparse(u.decode("ascii","ignore")).path.encode()
        except Exception:continue
        cleaned=clean_path(pa)
        if cleaned and cleaned.startswith(("/api","/v1","/v2","/v3","/v4")):
            paths[cleaned]+=1
    for m in PATH_RE.findall(data):
        p=clean_path(m)
        if p:paths[p]+=1
    for token in SIGNALS:
        k=token.decode("ascii")
        n=data.lower().count(token.lower())
        if n:hits[k]+=n

def inspect_archive(rawfile:Path,report:dict,depth:int=0):
    with zipfile.ZipFile(rawfile) as z:
        files=z.infolist()
        if depth==0:
            report["container_entries"]=len(files)
            report["container_type"]="XAPK/split" if any(n.filename.endswith(".apk") for n in files) else "APK"
        for member in files:
            name=member.filename
            if member.is_dir() or member.file_size>MAX_ARCHIVE_ENTRY:continue
            if name.lower().endswith(".apk") and depth==0:
                if member.file_size>MAX_ARCHIVE_ENTRY:continue
                try:
                    with tempfile.TemporaryDirectory() as temp:
                        dest=Path(temp)/"base.apk"
                        with z.open(member) as inp,dest.open("wb") as out:
                            while True:
                                b=inp.read(1024*1024)
                                if not b:break
                                out.write(b)
                        inspect_archive(dest,report,depth=1)
                except Exception as exc:
                    report.setdefault("archive_read_issues",[]).append(type(exc).__name__)
                continue
            if not (re.search(r'(^|/)(classes[0-9]*\.dex|libapp\.so|lib[^/]*\.so|.*\.(?:js|bundle|json|properties|txt|xml))$',name,re.I)):
                continue
            if report["scanner"]["scanned_bytes"]>=MAX_SCAN_BYTES:break
            try:
                data=z.read(member)
                inspect_bytes(data,report["scanner"],name)
                if len(report["scanner"]["files"])<18:
                    report["scanner"]["files"].append(name[-100:])
            except Exception as exc:
                report.setdefault("archive_read_issues",[]).append(type(exc).__name__)
        if depth==0 and report["scanner"]["scanned_files"]==0:
            report["result"]="ARCHIVE_HAS_NO_ANALYZABLE_CODE"

def download_public(package:str,path:Path):
    url=f"https://d.apkpure.com/b/APK/{package}?version=latest"
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/octet-stream"})
    digest=hashlib.sha256()
    total=0
    with urlopen(req,timeout=80) as f,path.open("wb") as out:
        meta={"http":f.status,"source_host":urlparse(f.geturl()).hostname,
              "expected_bytes":f.headers.get("Content-Length")}
        while True:
            chunk=f.read(1024*1024)
            if not chunk:break
            total+=len(chunk)
            if total>MAX_DOWNLOAD:raise ValueError("Package above bounded max")
            out.write(chunk);digest.update(chunk)
    if total<50000 or path.read_bytes()[:4]!=b"PK\x03\x04":
        raise ValueError("Response is not a ZIP/APK archive")
    meta.update({"download_bytes":total,"sha256":digest.hexdigest()})
    return meta

def study(retailer,package):
    result={"retailer":retailer,"expected_package":package}
    result["scanner"]={"hosts":Counter(),"paths":Counter(),"signal_hits":Counter(),
                        "scanned_bytes":0,"scanned_files":0,"files":[]}
    try:
        with tempfile.TemporaryDirectory() as temp:
            apk=Path(temp)/"public_android_package.zip"
            result.update(download_public(package,apk))
            inspect_archive(apk,result)
        result["result"]="BINARY_ANALYZED"
    except HTTPError as e:result.update({"result":"DOWNLOAD_HTTP_ERROR","http":e.code})
    except Exception as e:result.update({"result":"ERROR","error":type(e).__name__+": "+str(e)[:180]})
    stats=result["scanner"]
    result["scanner"]={
        "scanned_bytes":stats["scanned_bytes"],
        "scanned_files":stats["scanned_files"],
        "files_sample":stats["files"],
        "hostnames":sorted(stats["hosts"],key=lambda k:-stats["hosts"][k])[:70],
        "api_route_candidates":sorted(stats["paths"],key=lambda k:(-stats["paths"][k],k))[:85],
        "feature_signal_counts":dict(stats["signal_hits"].most_common()),
    }
    return result

def main():
    args=sys.argv[1:] or ["edeka_current","penny","penny_scan_go","netto_marken_discount","kaufland"]
    result={"checked_utc":datetime.now(timezone.utc).isoformat(),
            "method":"Direct binary string extraction of actual APK/XAPK (no execution, no authentication)",
            "caveat":"Paths are *static references*, not proof of working endpoints or actual catalogue prices.",
            "apps":[]}
    for name in args:
        if name not in PACKAGES:
            raise ValueError("Unknown expected package "+name)
        output=study(name,PACKAGES[name])
        print(json.dumps({"app":name,"result":output["result"],
           "download_bytes":output.get("download_bytes"),
           "scanned_files":output["scanner"]["scanned_files"],
           "hosts":len(output["scanner"]["hostnames"]),
           "paths":len(output["scanner"]["api_route_candidates"])},ensure_ascii=False),flush=True)
        result["apps"].append(output)
    Path("results").mkdir(exist_ok=True)
    Path("results/real_apk_static_analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("REPORT="+json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
