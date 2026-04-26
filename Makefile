PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

install:
	$(PIP) install -e .[dev]

test:
	pytest -q

doctor:
	vovan doctor

preflight:
	@if [ -z "$(SAMPLE)" ]; then echo "Usage: make preflight SAMPLE=path"; exit 1; fi
	vovan preflight $(SAMPLE)

ocr:
	@if [ -z "$(SAMPLE)" ]; then echo "Usage: make ocr SAMPLE=path"; exit 1; fi
	vovan ocr $(SAMPLE)

worker:
	vovan worker

docker-build:
	docker compose build vovan-worker

docker-worker:
	docker compose run --rm vovan-worker

smoke:
	$(MAKE) doctor
	$(MAKE) preflight SAMPLE=data/sample.png
	$(MAKE) ocr SAMPLE=data/sample.png
