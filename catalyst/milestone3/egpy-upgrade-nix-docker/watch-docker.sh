#!/usr/bin/env bash
# Docker networks + containers by name.

cmd="docker network ls"
cmd="$cmd; echo"
cmd="$cmd; docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | sort -k 1 -h"
watch -t -n10 "$cmd"
