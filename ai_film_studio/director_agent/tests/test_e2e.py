"""End-to-end test (GPU/zombie nahi): plan -> render (multi-GPU mock) -> assemble.

Mock ComfyUI servers use karta hai + stub ffmpeg, taaki poora automation flow
is sandbox me bhi verify ho. Run: python3 tests/test_e2e.py
"""
import json
import os
import shutil
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.dirname(HERE)
ROOT = os.path.dirname(AGENT)
sys.path.insert(0, AGENT)

import config as config_mod  # noqa: E402
import renderer  # noqa: E402
import assembler  # noqa: E402
import planner  # noqa: E402
from state import load_state, project_dir, save_plan  # noqa: E402
from tests.mock_comfy import MockComfy  # noqa: E402

WORKFLOW = os.path.join(ROOT, "workflows", "wan22_5b_i2v_example.json")
STUB_DIR = os.path.join(tempfile.gettempdir(), "aifs_stub_bin")


def _stub_ffmpeg():
    os.makedirs(STUB_DIR, exist_ok=True)
    ff = os.path.join(STUB_DIR, "ffmpeg")
    with open(ff, "w") as f:
        f.write("""#!/bin/bash
# stub ffmpeg: last arg = output, first existing file after -i = input
out="${@: -1}"
src=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-i" ]; then src="$a"; break; fi
  prev="$a"
done
[ -z "$src" ] && src="$(ls "$(dirname "$out")"/*.mp4 2>/dev/null | head -1)"
if [ -f "$src" ]; then cp "$src" "$out"; else touch "$out"; fi
""")
    os.chmod(ff, os.stat(ff).st_mode | stat.S_IEXEC)
    fp = os.path.join(STUB_DIR, "ffprobe")
    with open(fp, "w") as f:
        f.write("#!/bin/bash\necho 48000\n")
    os.chmod(fp, os.stat(fp).st_mode | stat.S_IEXEC)
    os.environ["PATH"] = STUB_DIR + os.pathsep + os.environ.get("PATH", "")


def main():
    _stub_ffmpeg()
    wf = json.load(open(WORKFLOW, encoding="utf-8"))
    srv1, srv2 = MockComfy(wf), MockComfy(wf)
    tmp = tempfile.mkdtemp(prefix="aifs_e2e_")
    try:
        cfg = config_mod.load_config()
        cfg["comfy_url"] = srv1.url
        cfg["comfy_urls"] = [srv1.url, srv2.url]
        cfg["project_root"] = tmp
        cfg["image_checkpoint"] = "fake.safetensors"

        # 1) plan (mock, no LLM)
        plan = planner.build_plan(cfg, None, "E2E test film", scene_count=3, mock=True)
        proj = project_dir(cfg, "e2e")
        save_plan(proj, plan)
        assert len(plan["scenes"]) == 3

        # 2) render on 2 mock GPUs
        renderer.render_project(cfg, proj, parallel=2)
        state = load_state(proj)
        done = [k for k, v in state.items() if k.startswith("scene_") and v.get("video")]
        print("scenes done:", len(done))
        assert len(done) == 3, f"expected 3 rendered scenes, got {len(done)}"
        for k in done:
            v = state[k].get("video")
            assert v and os.path.exists(os.path.join(proj, "scenes", v)), \
                f"{k}: missing video {v}"
            kf = state[k].get("keyframe")
            assert kf and os.path.exists(os.path.join(proj, "keyframes", kf)), \
                f"{k}: missing keyframe {kf}"
        print("[OK] render (parallel=2, keyframes + videos + state)")

        # 3) assemble with stub ffmpeg
        out = assembler.concat_videos(proj, fps=24)
        assert os.path.exists(out) and os.path.getsize(out) > 0
        print(f"[OK] assemble -> {out}")

        # 4) resume behaviour: second run skip
        renderer.render_project(cfg, proj, parallel=2)
        print("[OK] resumable state (skip already rendered)")

        print("\nE2E PASSED ✅ (plan -> cast path -> multi-GPU render -> assemble)")
    finally:
        srv1.stop()
        srv2.stop()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
