#!/usr/bin/env python3
"""Verify Netto store-chosen official leaflet PDF has extractable structured text.

PDF bytes held in a temporary directory only; neither PDF nor substantial
copyrighted text are persisted in GitHub. No access restrictions bypassed.
"""
import json,re,os,tempfile,subprocess,shutil
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from pathlib import Path
from datetime import datetime,timezone

ua="Ernaehrungsgedaechtnis-Research/1.1 (read-only public brochure text research)"
root="https://wochenprospekt.netto-online.de"
storepages={"7679":"https://wochenprospekt.netto-online.de/hz45_besb/?storeid=7679",
            "8135":"https://wochenprospekt.netto-online.de/hz45_wrse/?storeid=8135"}
robots_cache={}
output=[]
def permission(url):
    p=urlparse(url);base=p.scheme+"://"+p.netloc
    if base not in robots_cache:
        try:
            with urlopen(Request(base+"/robots.txt",headers={"User-Agent":ua}),timeout=12) as f:
                robot=RobotFileParser();robot.parse(f.read(250000).decode("utf8","replace").splitlines());robots_cache[base]=robot
        except HTTPError as e:robots_cache[base]="allow" if e.code==404 else "unknown: HTTP "+str(e.code)
        except Exception as e:robots_cache[base]="unknown: "+type(e).__name__
    rule=robots_cache[base]
    return (rule=="allow" if isinstance(rule,str) else rule.can_fetch(ua,url))
for sid,page in storepages.items():
    rec={"store_id":sid,"prospect_page":page}
    try:
        if not permission(page):
            rec["status"]="skipped: robots";output.append(rec);continue
        with urlopen(Request(page,headers={"User-Agent":ua,"Accept":"text/html"}),timeout=18) as f:
            html=f.read(500000).decode("utf-8","replace")
        found=re.search(r'https?://view\.publitas\.com/[^"\x27\s<>\\]+?\.pdf\?[^"\x27\s<>\\]+',html,re.I)
        if not found:
            rec["status"]="PDF URL not found in public official viewer";output.append(rec);continue
        url=found.group(0).replace("&amp;","&")
        rec["pdf_url_host"]=urlparse(url).netloc
        rec["pdf_file_hint"]=re.search(r'/([^/]+)\.pdf',url).group(1)[-32:]
        if not permission(url):
            rec["status"]="PDF retrieval restricted/robots unknown";output.append(rec);continue
        with urlopen(Request(url,headers={"User-Agent":ua,"Accept":"application/pdf"}),timeout=30) as f:
            rec["http"]=f.status
            rec["content_type"]=f.headers.get("Content-Type","")
            raw=f.read(16_000_001)
        rec["pdf_bytes"]=len(raw)
        if not raw.startswith(b"%PDF") or len(raw)>16_000_000:
            rec["status"]="not a PDF or exceeds bounded size";output.append(rec);continue
        if shutil.which("pdftotext") is None:
            rec["status"]="PDF downloaded but pdftotext not installed";output.append(rec);continue
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"prospekt.pdf";path.write_bytes(raw)
            cmd=["pdftotext","-f","1","-l","3","-layout",str(path),"-"]
            run=subprocess.run(cmd,capture_output=True,timeout=30)
            text=run.stdout.decode("utf-8","replace")
            rec["pdftotext_returncode"]=run.returncode
            rec["extracted_chars_first_3_pages"]=len(text)
            rec["words_first_3_pages"]=len(text.split())
            rec["price_like_occurrences"]=len(re.findall(r'\b\d{1,3}[,.]\d{2}\b',text))
            rec["sample_ordinary_lines"]=[re.sub(r'\s+',' ',line.strip())[:85] for line in text.splitlines()
                                          if 3<len(line.strip())<100][:9]
            if shutil.which("pdfinfo"):
                info=subprocess.run(["pdfinfo",str(path)],capture_output=True,timeout=15)
                inf=info.stdout.decode("utf-8","replace")
                m=re.search(r'^Pages:\s+(\d+)',inf,re.M)
                rec["pages"]=int(m.group(1)) if m else None
        rec["status"]="PDF text extraction tested"
    except HTTPError as e:rec["http"]=e.code;rec["status"]="HTTP error"
    except Exception as e:rec["status"]=type(e).__name__+":"+str(e)[:150]
    output.append(rec)
Path("results").mkdir(exist_ok=True)
Path("results/netto_brochure_pdf_text_diagnostic.json").write_text(json.dumps({
    "timestamp_utc":datetime.now(timezone.utc).isoformat(),
    "note":"No entire PDFs or their text saved; samples and metrics only",
    "tests":output
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(output,ensure_ascii=False,indent=2))
