# LXMFy JS8Call Bot

LXMF JS8Call bot that uses the [LXMFy bot framework](https://lxmfy.github.io/LXMFy/). Relays messages from JS8Call over LXMF.

## Features

- Relays messages from JS8Call over LXMF via TCP API for JS8Call.
- Supports multiple users and groups.

## To-Do

- [ ] Supports multiple JS8Call APIs.
- [ ] Bot LXMF icons
- [ ] Guide

## Installation

Create directories for the bot

```bash
mkdir -p yourbotname/config yourbotname/storage yourbotname/.reticulum
```

**Docker/Podman:**

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

**Manual:**

```bash
poetry install
poetry run lxmfy-js8call-bot
```