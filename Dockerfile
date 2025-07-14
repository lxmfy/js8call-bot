ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /bot

RUN mkdir -p /root/.reticulum /bot/config /bot/storage

RUN pip install poetry

RUN echo "# LXMFy JS8Call Bot" > README.md

COPY pyproject.toml .

RUN poetry lock

COPY lxmfy_js8call_bot ./lxmfy_js8call_bot/

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi \
    && pip install -e .

VOLUME ["/bot/config", "/root/.reticulum", "/bot/storage"]

CMD ["python3", "-m", "lxmfy_js8call_bot.bot"] 