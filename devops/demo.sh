#!/usr/bin/env bash

export EGC_CARDANO_TOPOLOGY=/etc/cardano/toplogy.json
docker compose up $@
