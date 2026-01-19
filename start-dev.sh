#!/usr/bin/env bash

set -e

trap "trap - SIGINT SIGTERM EXIT; kill -- -$$" SIGINT SIGTERM EXIT

(
  cd frontend
  npm run dev
) &

(
  cd backend
  uv sync && uv run python -m app.main
) &

wait

