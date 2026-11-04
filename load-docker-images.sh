#!/usr/bin/env bash

# TODO version of this with only pre-built images from official sources, to go with docker-compose
# TODO then make it clear this is the dev version

# Pull pinned 3rd party images
for img in cardano ogmios ipfs; do
  nix build .#allDockerImages.${img}.file --out-link result-docker-image-${img}
done

# Build the EGC image locally
# TODO pin a pre-built version for releases?
nix build .#allDockerImages.egc --out-link result-docker-image-egc

# Load everything into Docker
for img in cardano ogmios ipfs egc; do
  docker load < result-docker-image-${img}
done
