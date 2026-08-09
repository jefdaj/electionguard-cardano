#!/bin/sh
set -eu

# Keep DHT so content is still findable, but as client only
ipfs config Routing.Type dhtclient

# Don't be a general IPFS gateway for finding everyones' content.
# Only serve the election data.
ipfs config --json Gateway.NoFetch true

# Announce only roots ("pinned" strategy or "roots"), and less often.
# TODO does this matter in our case?
# TODO add_json also pins, right?
ipfs config Provide.Strategy pinned

# HARD caps on total connections — this is the real lever
# Specific caps are set by bind mounting ipfs-caps.json
ipfs config --json Swarm.ResourceMgr.Enabled true

# Much tighter connection budget
# Note that these must be lower than the hard caps above.
ipfs config --json Swarm.ConnMgr.LowWater 15
ipfs config --json Swarm.ConnMgr.HighWater 30
ipfs config Swarm.ConnMgr.GracePeriod 5s

# Kill relay serving (you don't need to relay others' traffic)
ipfs config --json Swarm.RelayService.Enabled false
ipfs config --json Swarm.Transports.Network.Relay true # required for next one
ipfs config --json Swarm.RelayClient.Enabled true      # keep so YOU stay reachable

# Reduce NAT probing chatter
# ipfs config AutoNAT.ServiceMode disabled
ipfs config AutoNAT.ServiceMode enabled # TODO does this help?

# Local mDNS off (irrelevant over internet, saves noise)
# ipfs config --json Discovery.MDNS.Enabled false
ipfs config --json Discovery.MDNS.Enabled true # TODO does this help?

# Cap resource-manager scaling explicitly. The RM auto-scales to your RAM, which on a big host = huge limits. Pin them:
# (Claude recommended 512)
# ipfs config --json Swarm.ResourceMgr.MaxMemory '"128MB"'
# ipfs config --json Swarm.ResourceMgr.MaxFileDescriptors 128

# Disable the accelerated DHT client if it got enabled — it does bulk network sweeps:
ipfs config --json Routing.AcceleratedDHTClient false

# Stop advertising a relay & stop NAT port mapping storms
# ipfs config --json Swarm.RelayService.Enabled false
# ipfs config --json Swarm.DisableNatPortMap true
ipfs config --json Swarm.RelayService.Enabled true # TODO does this help?
ipfs config --json Swarm.DisableNatPortMap false # TODO does this help?

# QUIC opens lots of UDP flows -> conntrack blowup on cheap routers.
# Test with TCP only to confirm that's the cause:
ipfs config --json Swarm.Transports.Network.QUIC false
# ipfs config --json Swarm.Transports.Network.Relay false
