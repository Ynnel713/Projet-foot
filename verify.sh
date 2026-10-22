#!/usr/bin/env bash
set -u
PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider
