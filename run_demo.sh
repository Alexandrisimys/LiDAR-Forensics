#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_EXE:-python3}"
mkdir -p .tmp .pip-cache .pycache
export TMPDIR="$PWD/.tmp"
export PIP_CACHE_DIR="$PWD/.pip-cache"
export PYTHONPYCACHEPREFIX="$PWD/.pycache"

if [ ! -x ".venv/bin/python" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

. .venv/bin/activate
python -m pip install --disable-pip-version-check -e '.[dev]'
python -m lidar_forensics.synthetic
echo "LiDAR Forensics is starting at http://127.0.0.1:8765"
python -m uvicorn lidar_forensics.app:app --host 127.0.0.1 --port 8765
