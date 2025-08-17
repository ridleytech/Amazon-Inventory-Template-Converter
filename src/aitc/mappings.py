import re

def slug_header(h: str) -> str:
    if h is None:
        return ""
    h = str(h).strip().lower()
    h = re.sub(r"[\s\-]+", "_", h)
    h = re.sub(r"[^a-z0-9_]+", "", h)
    return h

SYN = {
    "sku": {"sku", "seller_sku", "item_sku"},
    "parent_sku": {"parent_sku", "parent", "parentage_sku", "parentsku"},
    "parentage": {"parentage"},
    "variation_theme": {"variation_theme", "variationtheme"},
    "title": {"item_name", "item_title", "title", "itemname"},
    "brand": {"brand_name", "brand"},
    "description": {"product_description", "item_description", "description"},
    "bullet1": {"bullet_point1", "bulletpoint1"},
    "bullet2": {"bullet_point2", "bulletpoint2"},
    "bullet3": {"bullet_point3", "bulletpoint3"},
    "bullet4": {"bullet_point4", "bulletpoint4"},
    "bullet5": {"bullet_point5", "bulletpoint5"},
    "main_image": {"main_image_url", "main_image", "main_image_link"},
    "other_image1": {"other_image_url1"},
    "other_image2": {"other_image_url2"},
    "other_image3": {"other_image_url3"},
    "other_image4": {"other_image_url4"},
    "other_image5": {"other_image_url5"},
    "other_image6": {"other_image_url6"},
    "other_image7": {"other_image_url7"},
    "standard_price": {"standard_price", "price"},
    "sale_price": {"sale_price"},
    "currency": {"currency", "standard_price_currency"},
    "size_name": {"size_name", "size"},
    "metal_type": {"metal_type", "material_type", "metal"},
    "color_name": {"color_name", "color"},
    "metal_stamp": {"metal_stamp", "metal_karat", "karat"},
}

def normalize_option_key(raw_key: str):
    k = raw_key
    if k in ("size_name",):
        return "ring_size"
    if k in ("metal_type", "color_name"):
        return "metal_type"
    if k in ("metal_stamp",):
        return "karat"
    return None

def first_nonempty(*vals):
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s != "" and s.lower() != "nan":
            return s
    return None
