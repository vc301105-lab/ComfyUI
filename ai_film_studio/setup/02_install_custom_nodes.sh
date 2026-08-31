#!/usr/bin/env bash
# ============================================================
# AI Film Studio — Phase 1b: Custom Nodes install
# CORE = video production ke liye zaroori
# OPT = character consistency / upscale / extra
# Run: bash ai_film_studio/setup/02_install_custom_nodes.sh
#      bash ai_film_studio/setup/02_install_custom_nodes.sh --optional
# ============================================================
set -uo pipefail
cd "$(dirname "$0")/../.."   # ComfyUI root

say() { printf '\033[1;34m[..]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
er()  { printf '\033[1;31m[XX]\033[0m %s\n' "$*"; }

CUSTOM_NODES="custom_nodes"
mkdir -p "$CUSTOM_NODES"

CORE=(
  "ltdrdata/ComfyUI-Manager"
  "Kosinkadink/ComfyUI-VideoHelperSuite"
  "Kosinkadink/ComfyUI-AnimateDiff-Evolved"
  "Kosinkadink/ComfyUI-Advanced-ControlNet"
  "kijai/ComfyUI-WanVideoWrapper"
  "Lightricks/ComfyUI-LTXVideo"
  "Fannovel16/ComfyUI-Frame-Interpolation"
  "kijai/ComfyUI-KJNodes"
  "pythongosssss/ComfyUI-Custom-Scripts"
  "ltdrdata/ComfyUI-Impact-Pack"
  "ltdrdata/ComfyUI-Inspire-Pack"
  "city96/ComfyUI-GGUF"
)

OPTIONAL=(
  "cubiq/ComfyUI_IPAdapter_plus"
  "cubiq/ComfyUI-InstantID"
  "cubiq/ComfyUI-PuLID"
  "cubiq/ComfyUI_essentials"
  "Fannovel16/comfyui_controlnet_aux"
  "kijai/ComfyUI-SUPIR"
)

install_nodes() {
  local label="$1"; shift
  say "--- $label ($# nodes) ---"
  for repo in "$@"; do
    local name
    name=$(basename "$repo")
    if [ -d "$CUSTOM_NODES/$name" ]; then
      ok "$name: already installed"
      continue
    fi
    say "cloning $repo"
    if git clone --depth 1 "https://github.com/$repo.git" "$CUSTOM_NODES/$name" 2>&1 | tail -2; then
      ok "$name: cloned"
    else
      er "$name: clone FAILED (network? repo naam?)"
      continue
    fi
    # node-specific requirements (agar hai)
    if [ -f "$CUSTOM_NODES/$name/requirements.txt" ]; then
      say "$name: installing requirements.txt"
      if [ -x "$VENV/bin/python" ]; then pip_="$VENV/bin/pip"; else pip_="pip"; fi
      # shellcheck disable=SC1091
      [ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"
      "$pip_" install -r "$CUSTOM_NODES/$name/requirements.txt" || er "$name: deps me dikkat (manual dekhein)"
    fi
  done
}

install_nodes "CORE VIDEO NODES" "${CORE[@]}"

if [ "${1:-}" = "--optional" ] || [ "${1:-}" = "--all" ]; then
  install_nodes "OPTIONAL NODES" "${OPTIONAL[@]}"
else
  say "Optional nodes skip (IP-Adapter/InstantID/SUPIR). Chalane ke liye: --optional"
fi

say "Custom nodes total: $(ls "$CUSTOM_NODES" | grep -v '\.py' | wc -l)"
ok "Done! Next: bash ai_film_studio/setup/03_verify_setup.sh"
