#!/usr/bin/env bash

# TODO convert to docker-compose and/or arion

api_port=1442

# chosen from the top of the cardanoscan tokens list
asset_policy_id=7c833f1eb9b70c2e700d028e0ee28d421edad2af4222061be525382d

cd ..

# add this when first scanning the chain, if it'll be a big one:
# --defer-db-indexes \

docker run \
	-p "${api_port}:${api_port}" \
	-v ./cardano-node-ogmios/config/network/preview/cardano-node:/node-config \
	-v ./cardano-node-ogmios/data/node-ipc:/node-ipc \
	-v ./kupo/data/kupo-db:/kupo-db 84db4ae204e4 \
	--node-socket /node-ipc/node.socket \
	--node-config /node-config/config.json \
	--since origin \
	--workdir /kupo-db \
	--host 0.0.0.0 \
	--port ${api_port} \
	--match "${asset_policy_id}.*"
