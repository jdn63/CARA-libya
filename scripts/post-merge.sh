#!/bin/bash
set -e

# Post-merge setup for Libya CARA
# Runs automatically after any task agent merge.
# Must be idempotent and non-interactive.

echo "=== Libya CARA post-merge setup ==="

# Install / sync Python dependencies using pip into the Replit pythonlibs path.
# uv sync is intentionally NOT used here — the Nix store is read-only in this
# environment and uv cannot install packages there.
if [ -f "CARA_requirements.txt" ]; then
    echo "Installing from CARA_requirements.txt..."
    pip install -q --no-input -r CARA_requirements.txt
elif [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -q --no-input -r requirements.txt
else
    echo "No requirements file found — skipping pip install."
fi

echo "=== Post-merge setup complete ==="
