#!/usr/bin/env python3
"""Inspect structured price signals inside public Netto webshop HTML.

Read-only single page, minimal output: only keys/counts and numeric values
clearly paired with EUR currency. No full HTML, cookies or private tokens saved.
"""
import json,re,urllib.request,urllib.error,html
from datetime import datetime,timezone
from pathlib import Path
URLS=[
"https://www.netto-online.de/koelln-haferflocken-kernig-500-g-10er-pack/p-2162281000",
"https://www.netto-online.de/cornflakes-muesli/c-N011501",
]
PATTERNS={
"next_data":r'id=["\x27]__NEXT_DATA__["\x27]',
"next_f":r'self\.__next_f',
"nuxt":r'__NUXT__',
"apollo":r'__APOLLO_STATE__',
"redux":r'__PRELOADED_STATE__',
"gtm":r'dataLayer\s*=',
"json_price":r'"(?:currentPrice|sellingPrice|salePrice|price|amount|priceValue|finalPrice)"\s*:',
"json_currency":r'"(?:priceCurrency|currencyCode|currency)"\s*:',
"money_str":r'\b\d{1,4}[.,]\d\d\s*(?:€|EUR)\b',
"html_currency_eur":r'&euro;|&#8364;|€',
"item_price":r'itemprop=["\x27]price["\x27]',
"data_price":r'data-(?:product-)?price(?:=|-)',
"price_class":r'class=["\x27][^"\x27]{0,120}price',
"product_id":r'2162281000',
"api_endpoint":r'api/[a-zA-Z]{1,30}/',
}
OUT=Path("results/netto_online_embedded_price_diagnostic.json")
def main():
    items=[]
    for url in URLS:
        item={"url":url,"checked_utc":datetime.now(timezone.utc).isoformat()}
        try:
            with urllib.request.urlopen(urllib.request.Request(
                url,headers={"User-Agent":"ErnaehrungsgedaechnisResearch/2.2 (public webshop price signal verification)",
                             "Accept":"text/html"}),timeout=25) as resp:
                doc=resp.read(2100000).decode("utf8","replace")
                item["http_status"]=resp.status
            item["pattern_counts"]={k:len(re.findall(v,doc,re.I|re.S)) for k,v in PATTERNS.items()}
            for k in ("json_price","json_currency","money_str"):
                examples=[]
                for match in re.finditer(PATTERNS[k],doc,re.I|re.S):
                    after=doc[match.end():match.end()+60]
                    if k=="json_price":
                        found=re.search(r'^\s*(?:"(\d{1,5}(?:[.,]\d{1,3})?)"|(\d{1,5}(?:[.,]\d{1,3})?))',after)
                        if found:examples.append({"field":match.group().strip('": '),"number":found.group(1) or found.group(2)})
                    elif k=="json_currency":
                        found=re.search(r'^\s*"([A-Z]{3})"',after)
                        if found:examples.append({"currency":found.group(1)})
                    else:examples.append({"money":match.group()[:30]})
                    if len(examples)>=12:break
                item[k+"_examples"]=examples
            # Diagnostic for current product only: a small sanitized excerpt
            # around exactly the candidate JSON price. No HTML body stored.
            excerpts=[]
            for match in list(re.finditer(r'"price"\s*:\s*"?\d+(?:[.,]\d+)?"?',doc,re.I))[:4]:
                start=max(0,match.start()-180)
                end=min(len(doc),match.end()+200)
                snippet=doc[start:end]
                snippet=re.sub(r'https?://[^\s"<>]+','[URL]',snippet)
                snippet=re.sub(r'[A-Za-z0-9+/=]{80,}','[LONG_LITERAL]',snippet)
                snippet=re.sub(r'<[^>]+>',' ',snippet)
                excerpts.append(snippet[:380])
                tag_start=doc.rfind("<script",0,match.start())
                tag_end=doc.find(">",tag_start) if tag_start>=0 else -1
                if tag_start>=0 and 0<=tag_end<match.start():
                    item.setdefault("containing_script_open_tags",[]).append(doc[tag_start:tag_end+1][:240])

            item["price_context_examples"]=excerpts
            item["result"]="HTML_MEASURED"
        except urllib.error.HTTPError as e:
            item["http_status"]=e.code;item["result"]="HTTP_ERROR"
        except Exception as e:
            item["result"]="ERROR";item["error_type"]=type(e).__name__
        items.append(item)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(items,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(items,ensure_ascii=False))
if __name__=="__main__":main()
