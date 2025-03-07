dev:
	uv run -- python3 manage.py runserver

lint:
	uv run ruff check && uv run isort honduras_shop_aggregator/

install:
	uv install

installrender:
	pip install -r requirements.txt

makemigrations:
	uv run python3 manage.py makemigrations

migrate:
	uv run python3 manage.py migrate

PORT ?= 8000
start:
	uv run gunicorn honduras_shop_aggregator.wsgi:application --bind 0.0.0.0:$(PORT)
