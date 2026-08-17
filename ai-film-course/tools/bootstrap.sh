#!/usr/bin/env bash
# ============================================================
#  One-command restore of the local AI filmmaking environment.
#
#  Use after a sandbox/workspace reset, or on a fresh GPU machine
#  (on a fresh machine: skip the pip flag, you won't need it).
#
#    bash ai-film-course/tools/bootstrap.sh
#
#  What it does:
#    1. installs ComfyUI's python requirements + build tools
#    2. installs ComfyUI-Manager + ComfyUI_IPAdapter_plus
#    3. regenerates + validates all workflows against the server
#    4. regenerates the sound beds, captions, thumbnail
#    5. rebuilds film.mp4 + film-vertical.mp4
#
#  NOTE: the AI-generated assets (frames/*.png, audio/narration.mp3)
#  must exist already — they can only be created by the image/voice
#  models. They ARE committed in this git repo, so a reset is fine;
#  on a fresh machine, just clone the repo.
# ============================================================
set -euo pipefail
COMFY=${COMFY:-/home/user/ComfyUI}
COURSE=${COURSE:-"$COMFY/ai-film-course"}

echo "==> [1/5] python requirements (this is the big one)"
( pip install --break-system-packages -r "$COMFY/requirements.txt" \
  || pip install --break-system-packages -r "$COMFY/requirements.txt" ) 2>&1 | tail -2
pip install --break-system-packages -q imageio-ffmpeg pillow GitPython PyGithub matrix-nio uv chardet toml

echo "==> [2/5] custom node packs"
mkdir -p "$COMFY/custom_nodes"
[ -d "$COMFY/custom_nodes/ComfyUI-Manager" ] || \
  git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git "$COMFY/custom_nodes/ComfyUI-Manager"
[ -d "$COMFY/custom_nodes/ComfyUI_IPAdapter_plus" ] || \
  git clone --depth 1 https://github.com/cubiq/ComfyUI_IPAdapter_plus.git "$COMFY/custom_nodes/ComfyUI_IPAdapter_plus"

echo "==> [3/5] workflows (needs the server — starting it briefly)"
cd "$COMFY"
if ! curl -s -o /dev/null http://127.0.0.1:8188/system_stats; then
  nohup python3 main.py --cpu --listen 0.0.0.0 --port 8188 > /tmp/comfy-bootstrap.log 2>&1 &
  for i in $(seq 1 30); do
    sleep 5
    curl -s -o /dev/null http://127.0.0.1:8188/system_stats && break
  done
fi
python3 "$COURSE/tools/build_comfy_workflow.py"

echo "==> [4/5] sound design + captions + thumbnail"
python3 "$COURSE/demo-film/audio/make_ambience.py"
python3 "$COURSE/demo-film/audio/make_music.py"
python3 "$COURSE/demo-film/make_subtitles.py"
python3 "$COURSE/demo-film/make_thumbnail.py"

echo "==> [5/5] films"
bash "$COURSE/demo-film/build_film.sh"
bash "$COURSE/demo-film/build_vertical.sh"

echo "==> DONE. ComfyUI: http://localhost:8188 | film: $COURSE/demo-film/film.mp4"
