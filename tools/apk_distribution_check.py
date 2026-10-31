#!/usr/bin/env python3
"""Find publicly distributable APK/XAPK bytes, never bypass challenge or sign in.

Read only a 64KiB range from each provider URL and record content type, ZIP/APK
signature and HTTP status. This is a HEAD/Range feasibility step, NOT APK
decompilation. Do not save software or any credentials into GitHub artifacts.
"""
from urllib.request import urlopen, Request
from urllib.error import HTTPError,URLError
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime,timezone
import json
UA="Ernaehrungsgedaechtnis-Research/3.3 (single public Android package acquisition check)"
packages={
 "netto_marken_discount":"com.valuephone.vpnetto",
 "penny":"de.penny.app",
 "kaufland":"com.kaufland.Kaufland",
 "edeka":"com.valuephone.vpedeka",
 "penny_scango":"de.penny.scango",
}
attempts=[]
for retailer,package in packages.items():
  for fmt in ("APK","XAPK"):
    url=f"https://d.apkpure.com/b/{fmt}/{package}?version=latest"
    row={"retailer":retailer,"package_name":package,"distribution":"APKPure","format_requested":fmt}
    try:
      req=Request(url,headers={"User-Agent":UA,"Range":"bytes=0-65535","Accept":"application/octet-stream,*/*;q=0.5"})
      with urlopen(req,timeout=18) as r:
        data=r.read(65536)
        row.update({"status":r.status,"content_type":r.headers.get("Content-Type","")[:90],
           "content_length":r.headers.get("Content-Length"),
           "content_range":r.headers.get("Content-Range"),
           "final_host":urlparse(r.geturl()).netloc,
           "bytes_sampled":len(data),
           "zip_magic":data[:4].hex(),
           "zip_archive":data.startswith(b"PK\x03\x04")})
      attempts.append(row)
      # One working source per package is enough.
      if row["zip_archive"]:break
    except HTTPError as e:
      row["status"]=e.code;row["final_host"]=urlparse(e.geturl()).netloc
    except Exception as e:row["error"]=type(e).__name__+":"+str(e)[:140]
    attempts.append(row)
out={"checked_utc":datetime.now(timezone.utc).isoformat(),"checks":attempts,
     "note":"Only read 64KiB of each publicly distributable APK/XAPK; never bypass HTTP restrictions"}
Path("results").mkdir(exist_ok=True)
Path("results/apk_public_distribution_sources.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2,ensure_ascii=False))
