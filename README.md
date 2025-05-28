# LXMFy JS8Call Bot

LXMF JS8Call bot that uses the [LXMFy bot framework](https://lxmfy.github.io/LXMFy/). Relays messages from JS8Call over LXMF.

## Installation

Create directories for the bot

```bash
mkdir -p yourbotname/config yourbotname/storage yourbotname/.reticulum
```

**Docker:**

```bash
docker run -d \
    --name lxmfy-js8call-bot \
    --network host \
    -v $(pwd)/yourbotname/config:/bot/config \
    -v $(pwd)/yourbotname/.reticulum:/root/.reticulum \
    -v $(pwd)/yourbotname/storage:/bot/storage \
    --restart unless-stopped \
    ghcr.io/lxmfy/lxmfy-js8call-bot:latest
```

**Manual:**

```bash
poetry install
poetry run lxmfy-js8call-bot
```

## Development

```bash
poetry install
poetry run lxmfy-js8call-bot
```