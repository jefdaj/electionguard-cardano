#!/bin/sh
set -eu

# Keep DHT so content is still findable, but as client only
ipfs config Routing.Type dhtclient

# Much tighter connection budget
# (Claude recommended 8 and 20)
ipfs config --json Swarm.ConnMgr.LowWater 2
ipfs config --json Swarm.ConnMgr.HighWater 3
ipfs config Swarm.ConnMgr.GracePeriod 20s

# HARD caps on total connections — this is the real lever
ipfs config --json Swarm.ResourceMgr.Enabled true
# ipfs config --json Swarm.ResourceMgr.Limits.System.ConnsInbound 32
# ipfs config --json Swarm.ResourceMgr.Limits.System.ConnsOutbound 64
# ipfs config --json Swarm.ResourceMgr.Limits.System.Conns 96
# ipfs config --json Swarm.ResourceMgr.Limits.System.FD 256

# Reprovider = periodic DHT re-announce of ALL local blocks. Huge upload cost.
# Announce only roots ("pinned" strategy or "roots"), and less often.
ipfs config Provide.Strategy pinned

# Should probably be below 24h to ensure content isn't dropped from DHT?
ipfs config Provide.DHT.Interval 12h # 0 disables entirely
# ipfs config --json Provide.Enabled false

# Resource manager hard caps
ipfs config --json Swarm.ResourceMgr.Enabled true

# Kill relay serving (you don't need to relay others' traffic)
ipfs config --json Swarm.RelayService.Enabled false
ipfs config --json Swarm.Transports.Network.Relay true # required for next one
ipfs config --json Swarm.RelayClient.Enabled true   # keep so YOU stay reachable

# Reduce NAT probing chatter
# ipfs config AutoNAT.ServiceMode disabled

# Local mDNS off (irrelevant over internet, saves noise)
# ipfs config --json Discovery.MDNS.Enabled false

# Cap resource-manager scaling explicitly. The RM auto-scales to your RAM, which on a big host = huge limits. Pin them:
# (Claude recommended 512)
ipfs config --json Swarm.ResourceMgr.MaxMemory '"128MB"'
ipfs config --json Swarm.ResourceMgr.MaxFileDescriptors 128

# Disable the accelerated DHT client if it got enabled — it does bulk network sweeps:
ipfs config --json Routing.AcceleratedDHTClient false

# Stop advertising a relay & stop NAT port mapping storms
ipfs config --json Swarm.RelayService.Enabled false
ipfs config --json Swarm.DisableNatPortMap true

# QUIC opens lots of UDP flows -> conntrack blowup on cheap routers.
# Test with TCP only to confirm that's the cause:
ipfs config --json Swarm.Transports.Network.QUIC false
# ipfs config --json Swarm.Transports.Network.Relay false
