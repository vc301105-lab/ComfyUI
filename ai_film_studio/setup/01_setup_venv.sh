#!/usr/bin/env bash
# ============================================================
# AI Film Studio — Phase 1a: Python venv + ComfyUI dependencies
# CUDA 12.8 torch wheels install karta hai, phir requirements.txt
# Run: bash ai_film_studio/setup/01_setup_venv.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."   # ComfyUI root

say() { printf '\033[1;34m[..]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }

VENV=".venv"
PYTHON=${PYTHON:-python3}

if [ ! -d "$VENV" ]; then
  say "Creating venv: $VENV"
  "$PYTHON" -m venv "$VENV"
else
  say "Venv already exists: $VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel
ok "pip: $(pip --version)"

say "Installing PyTorch (CUDA 12.8 wheels — 48GB+ NVIDIA GPU ke liye)"
# Agar aapke CUDA driver 12.x se purana hai (11.8), toh cu121 ya cu118 index use karein.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
ok "torch: $(python -c 'import torch;print(torch.__version__)')"

say "Installing ComfyUI requirements.txt"
pip install -r requirements.txt

say "Installing helpers: huggingface_hub CLI"
pip install -U "huggingface_hub[cli]"
ok "huggingface-cli: $(command -v huggingface-cli)"

python - <<'PY'
import torch
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device:", torch.cuda.get_device_name(0))
    print("VRAM GB:", round(torch.cuda.get_device_properties(0).total_memory/1024**3,1))
PY

ok "Done! Next: bash ai_film_studio/setup/02_install_custom_nodes.sh"
