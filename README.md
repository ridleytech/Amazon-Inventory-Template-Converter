# Amazon Inventory Template Converter

<p align="center">
  <a href="https://github.com/ridleytech/Amazon-Inventory-Template-Converter/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/ridleytech/Amazon-Inventory-Template-Converter/ci.yml?branch=main" alt="CI">
  </a>
  <a href="https://pypi.org/project/amazon-inventory-template-converter/">
    <img src="https://img.shields.io/pypi/v/amazon-inventory-template-converter.svg" alt="PyPI">
  </a>
  <a href="https://github.com/ridleytech/Amazon-Inventory-Template-Converter/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
</p>

Convert Amazon Seller Central inventory Excel templates (`.xlsx`/`.xlsm`) into **MongoDB-friendly JSON** with a single parent product document containing normalized **variants** and an **optionSchema**.

- **Name:** Amazon Inventory Template Converter
- **CLI:** `aitc`
- **Output:** JSON that fits a collection like `rings` in your into your MongoDB database

## Install

```bash
# from source
pip install -e .
# or build & install
pip install build
python -m build
pip install dist/*.whl
```

Python 3.9+ recommended.

## Quick Start

```bash
aitc convert examples/sample-amazon-template.xlsx -o out.json
# or explicitly choose sheet:
aitc convert examples/sample-amazon-template.xlsx -o out.json --sheet "Template"
```

Reads your Amazon sheet and writes **parent + variants** JSON with an `optionSchema`.

## CLI Usage

```bash
aitc convert <excel-file> [--sheet SHEETNAME] -o <output.json> \
  [--collection rings] [--infer-single] [--pretty]
```

## Docker

Build and run the CLI in a container:

```bash
docker build -t aitc:latest .
docker run --rm -it -v "$PWD/examples":/work aitc:latest --help
# Convert a file within /work
docker run --rm -it -v "$PWD/examples":/work -w /work aitc:latest convert sample-amazon-template.xlsx -o out.json --pretty
```

## Contributing

- Install dev tools: `pip install -r requirements-dev.txt`
- Run checks: `make lint && make test`
- Format: `make format`
- Enable **pre-commit** hooks:
  ```bash
  pre-commit install
  ```
- Open a PR — CI runs lint, tests, and build.
