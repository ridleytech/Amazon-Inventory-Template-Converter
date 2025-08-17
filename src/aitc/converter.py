from __future__ import annotations
import re, json, datetime as dt
from typing import Dict, Any, List, Optional
import pandas as pd

# ----- helpers -----
def _slug(s: str) -> str:
    s = (s or "").strip()
    return re.sub(r"\s+", " ", s)

def _to_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return None
    s = s.replace("$", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        try:
            return float(re.sub(r"[^0-9.\-]", "", s))
        except Exception:
            return None

def _drop_empty(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, str):
            if v.strip() == "" or v.strip().lower() == "nan":
                continue
        if isinstance(v, list):
            v2 = [vv for vv in v if vv not in (None, "", float("nan"))]
            if not v2:
                continue
            out[k] = v2
            continue
        if isinstance(v, dict):
            v2 = _drop_empty(v)
            if not v2:
                continue
            out[k] = v2
            continue
        out[k] = v
    return out

def _first_nonempty(*vals) -> Optional[str]:
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            return s
    return None

SKU_SIZE_RE = re.compile(r"-([0-9]{2,3})$")

def infer_ring_size_from_sku(sku: str) -> Optional[str]:
    """Infer ring size from trailing -40/-45/-100 => 4.0/4.5/10.0"""
    if not sku:
        return None
    m = SKU_SIZE_RE.search(str(sku))
    if not m:
        return None
    n = m.group(1)
    try:
        iv = int(n)
        if iv >= 100:
            return f"{iv/10:.1f}".rstrip("0").rstrip(".")
        else:
            return f"{iv/10:.1f}".rstrip("0").rstrip(".")
    except Exception:
        return None

# Price columns in the new template
US_OUR_PRICE = "purchasable_offer[marketplace_id=ATVPDKIKX0DER]#1.our_price#1.schedule#1.value_with_tax"
US_DISC_PRICE = "purchasable_offer[marketplace_id=ATVPDKIKX0DER]#1.discounted_price#1.schedule#1.value_with_tax"
LIST_PRICE = "list_price"

IMAGE_COLS = ["main_image_url"] + [f"other_image_url{i}" for i in range(1, 15)] + ["swatch_image_url"]

# ----- core -----
def read_template(path: str) -> pd.DataFrame:
    """Read the sheet named 'Template', using row 2 as headers and data starting row 3."""
    df = pd.read_excel(path, sheet_name="Template", header=None, dtype=object, engine="openpyxl")
    if df.shape[0] < 3:
        # Not enough rows to contain headers + data
        return pd.DataFrame()
    headers = [str(x) if x is not None else "" for x in list(df.iloc[2, :])]
    data = df.iloc[3:, :].copy()
    data.columns = headers
    # Drop fully empty rows
    data = data.dropna(how="all")
    # Normalize types: keep as str where possible
    for c in data.columns:
        try:
            data[c] = data[c].astype(str)
        except Exception:
            pass
    # Keep rows with item_sku present
    if "item_sku" in data.columns:
        data = data[data["item_sku"].astype(str).str.strip() != ""]
    return data

def collect_images(row: pd.Series) -> List[str]:
    urls = []
    for c in IMAGE_COLS:
        if c in row.index:
            val = str(row.get(c, "")).strip()
            if val and val.lower() != "nan":
                urls.append(val)
    # de-dupe keep order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def pick_title(row: pd.Series) -> Optional[str]:
    # Your file uses 'certificate_number' as a descriptive name; fallbacks provided
    return _first_nonempty(
        row.get("certificate_number"),
        row.get("item_name"),
        row.get("model"),
        row.get("pattern_name"),
        row.get("product_description"),
    )

def pick_description(row: pd.Series) -> Optional[str]:
    return _first_nonempty(
        row.get("model"),
        row.get("product_description"),
        row.get("pattern_name"),
    )

def pick_price_fields(row: pd.Series) -> (Optional[float], Optional[float]):
    p = None
    sp = None
    if US_OUR_PRICE in row.index:
        p = _to_float(row.get(US_OUR_PRICE))
    if LIST_PRICE in row.index and p is None:
        p = _to_float(row.get(LIST_PRICE))
    if US_DISC_PRICE in row.index:
        sp = _to_float(row.get(US_DISC_PRICE))
    return p, sp

def parse_variant_options(row: pd.Series) -> Dict[str, str]:
    opts: Dict[str, str] = {}
    # ring size
    rs = _first_nonempty(row.get("ring_size"), row.get("size_name"))
    if not rs:
        rs = infer_ring_size_from_sku(row.get("item_sku"))
    if rs:
        opts["ring_size"] = str(rs).strip()
    # metal
    mt = _first_nonempty(row.get("metal_type"))
    if mt:
        opts["metal_type"] = str(mt).strip()
    # karat from metals_metal_stamp if it looks like "14k"/"18k" etc.
    ms = _first_nonempty(row.get("metals_metal_stamp"))
    if ms:
        s = str(ms).strip().lower()
        m = re.search(r"(10|14|18|22|24)\s*k", s)
        if m:
            opts["karat"] = f"{m.group(1)}k"
    return opts

def convert(path: str) -> List[Dict[str, Any]]:
    df = read_template(path)
    if df.empty:
        return []

    # Partition into parent/child based on 'parent_sku' textual marker (Parent/Child)
    parents = {}
    children_by_parent = {}

    for _, r in df.iterrows():
        parent_sku_value = str(r.get("parent_sku", "")).strip().lower()
        sku = str(r.get("item_sku", "")).strip()
        if not sku:
            continue

        if parent_sku_value == "parent":
            parents[sku] = r
            children_by_parent.setdefault(sku, [])
        elif parent_sku_value == "child":
            # in this file, the actual parent key is stored in 'variation_theme'
            parent_key = str(r.get("variation_theme", "")).strip() or None
            if not parent_key:
                # fallback: group by base SKU without -NN suffix
                m = re.match(r"(.+)-[0-9]{2,3}$", sku)
                parent_key = m.group(1) if m else None
            if parent_key:
                children_by_parent.setdefault(parent_key, []).append(r)
        else:
            # Standalone row w/o explicit parent/child: treat as parent
            parents.setdefault(sku, r)

    docs: List[Dict[str, Any]] = []

    for parent_key, prow in parents.items():
        childs = children_by_parent.get(parent_key, [])

        title = pick_title(prow)
        brand = _first_nonempty(prow.get("brand_name"))
        desc = pick_description(prow)
        bullets = [prow.get(f"bullet_point{i}") for i in range(1, 6)]
        bullets = [str(b).strip() for b in bullets if b and str(b).strip().lower() != "nan"]
        images = collect_images(prow)

        price, sale = pick_price_fields(prow)

        # Build variants
        variants: List[Dict[str, Any]] = []
        option_values = {"ring_size": set(), "metal_type": set(), "karat": set()}

        for crow in childs:
            vsku = str(crow.get("item_sku", "")).strip()
            vprice, vsale = pick_price_fields(crow)
            vopts = parse_variant_options(crow)
            for k, v in vopts.items():
                if k in option_values and v:
                    option_values[k].add(v)
            vdoc = _drop_empty({
                "sku": vsku or None,
                "options": vopts or None,
                "price": vprice,
                "salePrice": vsale,
            })
            if vdoc:
                variants.append(vdoc)

        optionSchema = {k: sorted(list(v)) for k, v in option_values.items() if v}

        # Fallback: if parent price is missing, derive from variants
        if price is None and variants:
            prices = [(vd.get("salePrice") or vd.get("price")) for vd in variants if (vd.get("salePrice") or vd.get("price")) is not None]
            if prices:
                price = min(prices)

        doc = _drop_empty({
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
