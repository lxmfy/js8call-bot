# LXMFy JS8Call Bot

[![DeepSource](https://app.deepsource.com/gh/lxmfy/js8call-bot.svg/?label=active+issues&show_trend=true&token=wJqFJxNQ5HrruY2vjJ4q8IEM)](https://app.deepsource.com/gh/lxmfy/js8call-bot/)
[![Build Test](https://github.com/lxmfy/js8call-bot/actions/workflows/build-test.yml/badge.svg)](https://github.com/lxmfy/js8call-bot/actions/workflows/build-test.yml)
[![Docker Build and Publish](https://github.com/lxmfy/js8call-bot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/lxmfy/js8call-bot/actions/workflows/docker-publish.yml)

LXMF JS8Call bot that uses the [LXMFy bot framework](https://lxmfy.github.io/LXMFy/). Relays messages from JS8Call over LXMF.

## Features

- Relays messages from JS8Call over LXMF via TCP API for JS8Call.
- Supports multiple users and groups.

## To-Do

- [ ] Supports multiple JS8Call APIs.
- [ ] Bot LXMF icons

## Installation

Make sure JS8Call is running and API enabled.

```
pipx install lxmfy-js8call-bot
lxmfy-js8call-bot
```

### Docker/Podman:

Create directories for the bot

```bash
mkdir -p yourbotname/config yourbotname/storage yourbotname/.reticulum
```

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

Remove `--network host` for no auto-interface and want to keep things isolated.

### Running with Poetry:

```bash
poetry install
poetry run lxmfy-js8call-bot
```

### Building:

```bash
poetry install
poetry build
```