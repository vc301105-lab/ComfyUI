#!/usr/bin/env bash
# ============================================================
# AI Film Studio — Phase 0: Hardware & Tooling Check
# Kuch bhi install nahi karta. Sirf report deta hai.
# Run: bash ai_film_studio/setup/00_hardware_check.sh
# ============================================================
set -uo pipefail

PASS=0; WARN=0; FAIL=0
say()  { printf '\033[1;34m[..]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; PASS=$((PASS+1)); }
warn() { printf '\033[1;33m[!!]\033[0m %s\n' "$*"; WARN=$((WARN+1)); }
bad()  { printf '\033[1;31m[XX]\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }

echo "============================================================"
echo " AI FILM STUDIO — HARDWARE CHECK ($(date))"
echo "============================================================"

say "1) NVIDIA GPU + VRAM"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
  TOTAL_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
  if [ "${TOTAL_VRAM:-0}" -ge 45000 ]; then ok "VRAM detected: ${TOTAL_VRAM} MB (48GB+ tier — pro stack ready)"
  elif [ "${TOTAL_VRAM:-0}" -ge 22000 ]; then ok "VRAM: ${TOTAL_VRAM} MB (good tier — Wan/LTX ok, HunyuanImage-3.0 limit)"
  else warn "VRAM: ${TOTAL_VRAM} MB (12-16GB tier — quantized models / shorts only)"
  fi
else
  bad "nvidia-smi not found — no NVIDIA GPU / driver missing. Install CUDA driver first."
fi

say "2) CUDA capability"
if command -v nvcc >/dev/null 2>&1; then ok "nvcc: $(nvcc --version | tail -1)"
else warn "nvcc not on PATH (torch CUDA wheels still work without it)"
fi

say "3) CPU / RAM"
NPROC=$(nproc); RAM_GB=$(free -g | awk '/Mem:/{print $2}')
echo "  CPUs: $NPROC   RAM: ${RAM_GB}GB"
[ "$NPROC" -ge 8 ] && ok "CPU cores >= 8" || warn "Only $NPROC cores"
[ "$RAM_GB" -ge 32 ] && ok "RAM >= 32GB (LLM 32B-70B ke liye)" || warn "RAM < 32GB — LLM ko GGUF quantized use karein"

say "4) Disk space"
DISK_GB=$(df -BG --output=avail / | tail -1 | tr -d ' GB')
echo "  Available: ${DISK_GB}GB"
if [ "${DISK_GB:-0}" -ge 1000 ]; then ok "Disk >= 1TB — full stack + weights fit"
elif [ "${DISK_GB:-0}" -ge 400 ]; then warn "Disk 400GB-1TB — kam models dalna padega (pick: Wan + Hunyuan + FLUX klein)"
else bad "Disk < 400GB — models nahi fit honge. 2TB NVMe recommended."
fi

say "5) Python / venv"
if command -v python3 >/dev/null 2>&1; then
  ok "python3: $(python3 --version)"
else bad "python3 missing"
fi
python3 -c "import venv" 2>/dev/null && ok "venv module present" || { bad "python3-venv missing (apt install python3-venv)"; }

say "6) git / curl / ffmpeg"
for t in git curl ffmpeg; do
  command -v $t >/dev/null 2>&1 && ok "$t: $(command -v $t)" || bad "$t missing"
done
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg version: $(ffmpeg -version 2>/dev/null | head -1)"
  ffmpeg -hide_banner -encoders 2>/dev/null | grep -q h264_nvenc && ok "h264_nvenc available (fast GPU encode)" || warn "h264_nvenc nahi mila — CPU encode hoga (slow)"
fi

say "7) huggingface-cli"
if command -v huggingface-cli >/dev/null 2>&1; then ok "huggingface-cli present"
else warn "huggingface-cli missing — 01_setup_venv.sh me install hoga"
fi

echo "------------------------------------------------------------"
echo " RESULT:  PASS=$PASS   WARN=$WARN   FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  printf '\033[1;32mSETUP READY — next: bash ai_film_studio/setup/01_setup_venv.sh\033[0m\n'
else
  printf '\033[1;31mKuch critical tools missing hain — upar [XX] wale fix karein.\033[0m\n'
fi
