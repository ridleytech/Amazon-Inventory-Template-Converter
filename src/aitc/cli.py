import argparse, json, sys
from .converter import convert

def main(argv=None):
    p = argparse.ArgumentParser(prog="aitc", description="Amazon Inventory Template Converter")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="Convert an Excel template to Mongo-friendly JSON")
    c.add_argument("excel", help="Path to .xlsx/.xlsm file")
    c.add_argument("-o", "--out", help="Output JSON file (default: stdout)")
    c.add_argument("--sheet", help="Sheet name to read (default: auto-pick first non-empty)")
    c.add_argument("--infer-single", action="store_true", help="If no parentage, treat each row as a single-product parent with itself as a variant")
    c.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = p.parse_args(argv)

    if args.cmd == "convert":
        docs = convert(args.excel, sheet=args.sheet, infer_single=args.infer_single)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(docs, f, ensure_ascii=False, indent=2 if args.pretty else None)
            print(f"Wrote {len(docs)} document(s) -> {args.out}")
        else:
            json.dump(docs, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
            print()
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main())
