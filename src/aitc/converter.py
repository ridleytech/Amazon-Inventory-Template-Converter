from __future__ import annotations
import json
import datetime as dt
from typing import Dict, Any, List, Optional
import pandas as pd

from .mappings import slug_header, SYN, normalize_option_key

Number = Optional[float]

def to_number(x) -> Number:
    if x is None:
        return None
    try:
        s = str(x).strip()
        if s == "":
            return None
        s = s.replace("$", "").replace(",", "")
        return float(s)
    except Exception:
        try:
            return float(x)
        except Exception:
            return None

def drop_empty(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, str):
            if v.strip() == "":
                continue
        if isinstance(v, list):
            v2 = [vv for vv in v if vv not in (None, "", float("nan"))]
            if not v2:
                continue
            out[k] = v2
            continue
        out[k] = v
    return out

def read_excel_any(path: str, sheet: Optional[str] = None) -> pd.DataFrame:
    if sheet:
        return pd.read_excel(path, sheet_name=sheet, dtype=str, engine="openpyxl")
    xls = pd.ExcelFile(path, engine="openpyxl")
    for s in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=s, dtype=str, engine="openpyxl")
        if df.dropna(how="all").shape[0] > 0 and df.dropna(how="all").shape[1] > 0:
            return df
    return pd.read_excel(path, dtype=str, engine="openpyxl")

def build_header_map(cols: List[str]) -> Dict[str, str]:
    raw_slugs = [slug_header(c) for c in cols]
    hmap: Dict[str, str] = {}
    for rs, orig in zip(raw_slugs, cols):
        mapped = None
        for canon, names in SYN.items():
            if rs in names:
                mapped = canon
                break
        hmap[rs] = mapped or rs
    return hmap

def row_get(row: Dict[str, Any], hmap: Dict[str, str], canon: str) -> Optional[str]:
    for rs, c in hmap.items():
        if c == canon:
            v = row.get(rs) or row.get(c)
            if v is not None:
                s = str(v).strip()
                if s != "" and s.lower() != "nan":
                    return s
    return None

def collect_bullets(row: Dict[str, Any], hmap: Dict[str, str]) -> List[str]:
    out = []
    for i in range(1, 6):
        v = row_get(row, hmap, f"bullet{i}")
        if v:
            out.append(v)
    return out

def collect_images(row: Dict[str, Any], hmap: Dict[str, str]) -> List[str]:
    images = []
    m = row_get(row, hmap, "main_image")
    if m: images.append(m)
    for i in range(1, 8):
        v = row_get(row, hmap, f"other_image{i}")
        if v: images.append(v)
    seen, out = set(), []
    for url in images:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out

def parse_options(row: Dict[str, Any], hmap: Dict[str, str]) -> Dict[str, str]:
    opts = {}
    for raw_slug, canon in hmap.items():
        if canon in ("size_name", "metal_type", "color_name", "metal_stamp"):
            val = row.get(raw_slug)
            if val is None:
                continue
            s = str(val).strip()
            if s == "" or s.lower() == "nan":
                continue
            key = normalize_option_key(canon)
            if key:
                label = s
                if key == "karat":
                    label = s.lower().replace(" ", "").replace("kt", "k")
                    if not label.endswith("k") and label.isdigit():
                        label = f"{label}k"
                opts[key] = label
    return opts

def convert(path: str, sheet: Optional[str] = None, infer_single: bool = False):
    df = read_excel_any(path, sheet=sheet)
    if df.empty:
        return []

    df.columns = [slug_header(c) for c in df.columns]
    df = df.dropna(how="all")
    rows = df.fillna("").astype(str).to_dict(orient="records")
    hmap = build_header_map(list(df.columns))

    parents = {}
    children_by_parent = {}

    for r in rows:
        parentage = (row_get(r, hmap, "parentage") or "").lower()
        sku = row_get(r, hmap, "sku")
        parent_sku = row_get(r, hmap, "parent_sku") or row_get(r, hmap, "sku")
        if not sku:
            continue
        if parentage == "parent":
            parents[parent_sku] = r
            children_by_parent.setdefault(parent_sku, [])
        elif parentage == "child":
            if not parent_sku:
                parent_sku = sku
            children_by_parent.setdefault(parent_sku, []).append(r)
        else:
            if infer_single:
                parents[sku] = r
                children_by_parent.setdefault(sku, []).append(r)
            else:
                if parent_sku and parent_sku != sku:
                    children_by_parent.setdefault(parent_sku, []).append(r)
                else:
                    parents.setdefault(sku, r)

    docs = []

    for parent_key, prow in parents.items():
        childs = children_by_parent.get(parent_key, [])

        title = row_get(prow, hmap, "title")
        brand = row_get(prow, hmap, "brand")
        desc = row_get(prow, hmap, "description")
        bullets = collect_bullets(prow, hmap)
        images = collect_images(prow, hmap)

        price = to_number(row_get(prow, hmap, "standard_price"))
        sale = to_number(row_get(prow, hmap, "sale_price"))

        variants = []
        option_values = {"ring_size": set(), "metal_type": set(), "karat": set()}
        for crow in childs:
            vsku = row_get(crow, hmap, "sku") or ""
            vprice = to_number(row_get(crow, hmap, "standard_price"))
            vsale = to_number(row_get(crow, hmap, "sale_price"))
            vopts = parse_options(crow, hmap)
            for k, v in vopts.items():
                if k in option_values:
                    option_values[k].add(v)
            vdoc = drop_empty({
                "sku": vsku,
                "options": vopts or None,
                "price": vprice,
                "salePrice": vsale,
            })
            if vdoc:
                variants.append(vdoc)

        optionSchema = {k: sorted(list(v)) for k, v in option_values.items() if v}

        if price is None and variants:
            prices = [(v.get("salePrice") or v.get("price")) for v in variants if (v.get("salePrice") or v.get("price")) is not None]
            if prices:
                price = min(prices)

        doc = drop_empty({
            "_id": parent_key,
            "sku": parent_key,
            "title": title,
            "brand": brand,
            "description": desc,
            "bullets": bullets or None,
            "images": images or None,
            "price": price,
            "salePrice": sale,
            "optionSchema": optionSchema or None,
            "variants": variants or None,
            "createdAt": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        })
        docs.append(doc)

    return docs
