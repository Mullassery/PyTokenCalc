.PHONY: install dev test lint fmt fmt-check clean setup-hooks help

help:
	@echo "PyTokenCalc development tasks (pure Python):"
	@echo "  make install         Install package + dev/tokenizers extras"
	@echo "  make dev             Editable install + pre-commit hooks"
	@echo "  make test            Run the pytest suite with coverage"
	@echo "  make lint            black --check + ruff check + mypy"
	@echo "  make fmt             Auto-format with black + ruff --fix"
	@echo "  make fmt-check       Check formatting without modifying files"
	@echo "  make clean           Remove build/test artifacts"

install:
	pip install -e ".[dev,tokenizers]"

dev: install setup-hooks

setup-hooks:
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	pre-commit install

test:
	pytest tests/ -v --cov=pytokencalc --cov-report=term-missing

lint:
	black --check pytokencalc/ tests/
	ruff check pytokencalc/ tests/
	mypy pytokencalc/ --ignore-missing-imports

fmt:
	black pytokencalc/ tests/
	ruff check pytokencalc/ tests/ --fix

fmt-check:
	black --check pytokencalc/ tests/

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
