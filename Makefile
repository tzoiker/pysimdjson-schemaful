PROJECT_NAME := simdjson_schemaful
PROJECT_PATH := $(PROJECT_PATH)
PYTHON_IMAGE := docker.io/snakepacker/python:all

all:
	@echo "make clean              - Clean some generated files"
	@echo "make purge              - Remove virtual env"
	@echo "make develop            - Create virtual env"
	@echo "make pre-commit         - Install pre-commit hooks"
	@echo "make pre-commit-remove  - Remove pre-commit hooks"
	@echo "make lint               - Run linters"
	@echo "make format             - Format code"
	@echo "make test               - Run tests"
	@echo "make test-tox           - Run tests with tox"
	@echo "make test-docker-linux  - Run tests with linux docker image"
	@echo "make build              - Build wheel"
	@echo "make publish            - Publish wheel to PyPI"
	@exit 0

clean:
	rm -fr *.egg-info .tox dist
	find . -iname '*.pyc' -delete

purge: clean
	rm -rf ./.venv

develop: clean
	poetry install
	poetry run pre-commit install

pre-commit:
	poetry run pre-commit install

pre-commit-remove:
	poetry run pre-commit uninstall

mypy:
	poetry run mypy $(PROJECT_PATH)

ruff:
	poetry run ruff $(PROJECT_PATH) tests

lint: mypy ruff

format:
	poetry run ruff $(PROJECT_PATH) tests --fix-only
	poetry run black $(PROJECT_PATH) tests
	poetry run ruff $(PROJECT_PATH) tests

test:
	poetry run pytest tests

test-tox:
	tox -r

test-docker-linux:
	docker run --rm -v $(shell pwd):/mnt -w /mnt --name=$(PROJECT_NAME)_test $(PYTHON_IMAGE) tox

build:
	poetry build

publish: build
	poetry publish
