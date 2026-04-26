PYTHON ?= python3
PIP ?= pip3
SAMPLE ?= ./data/sample.txt

.PHONY: install test doctor preflight ocr worker docker-build docker-worker smoke

install:
	$(PIP) install -e .[dev]

test:
	pytest -q

doctor:
	vovan doctor

preflight:
	vovan preflight $(SAMPLE)

ocr:
	vovan ocr $(SAMPLE)

worker:
	vovan worker

docker-build:
	docker compose build vovan-worker

docker-worker:
	docker compose up --build vovan-worker

smoke:
	vovan doctor && vovan preflight $(SAMPLE) && vovan ocr $(SAMPLE)
