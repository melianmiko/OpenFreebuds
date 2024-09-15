#!/usr/bin/env bash

cd "$(dirname "$0")"
./bump_version.sh "0.99.git.$(git rev-parse HEAD)"
