#!/usr/bin/env python3
"""Read-only feasibility study: EDEKA gateway and documented shopreme interfaces.

No authentication, login, external market session, product enumeration, API
endpoint guessing, or attempts to work around access controls. Only vendor
landing pages and published documentation are requested once each.
"""
import json,re,sys
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser
from pathlib import Path

UA="Ernaehrungsgedaechtnis-Research/3.7 (public vendor documentation, one-shot)"
urls=[
 ("EDEKA B2C API gateway landing","https://b2c-gw.api.edeka/"),
 ("shopreme DataHub overview","https://docs.shopreme.com/kb/datahub/overview"),
 ("shopreme store price import docs","https://docs.shopreme.com/kb/management-console/overview"),
 ("shopreme basket price evaluation","https://docs.shopreme.com/kb/datahub/outbound-api/baskets-and-pricing"),
 ("shopreme product catalog docs","https://docs.shopreme.com/kb/management-console/product-catalogue"),
 ("shopreme DataHub store-specific product/price jobs","https://docs.shopreme.com/kb/management-console/datahub-import-jobs"),
 ("shopreme product detail with default and market prices","https://docs.shopreme.com/kb/management-console/product-detail-page"),
]
class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.fragments=[]
 def handle_data(self,x):
  if x.strip():self.fragments.append(x.strip())
out={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"checks":[],"purpose":"publisher documentation and gateway public landing only"}
robot_cache={}
for label,url in urls:
 rec={"label":label,"host":urlparse(url).netloc,"path":urlparse(url).path}
 origin=urlparse(url).scheme+"://"+urlparse(url).netloc
 if origin not in robot_cache:
  try:
   with urlopen(Request(origin+"/robots.txt",headers={"User-Agent":UA}),timeout=12) as f:
    rule=RobotFileParser();rule.parse(f.read(200000).decode("utf8","replace").splitlines())
    robot_cache[origin]=rule
  except HTTPError as e:robot_cache[origin]=None if e.code==404 else "unknown"
  except Exception:robot_cache[origin]="unknown"
 bot=robot_cache[origin]
 if bot=="unknown" or (bot is not None and not bot.can_fetch(UA,url)):
  rec["result"]="SKIPPED robots policy unavailable/disallows"
  out["checks"].append(rec);continue
 try:
  with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"}),timeout=20) as f:
   rec["http_status"]=f.status
   content=f.read(1_600_000)
  text=content.decode("utf8","replace")
  parser=TextParser();parser.feed(text)
  prose=" ".join(parser.fragments)
  rec["html_bytes"]=len(content)
  signals={
   "edeka_external_permission_required":bool(re.search(r"contact EDEKA to get access",prose,re.I)),
   "shopreme_product_import":bool(re.search(r"product import|import products",prose,re.I)),
   "shopreme_price_import":bool(re.search(r"price import|import.*prices",prose,re.I)),
   "shopreme_prices_by_store":bool(re.search(r"each product.s prices for each store|specific store|per.store",prose,re.I)),
   "shopreme_cart_evaluate":bool(re.search(r"/evaluate",text,re.I)),
   "shopreme_management_console":bool(re.search(r"Management Console",prose,re.I)),
   "shopreme_store_price_field":bool(re.search(r"storePrices",prose,re.I)),
   "shopreme_price_update_delta":bool(re.search(r"delta updates|price import is quicker",prose,re.I)),
   "shopreme_strike_price_field":bool(re.search(r"strikePrice",prose,re.I)),
   "shopreme_api_authentication_required":bool(re.search(r"API Tokens|basic authentication|sign in",prose,re.I)),
  }
  rec["signals"]=signals
  rec["result"]="PUBLIC_DOCS_HTTP_OK"
 except HTTPError as e:
  rec["http_status"]=e.code
  rec["result"]="HTTP_ERROR"
 except Exception as e:
  rec["result"]=type(e).__name__+":"+str(e)[:120]
 out["checks"].append(rec)
Path("results").mkdir(exist_ok=True)
Path("results/vendor_scan_go_feasibility.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(out,indent=2,ensure_ascii=False))
