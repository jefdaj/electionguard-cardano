#!/usr/bin/env bash
# Docker networks + containers by name.

cmd="echo 'networks:'; docker network ls | grep -v NAME"
cmd="$cmd; echo; echo 'containers:'"
cmd="$cmd; docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep -v NAME | sort -k 1 -h"
watch -t -n5 "$cmd"
