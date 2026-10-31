#!/usr/bin/env python3
"""Ordinary Chrome-headless rendering of public Netto pages, with no stealth/CAPTCHA bypass."""
import json,re,subprocess,shutil
from pathlib import Path
from datetime import datetime,timezone
urls=[
    "https://www.netto-online.de/filialen/berlin-charlottenburg/wilmersdorfer-str-46/7679/",
    "https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm/1013",
]
rows=[]
chrome=next((shutil.which(x) for x in ("google-chrome","chromium","chromium-browser","google-chrome-stable") if shutil.which(x)),None)
for url in urls:
    item={"url":url,"browser_available":bool(chrome)}
    if not chrome:
        item["outcome"]="Chrome executable not installed"
        rows.append(item);continue
    try:
        proc=subprocess.run([
           chrome,"--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage",
           "--no-first-run","--no-default-browser-check",
           "--virtual-time-budget=15000","--dump-dom",url
        ],capture_output=True,text=True,timeout=45)
        html=proc.stdout[:7_000_000]
        item["return_code"]=proc.returncode
        item["html_length"]=len(html)
        item["title"]=(re.search(r"<title[^>]*>(.*?)</title>",html,re.I|re.S).group(1)[:130]
                       if re.search(r"<title[^>]*>(.*?)</title>",html,re.I|re.S) else None)
        item["product_markers"]={key:(key.casefold() in html.casefold()) for key in
                                 ("Filial-Angebote","Haribo Fruchtgummi","Giovanni Ferrari","02.11.26")}
        item["blocking_indicators"]={key:(key.casefold() in html.casefold()) for key in
                                    ("access denied","captcha","verifizierung erforderlich","403 forbidden","please enable javascript")}
        item["content_markers"]={
            "json_ld":html.count("application/ld+json"),
            "netto_offer":len(re.findall(r'filial-angebot',html,re.I)),
            "offer_field":len(re.findall(r'["\x27]offers["\x27]\s*:',html,re.I))
        }
        # Never attempt CAPTCHA challenges or any bot-detection mitigation.
        if any(item["blocking_indicators"].values()):
            item["result"]="BLOCKED/CHALLENGE - no further actions"
        else:item["result"]="ordinary DOM analyzed"
    except Exception as exc:
        item["result"]="ERROR";item["reason"]=type(exc).__name__+":"+str(exc)[:150]
    rows.append(item)
Path("results").mkdir(exist_ok=True)
Path("results/netto_standard_chrome.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(rows,ensure_ascii=False,indent=2))
