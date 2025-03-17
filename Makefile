dev:
	uv run -- python3 manage.py runserver

lint:
	uv run ruff check && uv run isort honduras_shop_aggregator/

install:
	uv install

makemigrations:
	uv run python3 manage.py makemigrations

migrate:
	uv run python3 manage.py migrate

makemessages:
	uv run python3 manage.py makemessages -l es

compilemessages:
	uv run python3 manage.py compilemessages

renderinstalluv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

PORT ?= 8000
UVPATH ?= /opt/render/.local/bin/uv
renderstart:
	$(UVPATH) run python3 manage.py migrate && \
	$(UVPATH) run python3 manage.py collectstatic && \
	$(UVPATH) run gunicorn honduras_shop_aggregator.wsgi:application \
	--bind 0.0.0.0:$(PORT)