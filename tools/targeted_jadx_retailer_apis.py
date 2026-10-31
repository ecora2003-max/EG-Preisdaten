#!/usr/bin/env python3
"""Targeted APK decompilation for retail product catalogue interfaces.

Uses genuine publicly distributed packages and official JADX CLI. Never executes
retailer APKs; no API calls, credentials, certificates or source dumps are kept.
Only sanitized @GET/@POST path templates, class names and method signatures
are written to JSON.
"""
import hashlib,json,io,re,zipfile,subprocess,tempfile,os
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from datetime import datetime,timezone

UA="Ernaehrungsgedaechtnis-Research/4.1 (offline targeted APK code inspection)"
JADX="https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip"
MATCH={
    "kaufland":{"package":"com.kaufland.Kaufland","targets":["ProductDownloadApi","ProductApi"]},
    "netto_marken_discount":{"package":"com.valuephone.vpnetto","targets":["ProductAPIApi","MPOSApi"]},
}
MAX=245_000_000
def download(url,path,maxbytes=MAX):
    total=0;digest=hashlib.sha256()
    req=Request(url,headers={"User-Agent":UA})
    with urlopen(req,timeout=90) as r,path.open("wb") as f:
        while True:
            b=r.read(1024*1024)
            if not b:break
            total+=len(b)
            if total>maxbytes:raise ValueError("max bounded downloaded bytes exceeded")
            f.write(b);digest.update(b)
    if total<25000 or path.open("rb").read(4)!=b"PK\x03\x04":raise ValueError("Invalid ZIP header")
    return {"bytes":total,"sha256":digest.hexdigest()}
def official_jadx(bin_dir):
    zfile=bin_dir/"jadx.zip"
    stamp=download(JADX,zfile,90_000_000)
    with zipfile.ZipFile(zfile) as z:
        entries=z.infolist()
        if sum(x.file_size for x in entries)>450_000_000:raise ValueError("Unexpected oversized JADX")
        z.extractall(bin_dir/"jadx")
    cli=bin_dir/"jadx"/"bin"/"jadx"
    cli.chmod(0o755)
    return cli,stamp
def choose_base_apk(container,path):
    with zipfile.ZipFile(container) as z:
        entries=[e for e in z.infolist() if e.filename.endswith(".apk") and not e.is_dir()]
        if not entries:
            path.write_bytes(container.read_bytes())
            return "APK original"
        base=sorted(entries,key=lambda e:(("base" in e.filename.lower() or "com." in e.filename.lower()),e.file_size),reverse=True)[0]
        if base.file_size>320_000_000:raise ValueError("Base APK too large")
        with z.open(base) as a,path.open("wb") as b:
            while True:
                buf=a.read(1024*1024)
                if not buf:break
                b.write(buf)
        return base.filename
def class_names(apk,targets):
    found=set()
    pattern=re.compile(rb'L([a-zA-Z0-9_/$]{8,180});')
    with zipfile.ZipFile(apk) as z:
        for e in z.infolist():
            if not re.match(r"^classes\d*\.dex$",e.filename) or e.file_size>70_000_000:continue
            b=z.read(e)
            for m in pattern.finditer(b):
                clazz=m.group(1).decode("ascii","ignore").replace("/",".")
                if any(clazz.endswith(t) for t in targets) and len(clazz)<190:
                    found.add(clazz)
    return sorted(found)[:8]
def parse_decompilation(java):
    # Eliminate tokens/certificates/query values; keep only safe source-interface metadata.
    routes=[]
    for m in re.finditer(r'@(?:GET|POST|PUT|DELETE|PATCH|HEAD)\s*\(\s*"([^"]{1,220})"',java):
        route=m.group(1).split("?",1)[0]
        if re.fullmatch(r"/?[a-zA-Z0-9_{}./-]{3,170}",route):
            routes.append({"verb":re.search(r"@(\w+)",m.group(0)).group(1),"route":route})
    method_names=[m.group(1) for m in re.finditer(r'\b(?:public|abstract)\s+(?:[\w<>,? .\[\]]+)\s+([A-Za-z_]\w*)\s*\(',java)]
    query_keys=sorted(set(m.group(1) for m in re.finditer(r'@Query\(\s*"([A-Za-z_][A-Za-z_0-9-]{0,60})"\s*\)',java)))
    path_keys=sorted(set(m.group(1) for m in re.finditer(r'@Path\(\s*"([A-Za-z_][A-Za-z_0-9-]{0,60})"\s*\)',java)))
    return {"routes":routes[:35],"method_names":method_names[:40],
            "query_keys":query_keys[:40],"path_keys":path_keys[:35],
            "decompiled_java_chars":len(java)}
def inspect(name,config,jadx,work):
    d={"retailer":name,"expected_package":config["package"]}
    pkgzip=work/"download.zip"
    apk=work/"base.apk"
    try:
        d["download"]=download(f"https://d.apkpure.com/b/APK/{config['package']}?version=latest",pkgzip)
        d["base_archive_entry"]=choose_base_apk(pkgzip,apk)
        names=class_names(apk,config["targets"])
        d["target_classes_found"]=names
        d["classes"]=[]
        for index,clazz in enumerate(names[:4]):
            out=work/f"source_{index}.java"
            cmd=[str(jadx),"--no-res","--threads-count","2","--single-class",clazz,
                 "--single-class-output",str(out),str(apk)]
            try:
                run=subprocess.run(cmd,capture_output=True,text=True,timeout=105)
                item={"class":clazz,"return_code":run.returncode}
                if out.exists():
                    item.update(parse_decompilation(out.read_text(encoding="utf-8",errors="replace")[:800_000]))
                else:
                    item["failure_type"]="No decompiled output"
                d["classes"].append(item)
            except subprocess.TimeoutExpired:
                d["classes"].append({"class":clazz,"error":"timed out; no Java output retained"})
        d["result"]="TARGETED_BINARY_DECOMPILATION_FINISHED"
    except HTTPError as e:d.update({"result":"HTTP_ERROR","status":e.code})
    except Exception as e:d.update({"result":"ERROR","error":type(e).__name__+": "+str(e)[:175]})
    return d

def main():
    result={"checked_utc":datetime.now(timezone.utc).isoformat(),
     "note":"Original binary decompilation of app developer's method signatures. Does NOT show live API access or permission.",
     "apps":[]}
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        try:
            jadx,info=official_jadx(root)
            result["jadx_version"]="1.5.6"
            result["jadx_bundle_sha256"]=info["sha256"]
            for name,config in MATCH.items():
                (root/name).mkdir()
                entry=inspect(name,config,jadx,root/name)
                result["apps"].append(entry)
                print("ANALYZED="+json.dumps(entry,ensure_ascii=False),flush=True)
        except Exception as e:
            result["global_error"]=type(e).__name__+": "+str(e)[:175]
    Path("results").mkdir(exist_ok=True)
    Path("results/targeted_jadx_retailer_apis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("REPORT="+json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
