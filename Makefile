.PHONY: docker-build docker-run

docker-build:
	docker build -t aitc:latest .

# Run CLI in container; mount local examples as /work
docker-run:
	docker run --rm -it -v "$$(pwd)/examples":/work -w /work aitc:latest --help
