#!/usr/bin/env python3
"""Netto app: inspect POS itemInfo and product price DTOs (static read-only).

Finds exact first-party model class names in the APK and extracts only public
field/getter names and type signatures. No credentials, request headers,
decompiled source or private app code persisted in GitHub.
"""
from __future__ import annotations
import json,re,zipfile,tempfile,subprocess
from datetime import datetime,timezone
from pathlib import Path
from targeted_jadx_retailer_apis import download,choose_base_apk,official_jadx

APP="com.valuephone.vpnetto"
OUT=Path("results/netto_price_dtos_20261031.json")

def classes(apk):
    matches=set()
    with zipfile.ZipFile(apk) as z:
        for path in z.namelist():
            if not re.fullmatch(r"classes\d*\.dex",path):continue
            raw=z.read(path)
            for m in re.finditer(rb"Lorg/openapitools/client/models/[A-Za-z0-9_$]{3,130};",raw):
                cl=m.group()[1:-1].decode().replace("/",".")
                if any(x in cl.lower() for x in ("iteminfo","price","product","article")):
                    matches.add(cl)
    return sorted(matches)

def simplify(java):
    lines=[]
    for line in java.splitlines():
        if re.search(r"\bpublic\s+(?:final\s+)?(?:[A-Za-z_][A-Za-z0-9_<>,? .\[\]]{0,140})\s+(?:get|is)[A-Z][A-Za-z0-9]{1,60}\s*\(\s*\)",line):
            s=line.strip()
            if "password" not in s.lower() and "token" not in s.lower():
                lines.append(s[:180])
    jsonfields=sorted(set(re.findall(r'@(?:SerializedName|JsonProperty)[\s\S]{0,65}?["\x27]([A-Za-z][A-Za-z0-9_-]{1,55})["\x27]',java)))
    return {"getter_signatures":sorted(set(lines))[:90],"json_field_names":jsonfields[:85]}

def main():
    out={"checked_utc":datetime.now(timezone.utc).isoformat(),
         "source":"Netto Marken-Discount current APK static model analysis",
         "price_response_verified":False,"classes":[]}
    try:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            archive=root/"pkg.zip"
            stamp=download(f"https://d.apkpure.com/b/APK/{APP}?version=latest",archive)
            out["apk_sha256"]=stamp["sha256"]
            apk=root/"base.apk";choose_base_apk(archive,apk)
            available=classes(apk)
            out["matching_model_classes"]=available[:100]
            chosen=[x for x in available if any(v in x.lower() for v in
                    ("iteminfo","price","product","article")) and "$" not in x]
            chosen=sorted(chosen,key=lambda x:(0 if "iteminfo" in x.lower() else 1 if "price" in x.lower() else 2,len(x)))[:9]
            chosen.insert(0,"org.openapitools.client.apis.MPOSApi")
            cli,_=official_jadx(root)
            for i,cl in enumerate(chosen):
                fn=root/f"class{i}.java"
                try:
                    task=subprocess.run([str(cli),"--no-res","--threads-count","2","--single-class",cl,
                        "--single-class-output",str(fn),str(apk)],timeout=100,text=True,capture_output=True)
                    row={"class_name":cl,"return_code":task.returncode}
                    if fn.exists():
                        src=fn.read_text(errors="replace")[:600000]
                        row.update(simplify(src))
                    else:row["no_source_output"]=True
                except subprocess.TimeoutExpired:row={"class_name":cl,"timeout":True}
                out["classes"].append(row)
            out["status"]="COMPLETE"
    except Exception as e:
        out["status"]="ERROR";out["error"]=type(e).__name__+":"+str(e)[:150]
    OUT.parent.mkdir(exist_ok=True,parents=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
