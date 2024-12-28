# LXMFy JS8Call Bot

LXMF JS8Call bot that uses the [LXMFy bot framework](https://lxmfy.github.io/LXMFy/).

## Installation

**Docker:**

```bash
docker run -d \
    --name lxmfy-js8call-bot \
    --network host \
    -v $(pwd)/testbot/config:/bot/config \
    -v $(pwd)/testbot/.reticulum:/root/.reticulum \
    -v $(pwd)/testbot/storage:/bot/storage \
    --restart unless-stopped \
    ghcr.io/lxmfy/lxmfy-js8call-bot:latest
```

**Podman:**

```bash
podman run -d \
    --name lxmfy-js8call-bot \
    --network host \
    -v $(pwd)/testbot/config:/bot/config \
    -v $(pwd)/testbot/.reticulum:/root/.reticulum \
    -v $(pwd)/testbot/storage:/bot/storage \
    --restart unless-stopped \
    ghcr.io/lxmfy/lxmfy-js8call-bot:latest
```

**Manual:**

```bash
poetry install
poetry run lxmfy-js8call-bot
```

## Configuration

The bot uses a configuration file located at `config/lxmfy_js8call_bot.ini`. You can use example-config.ini as a template.

## Development

```bash
poetry install
poetry run lxmfy-js8call-bot
```

## Docker

```bash
docker build -t lxmfy-js8call-bot .


docker run -d \
    --name lxmfy-js8call-bot \
    --network host \
    -v $(pwd)/testbot/config:/bot/config \
    -v $(pwd)/testbot/.reticulum:/root/.reticulum \
    -v $(pwd)/testbot/storage:/bot/storage \
    --restart unless-stopped \
    lxmfy-js8call-bot
```

## Podman

```bash
podman run -d \
    --name lxmfy-js8call-bot \
    --network host \
    -v $(pwd)/testbot/config:/bot/config \
    -v $(pwd)/testbot/.reticulum:/root/.reticulum \
    -v $(pwd)/testbot/storage:/bot/storage \
    --restart unless-stopped \
    lxmfy-js8call-bot
```
