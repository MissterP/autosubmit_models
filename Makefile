.PHONY: test lint format security coverage clean check setup docker-test help

# Variables
PYTHON = python3
TEST_PATH = tests/
SRC_PATH = src/

# Help command
help:
	@echo "Commands available:"
	@echo "  test        : Run tests using the script (includes Docker)"
	@echo "  format      : Format code using black and isort"
	@echo "  lint        : Check code style and quality"
	@echo "  security    : Run security checks"
	@echo "  clean       : Remove generated files"
	@echo "  check       : Run lint, tests, and security checks"
	@echo "  setup       : Install dependencies"

# Test commands - all test operations use run_tests.sh
test:
	$(MAKE) clean
	./scripts/run_tests.sh

test-with-args:
	$(MAKE) clean
	./scripts/run_tests.sh $(ARGS)

# Format code
format:
	black $(SRC_PATH) $(TEST_PATH)
	isort $(SRC_PATH) $(TEST_PATH)

# Lint commands
lint:
	black --check $(SRC_PATH) $(TEST_PATH)
	isort --check $(SRC_PATH) $(TEST_PATH)
	flake8 $(SRC_PATH) $(TEST_PATH) --output-file=lint-report.txt
	@echo "Lint report generated in lint-report.txt"
	@if [ -s lint-report.txt ]; then \
		echo "Linting issues found:"; \
		cat lint-report.txt; \
	else \
		echo "No linting issues found."; \
	fi

# Security checks
security:
	bandit -r $(SRC_PATH) -f json -o bandit-report.json
	-safety scan > safety-report.txt
	@echo "Security analysis completed."

# Run all checks
check: clean lint test security

# Clean generated files
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf coverage.xml
	rm -rf flake-report
	rm -rf bandit-report.json
	rm -rf lint-report.txt
	rm -rf safety-report.txt
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Setup environment
setup:
	$(PYTHON) -m pip install -r requirements.txt