#!/usr/bin/env python3
"""Broad, bounded read-only discovery of grocery APK product interfaces.

Designed for GitHub Actions public runners and educational static analysis.
No APK execution, traffic interception, live retailer API access, accounts,
tokens, decompiled full-source release or certificate extraction.

Unlike a fixed-endpoint search, this discovers *candidate* Retrofit classes
from the APK itself and reads method annotations with jadx. Flutter/Hermes
binaries are only string-scanned; dynamic endpoints and obfuscated classes
can remain invisible.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from real_apk_static_analysis import inspect_archive
from targeted_jadx_retailer_apis import download, official_jadx, choose_base_apk

APPS = {
    "aldi_sued": "de.apptiv.business.android.aldi_de",
    "rewe": "de.rewe.app.mobile",
    "edeka": "de.edeka.genuss",
    "netto_marken_discount": "com.valuephone.vpnetto",
    "penny": "de.penny.app",
    "penny_scan_go": "de.penny.scango",
    "kaufland": "com.kaufland.Kaufland",
}
PER_APP_LIMIT = 10
PER_CLASS_TIMEOUT = 90
CANDIDATE_NAME = re.compile(
    r"(Product|Item|Price|Catalog|Catalogue|Article|Search|Barcode|"
    r"Scanner|Scan|Store|Shop|Market|Offer|Assortment|Inventory|Sync|"
    r"Category|Promotion)", re.I
)
INTERFACE_SUFFIX = re.compile(
    r"(Api|ApiService|Service|Repository|DataSource|Endpoint|Client)$", re.I
)
RISKY_PATH = re.compile(
    r"auth|login|token|user|account|password|pay|checkout|purchase|"
    r"basket|cart|device|profile|session|receipt|coupon", re.I
)
PRODUCT_PATH = re.compile(
    r"product|price|item|barcode|ean|catalog|category|store|market|"
    r"article|search|availability|offer", re.I
)
DEX_NAME = re.compile(rb"L([A-Za-z_$][A-Za-z_0-9$]*(?:/[A-Za-z_$][A-Za-z_0-9$]*)+);")
ROUTE_RE = re.compile(
    r'@(GET|HEAD)\s*\(\s*"([^"]{1,220})"\s*\)', re.I
)
QUERY_RE = re.compile(
    r'@(?:Query|Path)\(\s*"([A-Za-z_][A-Za-z_0-9-]{0,60})"\s*\)'
)


def candidates_from_dex(apk: Path):
    names = set()
    with zipfile.ZipFile(apk) as z:
        for entry in z.infolist():
            if not re.fullmatch(r"classes\d*\.dex", entry.filename):
                continue
            if entry.file_size > 85_000_000:
                continue
            data = z.read(entry)
            for match in DEX_NAME.finditer(data):
                name = match.group(1).decode("ascii", "ignore").replace("/", ".")
                last = name.rsplit(".", 1)[-1]
                if (len(name) < 180 and CANDIDATE_NAME.search(last)
                        and INTERFACE_SUFFIX.search(last)
                        and not re.search(
                            r"(^|\.)(android|google|facebook|firebase|"
                            r"retrofit2|okhttp3|squareup|reactnative)(\.|$)",
                            name, re.I)):
                    names.add(name)

    def score(name):
        tail = name.rsplit(".", 1)[-1]
        s = 0
        if re.search("Product|Price|Item|Catalog|Catalogue|Search", tail, re.I):
            s += 12
        if re.search("Download|Sync|Category|Barcode|Scan", tail, re.I):
            s += 8
        if re.search("Api$", tail, re.I):
            s += 6
        if re.search("retailer|kaufland|rewe|penny|netto|edeka|aldi|"
                     "selfscan|valuephone", name, re.I):
            s += 5
        if re.search("offer|coupon|basket|cart", tail, re.I):
            s -= 3
        return (-s, len(name), name)

    return sorted(names, key=score)


def strings_report(path):
    obj = {
        "scanner": {
            "hosts": {},
            "paths": {},
            "signal_hits": {},
            "scanned_bytes": 0,
            "scanned_files": 0,
            "files": []
        }
    }
    inspect_archive(path, obj)
    scan = obj["scanner"]
    # Store only already-sanitized path templates and public hostnames.
    paths = [p for p, count in scan["paths"].most_common()
             if PRODUCT_PATH.search(p) and not RISKY_PATH.search(p)]
    hosts = [h for h, count in scan["hosts"].most_common()
             if re.search(r"aldi|rewe|penny|netto|kaufland|edeka|"
                          r"lidl|valuephone|schwarz|shopreme", h, re.I)]
    return {
        "scanned_files": scan["scanned_files"],
        "scanned_bytes": scan["scanned_bytes"],
        "candidate_hosts": hosts[:70],
        "candidate_paths": paths[:220],
        "method": "DEX/native/asset static string extraction, no live requests"
    }


def decompile_candidate(jadx: Path, apk: Path, clazz: str, outfile: Path):
    cmd = [
        str(jadx), "--no-res", "--threads-count", "2",
        "--single-class", clazz, "--single-class-output",
        str(outfile), str(apk)
    ]
    try:
        p = subprocess.run(cmd, text=True, capture_output=True,
                           timeout=PER_CLASS_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"class": clazz, "status": "TIMEOUT"}
    if not outfile.exists():
        return {"class": clazz, "status": "NO_OUTPUT", "exit_code": p.returncode}
    code = outfile.read_text(encoding="utf-8", errors="replace")[:700_000]
    result = []
    for verb, route in ROUTE_RE.findall(code):
        route = route.split("?", 1)[0]
        if (re.fullmatch(r"/?[A-Za-z_0-9{}./-]{3,180}", route)
                and PRODUCT_PATH.search(route) and not RISKY_PATH.search(route)):
            result.append({"verb": verb.upper(), "path": route})
    hints = sorted(set(QUERY_RE.findall(code)))
    hints = [h for h in hints if not RISKY_PATH.search(h)]
    return {
        "class": clazz,
        "status": "INSPECTED",
        "http_product_routes": list({r["verb"] + " " + r["path"]: r
                                     for r in result}.values())[:40],
        "parameter_names_in_class": hints[:40],
        "note": "Parameter names not necessarily paired to individual routes"
    }


def inspect(app, jadx, root):
    r = {"app": app, "package": APPS[app]}
    source = root / "public_package.zip"
    apk = root / "base.apk"
    try:
        meta = download(
            f"https://d.apkpure.com/b/APK/{APPS[app]}?version=latest",
            source
        )
        r["package_sha256"] = meta["sha256"]
        r["download_bytes"] = meta["bytes"]
        r["base_apk_entry"] = choose_base_apk(source, apk)
        r["raw_strings"] = strings_report(apk)
        names = candidates_from_dex(apk)
        r["candidate_class_count"] = len(names)
        r["candidate_class_names_sample"] = names[:70]
        classes = []
        for i, name in enumerate(names[:PER_APP_LIMIT]):
            classes.append(decompile_candidate(jadx, apk, name,
                        root / f"class_{i}.java"))
        r["decompiled_classes"] = classes
        r["result"] = "STATIC_SCAN_FINISHED"
    except Exception as exc:
        r["result"] = "UNAVAILABLE_OR_ERROR"
        r["error_type"] = type(exc).__name__
        # Intentionally do not log exception messages containing possible URLs.
    return r


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", choices=sorted(APPS), required=True)
    args = parser.parse_args()
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Unprivileged local static APK analysis; no live store APIs",
        "uncertainty": "No confirmation of price, current API availability, "
                       "catalogue completeness, or legal reuse rights.",
        "limitations": "Heuristic class discovery; JADX samples at most 10 "
                       "classes. Flutter/Hermes is string-scanned, not decoded.",
    }
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        try:
            jadx, info = official_jadx(root)
            result["jadx_version"] = "1.5.6"
            result["jadx_sha256"] = info["sha256"]
            sub = root / args.app
            sub.mkdir()
            result["analysis"] = inspect(args.app, jadx, sub)
        except Exception as exc:
            result["analysis"] = {
                "app": args.app, "result": "GLOBAL_ERROR",
                "error_type": type(exc).__name__
            }
    out = Path("results") / "broader_apk_discovery"
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{args.app}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf8")
    status = result["analysis"].get("result", "UNKNOWN")
    print(f"RESULT_APP={args.app}; RESULT_STATUS={status}; REPORT={target}")
    # Do not say PASS for unavailable packages; still archive diagnosis.
    if status != "STATIC_SCAN_FINISHED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
