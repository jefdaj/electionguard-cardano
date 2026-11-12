#!/usr/bin/env bash

# Pull pinned 3rd party images
for img in cardano ogmios ipfs mithril; do
  nix build .#allDockerImages.${img}.file --out-link result-docker-image-${img}
done

# Build the EGC image locally
# TODO pin a pre-built version for releases
nix build .#allDockerImages.egc --out-link result-docker-image-egc

# Load everything into Docker
for img in cardano ogmios ipfs mithril egc; do
  docker load < result-docker-image-${img}
done
