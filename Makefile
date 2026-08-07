# Dev tasks. The toolkit itself is zero-dependency; ruff is dev-only tooling.
#
# `make ci` runs exactly what .github/workflows/ci.yml runs and is the
# pre-push gate. It does NOT need to clone or sandbox anything: the suite
# points IH_DATA_DIR at an empty temp tree (tests/__init__.py), so it already
# sees what a fresh clone sees. That indirection is the reason this target can
# be three ordinary commands instead of a scratch-clone script.

.PHONY: ci lint test import-check advise

ci: lint test import-check
	@echo "PASSED — matches .github/workflows/ci.yml"

lint:
	ruff check scripts tests

test:
	python3 -m unittest discover tests -q

# The library must import cleanly with no data tree at all, as on a fresh
# clone where data/ is git-ignored.
import-check:
	@IH_DATA_DIR=$$(mktemp -d) python3 -c "import sys; sys.path.insert(0, 'scripts'); import ihlib, experiments" \
		&& echo "import-check OK"

# Convenience: the standing progression advisory digest.
advise:
	python3 scripts/ih.py brief
