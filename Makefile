PYTHON ?= python3

.PHONY: test build blackbox whitebox down reset-blackbox reset-whitebox acceptance

test:
	$(PYTHON) -m unittest discover -s tests -v

build:
	docker compose --profile blackbox build
	docker compose --profile whitebox build

blackbox:
	docker compose --profile blackbox up -d --wait

whitebox:
	docker compose --profile whitebox up -d --wait

down:
	docker compose --profile blackbox down --remove-orphans
	docker compose --profile whitebox down --remove-orphans

reset-blackbox:
	./scripts/reset.sh blackbox

reset-whitebox:
	./scripts/reset.sh whitebox

acceptance:
	./scripts/acceptance.sh
