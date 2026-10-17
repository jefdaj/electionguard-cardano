# Websites/Docs

## electionguard

This is the docs site, also written in Python (Jinja templates). I think it might have the definitive sample data too?

Last commit 2024-08-15 by Jared <jared@turnout.rocks> updating a bunch of things.

No other forks worked on since then.

Latest closed issue is 2024-08-15 and it's a triage by jungshadow updating the docs. Says the data serialization spec currently matche the v2.0 implementation (meaning **not** the one in this repo?) but should be updated to 2.1 soon.

jungshadow also did the latest closed PR the same day.

Previous PRs in late 2023 are data, instructions, etc for multiple test elections so this looks like the version with the most actual use.

## egvote

This is a secondary website specifically about pilot elections?

Last commit 2023-10-30 rc-eti/rc carter <rocarter@microsoft.com> adding Spanish translations.

## website

This is also a website, also written in Python.

Maybe the difference is this one is run by ETI after handing the codebase over to them?

Last commit 2024-05-27 Jared <jared@turnout.rocks> working on misc things.

## ElectionGuard-SDK-Specification

Last commit Ethan Chumley 2019-10-03 on README.

FreeAndFair forked it in early 2023 but didn't change anything?

Latest open issue is 2021-01-23.


# Python 1.X Reference Implementation

## electionguard-python

This is the main source code of the python version, and probably what I want to use.

Current version is 1.4.0? The tag is only a couple commits behind main though, and those commits look useful. Can probably develop on main.

It also includes a python verifier implementation! Which is probably closely tied to the rest of the code.

TODO Consider using it instead of the Rust one.

It looks like the top level install and build things are done via Makefile, which calls poetry for the Python parts and has separate install functions for system libraries on Mac or Linux. The Mac ones use brew and the Linux ones use apt-get.

Sounds like it **could** be modified to work with Nix, but the simpler way would be to run it in a Docker image. Some of the Makefile commands also run docker or docker-compose directly. For example the MongoDB parts.

There's one .ipynb file but then they switched to markdown.

TODO: is the simplest/best dev setup going to be to use exising Docker images + generate your own new ones in Nix? Maybe check if they work fine podman or another open source alternative. Weirdly I don't see a top-level electionguard-python Dockerfile, only the API one. So I'll need to create that from a Debian/Ubuntu base image?

TODO check out how their github CI works. Does it use a Debian base image? Close: ubuntu-latest + macos-lastest.

TODO Consider whether the API is superior in most cases anyway? Maybe you should make a version of that Docker image with live code reloading?

Last commit John Morgan 2022-10-28 fix docker build.

Two forks worked on since then: pievalentin and jamestiotio.

grepping for `spec_version` reveals some 1.0 files and some 0.95 files.

TODO what are the differences?

## electionguard-api-python

This is a fastapi wrapper around electionguard-python. It installs it from poetry + pip rather than source code. There's also a Dockerfile and a docker-compose that runs one guardian + one mediator using the dockerfile. Also a "dev" dockerfile that adds some MongoDB and message-queue things I don't understand yet, and an Azure one that presumably is used to deploy the actual website?

README is good and includes instructions for developing in different environments (Docker, Windows, Mac/Linux)

Last commit 2023-08-02 John Morgan fixing a crypto thing.

john-s-morgan fork has other work around the same time.

# C#/C++ 2.X Production Implementation

## electionguard-core2
This is the new implementation, but it says it's pre-release software and not yet feature complete. You probably don't need to bother with it at all for now! Except to see where they're heading these days.

Last human commit John Morgan + SteveMaier-IRT 2024-01-30 on dev container
john-s-morgan, sarvex forks have some 2024 activity but most forks/branches are dependabot

## electionguard-cpp

Same pre-release, not feature complete warning, but also hasn't been updated for 3 years. Probably an early version of the core2? Looks that way from the top level code organization. Ignore for now.

Last commit John Morgan 2023-01-03 fix make environment
No major-looking current forks
