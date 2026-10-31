#!/usr/bin/env python3
"""Enumerate *all* Retrofit GET interface annotations from retailer DEX bytecode.

A static read-only complement to tools/broader_apk_discovery.py.
This does not guess interface names. It parses declared method annotations
in every DEX file (including non-config XAPK splits) via androguard.
It does not inspect live traffic, invoke retailer APIs or use app secrets.
"""
from __future__ import annotations
import argparse
import json
import re
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from androguard.core.dex import DEX
from targeted_jadx_retailer_apis import download

PACKAGES = {
    "aldi_sued": "de.apptiv.business.android.aldi_de",
    "rewe": "de.rewe.app.mobile",
    "edeka": "de.edeka.genuss",
    "netto_marken_discount": "com.valuephone.vpnetto",
    "penny": "de.penny.app",
    "penny_scan_go": "de.penny.scango",
    "kaufland": "com.kaufland.Kaufland",
}
HTTP = {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"}
CATEGORY_RE = re.compile(r"price|product|ean|article|barcode|catalog|"
                         r"stock|assort|inventory|category|categories|"
                         r"market|store|offer|scan|item|search", re.I)
WRITE_RE = re.compile(r"checkout|payment|purchase|login|token|account|"
                      r"basket|user|profile|session|customer|device|order", re.I)
SAFE_ROUTE = re.compile(r"/?[a-zA-Z0-9_{}./-]{2,190}")
SAFE_PARAM = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{0,60}")


def value(v):
    """Return scalar/string values from androguard's encoded DEX element."""
    try:
        v = v.get_value()
    except AttributeError:
        pass
    if isinstance(v, bytes):
        return v.decode("utf8", "replace")
    if isinstance(v, (int, float, bool, str)):
        return v
    return None


def annotations(cm, annotation_set_off):
    """Read a DEX annotation set by its offset, discarding complex values."""
    if not annotation_set_off:
        return []
    output = []
    aset = cm.get_annotation_set_item(annotation_set_off)
    for reference in aset.get_annotation_off_item():
        item = reference.get_annotation_item().get_annotation()
        kind = str(cm.get_type(item.get_type_idx()))
        parts = {}
        for element in item.get_elements():
            field = cm.get_string(element.get_name_idx())
            val = value(element.get_value())
            if isinstance(field, bytes):
                field = field.decode("utf8", "replace")
            if val is not None:
                parts[str(field)] = val
        output.append((kind, parts))
    return output


def dex_endpoints(raw: bytes):
    dex = DEX(raw)
    cm = dex.get_class_manager()
    entries = []
    stats = Counter()
    for clazz in dex.get_classes():
        stats["classes"] += 1
        try:
            directory = clazz.annotations_directory_item
            if directory is None:
                continue
            methods = directory.get_method_annotations() or []
            if not methods:
                continue
        except (AttributeError, TypeError, ValueError):
            continue
        for method in methods:
            stats["annotated_methods"] += 1
            try:
                method_anns = annotations(cm, method.get_annotations_off())
            except Exception:
                stats["annotation_parse_failures"] += 1
                continue
            verb, route = None, None
            for fqname, fields in method_anns:
                if "retrofit2/http/" not in fqname:
                    continue
                tag = fqname.split("/")[-1].rstrip(";")
                if tag in HTTP:
                    verb, route = tag, fields.get("value", "")
                elif tag == "HTTP":
                    verb, route = fields.get("method"), fields.get("path", "")
            if not verb:
                continue
            stats["retrofit_endpoints"] += 1
            if verb not in ("GET", "HEAD") or not isinstance(route, str):
                continue
            route = route.split("?", 1)[0]
            if not SAFE_ROUTE.fullmatch(route) or WRITE_RE.search(route):
                continue
            if not CATEGORY_RE.search(route):
                continue
            iface = clazz.get_name()
            if isinstance(iface, bytes):
                iface = iface.decode("utf8", "replace")
            iface = str(iface).strip("L;").replace("/", ".")
            if len(iface) > 170:
                iface = iface[:170]
            entry = {"verb": verb, "route": route, "interface": iface,
                     "query_params": [], "path_params": []}
            # Method parameter annotations belong to method_idx, if present.
            try:
                for p in directory.get_parameter_annotations() or []:
                    if p.get_method_idx() != method.get_method_idx():
                        continue
                    ref = cm.get_obj_by_offset(p.get_annotations_off())
                    for a in ref.get_list():
                        for kind, fields in annotations(cm, a.get_annotations_off()):
                            if "retrofit2/http/" not in kind:
                                continue
                            tag = kind.split("/")[-1].rstrip(";")
                            name = fields.get("value", "")
                            if (isinstance(name, str) and SAFE_PARAM.fullmatch(name)
                                    and not WRITE_RE.search(name)):
                                if tag == "Query":
                                    entry["query_params"].append(name)
                                elif tag == "Path":
                                    entry["path_params"].append(name)
            except Exception:
                stats["parameter_parse_failures"] += 1
            entry["query_params"] = sorted(set(entry["query_params"]))[:24]
            entry["path_params"] = sorted(set(entry["path_params"]))[:12]
            entries.append(entry)
    return entries, stats


def iter_dex(source):
    """Base + non-config XAPK splits; APK internals; bounded extraction."""
    with zipfile.ZipFile(source) as outer:
        names = [n for n in outer.namelist() if n.lower().endswith(".apk")]
        if not names:
            names = [None]
        for bundle_name in names:
            if bundle_name and re.search(
                    r"(?:config\.|split_config\.|/config\.|\.config\.)",
                    bundle_name, re.I):
                continue
            if bundle_name:
                raw_apk = outer.read(bundle_name)
                if len(raw_apk) > 260_000_000:
                    continue
                import io
                apk = zipfile.ZipFile(io.BytesIO(raw_apk))
            else:
                apk = outer
            try:
                for dex_name in apk.namelist():
                    if not re.fullmatch(r"classes\d*\.dex", dex_name):
                        continue
                    info = apk.getinfo(dex_name)
                    if info.file_size > 90_000_000:
                        continue
                    yield (bundle_name or "<apk>", dex_name, apk.read(dex_name))
            finally:
                if bundle_name:
                    apk.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app", required=True, choices=sorted(PACKAGES))
    args = p.parse_args()
    app = args.app
    report = {
        "app": app,
        "expected_package": PACKAGES[app],
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "method": "All-method DEX Retrofit annotation enumeration via androguard",
        "limits": "Only GET/HEAD product-relevant routes retained; Flutter and "
                  "Hermes native/JS and dynamic construction not decoded",
        "live_requests": "None",
    }
    with tempfile.TemporaryDirectory() as t:
        pkg = Path(t) / "android_package.zip"
        try:
            stamp = download(f"https://d.apkpure.com/b/APK/{PACKAGES[app]}?version=latest", pkg)
            report["sha256"] = stamp["sha256"]
            report["package_bytes"] = stamp["bytes"]
            all_entries = []
            counts = Counter()
            parts = []
            for source, dex_name, raw in iter_dex(pkg):
                counts["dex_files"] += 1
                try:
                    found, stats = dex_endpoints(raw)
                    all_entries += found
                    counts.update(stats)
                    parts.append({"bundle_part": source[-75:], "dex_file": dex_name,
                                  "bytes": len(raw), "parsed": True})
                except Exception as exc:
                    counts["dex_failures"] += 1
                    parts.append({"bundle_part": source[-75:], "dex_file": dex_name,
                                  "bytes": len(raw), "parsed": False,
                                  "failure_type": type(exc).__name__})
            report["counts"] = dict(counts)
            report["dex_parts"] = parts
            report["product_get_endpoints"] = list({
                (e["verb"], e["route"], e["interface"]): e for e in all_entries
            }.values())[:350]
            report["result"] = "STATIC_ENUMERATION_COMPLETE" if counts["dex_files"] > 0 else "NO_DEX_FOUND"
        except Exception as exc:
            report["result"] = "ERROR"
            report["error_type"] = type(exc).__name__
    target = Path("results/retailer_retrofit_annotations")
    target.mkdir(parents=True, exist_ok=True)
    out = target / (app + ".json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("RESULT=" + json.dumps({
        "app": app,
        "result": report["result"],
        "counts": report.get("counts"),
        "interesting_routes": len(report.get("product_get_endpoints", [])),
        "file": str(out),
    }))
    if report["result"] != "STATIC_ENUMERATION_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
