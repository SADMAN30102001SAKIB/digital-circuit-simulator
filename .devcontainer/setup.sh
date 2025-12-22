#!/bin/bash
set -e

# Install system dependencies for Qt/PySide6
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
        patchelf \
        ccache \
        libgl1 \
        libegl1 \
        libopengl0 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-keysyms1 \
        libxcb-image0 \
        libxcb-shm0 \
        libxcb-render-util0 \
        libxcb-xkb1 \
        libxkbcommon-x11-0 \
        libxcb-shape0 \
        libxcb-util1 \
        libxcb-xinerama0 \
        libxcb-xinput0

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install project dependencies
uv sync
