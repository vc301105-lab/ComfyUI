#!/usr/bin/env bash
# ============================================================
# AI Film Studio — Phase 1c: Verify setup
# ComfyUI locally start karta hai (bina model ke bhi chalega),
# log me node load errors dhokta hai.
# Run: bash ai_film_studio/setup/03_verify_setup.sh
# ============================================================
set -uo pipefail
cd "$(dirname "$0")/../.."   # ComfyUI root

say() { printf '\033[1;34m[..]\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
er()  { printf '\033[1;31m[XX]\033[0m %s\n' "$*"; }

[ -d ".venv" ] || { er ".venv missing — pehle 01_setup_venv.sh chalayein"; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate

say "ComfyUI version: $(python -c 'import comfyui_version; print(comfyui_version.__version__)')"
say "Checks: torch cuda + custom nodes folders"
python - <<'PY'
import torch, os, importlib.util
print("torch:", torch.__version__, "| cuda:", torch.cuda.is_available())
nodes = [d for d in os.listdir("custom_nodes") if os.path.isdir(os.path.join("custom_nodes", d))]
print("custom node folders:", len(nodes))
for n in sorted(nodes):
    print("  -", n)
PY

say "ComfyUI 60 sec ke liye start karke log check (Ctrl+C nahi, auto kill) ..."
LOG=$(mktemp)
timeout 60 python main.py --listen 127.0.0.1 --port 8188 >"$LOG" 2>&1 &
PID=$!
sleep 20
if kill -0 $PID 2>/dev/null; then ok "ComfyUI process alive (server starting...)"; else er "ComfyUI crash ho gaya — log dekhein:"; tail -40 "$LOG"; rm -f "$LOG"; exit 1; fi
sleep 15
kill $PID 2>/dev/null; wait $PID 2>/dev/null

if grep -qiE "error|traceback" "$LOG"; then
  er "Log me errors mili:"
  grep -iE "error|traceback" "$LOG" | head -20
else
  ok "No fatal errors in log"
fi
grep -E "To see the GUI go to|Starting server" "$LOG" | head -3
rm -f "$LOG"
ok "Verify complete. Ab models download karein: cat ai_film_studio/docs/model-downloads.md"
