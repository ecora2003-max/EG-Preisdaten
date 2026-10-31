#!/usr/bin/env python3
"""Resolve Netto MPOS endpoint's actual base hostname from current Android APK.

One-time static code analysis; do not save APK, credentials, literal query strings
or decompiled source. Only hostnames and safe structural method names. No live
price calls are made until a host has been identified.
"""
from __future__ import annotations
import json, re, subprocess, tempfile, zipfile
from datetime import datetime,timezone
from pathlib import Path
from targeted_jadx_retailer_apis import download,choose_base_apk,official_jadx

PKG="com.valuephone.vpnetto"
TARGET=[
 "org.openapitools.client.infrastructure.ApiClient",
 "org.openapitools.client.ApiClient",
 "org.openapitools.client.apis.MPOSApi",
 "de.netto.plus.appservice.api.infrastructure.ApiClient",
 "de.netto.plus.commons.api.infrastructure.ApiClient",
 "de.netto.b2c.core.common.data.network.di.NetworkModuleKt",
 "de.netto.b2c.core.common.data.network.di.RetrofitServiceFactory",
]
PROTOCOL=re.compile(r"https?://[a-z0-9][a-z0-9.-]{3,130}(?::\d{2,5})?/?",re.I)
DOMAIN=re.compile(r"(?<![a-z0-9_-])(?:[a-z0-9_-]+\.)+(?:de|com|net)(?![a-z0-9_-])",re.I)
SUSPECT=re.compile(r"netto|valuephone|vpserverapp|nes\.",re.I)
ROOT=Path("results/netto_mpos_base_host_20261031.json")

def main():
    out={"analyzed_at_utc":datetime.now(timezone.utc).isoformat(),
         "status":"STARTED","classes":[]}
    try:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            archive=root/"app.zip"
            snap=download(f"https://d.apkpure.com/b/APK/{PKG}?version=latest",archive)
            out["package_sha256"]=snap["sha256"]
            base=root/"app.apk";choose_base_apk(archive,base)
            with zipfile.ZipFile(base) as z:
                names=set()
                apk_domains=set()
                for d in z.namelist():
                    if not re.fullmatch(r"classes\d*\.dex",d):continue
                    blob=z.read(d)
                    for hit in re.finditer(rb"L[a-zA-Z0-9_/]{10,180}ApiClient;",blob):
                        cn=hit.group()[1:-1].decode("ascii","ignore").replace("/",".")
                        if "openapitools" in cn or "netto" in cn:
                            names.add(cn)
                    for hit in DOMAIN.findall(blob.decode("latin-1","ignore")):
                        if SUSPECT.search(hit) and len(hit)<140:
                            apk_domains.add(hit.lower())
                out["netto_hostname_literals_in_dex"]=sorted(apk_domains)[:120]
                out["api_client_classes_present"]=sorted(names)[:70]
            jadx,version=official_jadx(root)
            targets=list(dict.fromkeys(TARGET+[x for x in sorted(names) if
                      ("org.openapitools" in x) and x not in TARGET][:3]))
            for i,cl in enumerate(targets):
                out_java=root/f"out_{i}.java"
                entry={"class":cl}
                try:
                    p=subprocess.run([str(jadx),"--no-res","--threads-count","2",
                                      "--single-class",cl,"--single-class-output",str(out_java),
                                      str(base)],capture_output=True,timeout=100,text=True)
                    entry["exit"]=p.returncode
                    if out_java.exists():
                        source=out_java.read_text(encoding="utf8",errors="replace")
                        # Only hostname literals, never paths or query strings.
                        entry["url_origins"]=sorted(set(x.rstrip("/") for x in PROTOCOL.findall(source)
                                                         if SUSPECT.search(x)))[:40]
                        entry["hostnames"]=sorted(set(x.lower() for x in DOMAIN.findall(source)
                                                      if SUSPECT.search(x)))[:40]
                        # Structural signals without exposing full source.
                        entry["structural_fields"]=sorted(set(
                            k for k in ("getDefaultBasePath","DEFAULT_BASE_PATH","defaultBasePath",
                              "baseUrl(","Retrofit.Builder","MPOSApi","getItemInfo","itemInfo")
                            if k in source))
                    else:
                        entry["missing_class"]=True
                except subprocess.TimeoutExpired:
                    entry["timeout"]=True
                out["classes"].append(entry)
            out["status"]="STATIC_DONE"
    except Exception as e:
        out["status"]="ERROR"
        out["error_type"]=type(e).__name__
        out["error_summary"]=str(e)[:180]
    ROOT.parent.mkdir(parents=True,exist_ok=True)
    ROOT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
