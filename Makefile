.PHONY: venv install test lint format build clean docker-build docker-run

venv:
	python -m venv .venv

install:
	pip install -U pip
	pip install -e .
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check .
	black --check .

format:
	black .
	ruff check --fix .

build:
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache

docker-build:
	docker build -t aitc:latest .

docker-run:
	docker run --rm -it -v $$PWD/examples:/work aitc:latest --help
