#!/usr/bin/env sh
# Install project requirements using uv.
# Additional arguments are passed directly to 'uv pip install'.
# Example:
#   ./scripts/install_with_uv.sh             # install from requirements.txt
#   ./scripts/install_with_uv.sh -e .[dev]   # editable install with dev extras
set -e
uv pip install -r requirements.txt "$@"
