import argparse, json, sys
from .converter import convert

def main(argv=None):
    p = argparse.ArgumentParser(prog="aitc", description="Amazon Inventory Template Converter (Template sheet only)")
    p.add_argument("excel", help="Path to .xlsx/.xlsm file (must contain a sheet named 'Template')")
    p.add_argument("-o", "--out", help="Output JSON file (default: stdout)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = p.parse_args(argv)

    docs = convert(args.excel)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2 if args.pretty else None)
        print(f"Wrote {len(docs)} document(s) -> {args.out}")
    else:
        json.dump(docs, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
        print()

if __name__ == "__main__":
    raise SystemExit(main())
