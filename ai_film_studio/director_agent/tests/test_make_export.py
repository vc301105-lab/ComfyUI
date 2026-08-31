"""One-shot make + export pack tests (mock ComfyUI + stub ffmpeg).

Run: python3 tests/test_make_export.py
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
import pipeline  # noqa: E402
import export  # noqa: E402
import planner  # noqa: E402
from state import project_dir, save_plan, save_state, load_plan, load_state  # noqa: E402
from tests.mock_comfy import MockComfy  # noqa: E402

WORKFLOW = os.path.join(ROOT, "workflows", "wan22_5b_i2v_example.json")
STUB = os.path.join(tempfile.gettempdir(), "aifs_make_bin")


def _stub():
    os.makedirs(STUB, exist_ok=True)
    ff = os.path.join(STUB, "ffmpeg")
    with open(ff, "w") as f:
        f.write("""#!/bin/bash
echo "[blackdetect] black_start:0.5 black_end:1.5 black_duration:0.3" >&2
echo "pts_time:2.0" >&2
out="${@: -1}"
if [ "$out" = "-" ]; then exit 0; fi
src=""; prev=""
for a in "$@"; do
  if [ "$prev" = "-i" ]; then src="$a"; break; fi
  prev="$a"
done
# lavfi color/drawtext sources have no -i source file: just touch output
if [ -z "$src" ] || [ ! -f "$src" ]; then touch "$out"; else cp "$src" "$out"; fi
exit 0
""")
    os.chmod(ff, os.stat(ff).st_mode | stat.S_IEXEC)
    fp = os.path.join(STUB, "ffprobe")
    with open(fp, "w") as f:
        f.write("""#!/bin/bash
echo '{"streams":[{"codec_type":"video","codec_name":"h264","width":832,"height":480,
"avg_frame_rate":"24/1","duration":"5.0"},{"codec_type":"audio","codec_name":"aac"}],
"format":{"duration":"5.0"}}'
""")
    os.chmod(fp, os.stat(fp).st_mode | stat.S_IEXEC)
    os.environ["PATH"] = STUB + os.pathsep + os.environ.get("PATH", "")


def test_make_mock():
    srv = MockComfy(json.load(open(WORKFLOW, encoding="utf-8")))
    tmp = tempfile.mkdtemp(prefix="aifs_make_")
    try:
        cfg = config_mod.load_config()
        cfg["comfy_url"] = srv.url
        cfg["comfy_urls"] = [srv.url]
        cfg["project_root"] = tmp
        cfg["project_name"] = "makefilm"
        cfg["image_checkpoint"] = "fake.safetensors"
        project, final = pipeline.run_make(
            cfg, "E2E one-shot film", scene_count=2, mock=True,
            parallel=1, identity=False, auto_fix=True, max_fix=1)
        assert project and final and os.path.exists(final), "final missing"
        rep = json.load(open(os.path.join(project, "meta", "make_report.json")))
        assert rep["title"] == "Chai Aur Sitaare"
        assert rep["summary"]["scenes_total"] == 2
        assert rep["fix_attempts"] >= 1, "auto-fix should have triggered (stub black)"
        print(f"[OK] run_make one-shot (fix attempts={rep['fix_attempts']}) -> {final}")
        return project
    finally:
        srv.stop()
        shutil.rmtree(tmp, ignore_errors=True)


def test_export(tmp):
    cfg = config_mod.load_config()
    cfg["project_root"] = tmp
    proj = project_dir(cfg, "exp")
    plan = planner.build_plan(cfg, None, "t", scene_count=3, mock=True)
    save_plan(proj, plan)
    st = {}
    for sid in (1, 2, 3):
        p = os.path.join(proj, "scenes", f"s{sid}.mp4")
        with open(p, "wb") as f:
            f.write(b"x" * 64)
        kp = os.path.join(proj, "keyframes", f"kf_{sid:02d}.png")
        with open(kp, "wb") as f:
            f.write(b"x" * 64)
        st[f"scene_{sid:02d}"] = {"video": f"s{sid}.mp4", "keyframe": f"kf_{sid:02d}.png"}
    save_state(proj, st)

    ids = export.pick_top_scenes(proj, n=2)
    assert ids, "top scenes empty"
    tr = export.make_trailer(proj, scene_ids=ids, out="trailer.mp4")
    assert tr and os.path.exists(tr), "trailer missing"
    po = export.make_poster(proj, scene_id=1, out="poster.png")
    assert po and os.path.exists(po), "poster missing"
    cr = export.make_credits(proj, out="credits.mp4", seconds=3)
    assert cr and os.path.exists(cr), "credits missing"
    pr = export.platform_preset(proj, src=os.path.join(proj, "scenes", "s1.mp4"),
                                preset="youtube", out=os.path.join(proj, "yt.mp4"))
    assert pr and os.path.exists(pr), "preset missing"
    pr2 = export.platform_preset(proj, src=os.path.join(proj, "scenes", "s1.mp4"),
                                 preset="shorts", out=os.path.join(proj, "sh.mp4"))
    assert pr2 and os.path.exists(pr2), "shorts preset missing"
    print(f"[OK] export: trailer({ids}) poster credits youtube shorts")
    assert export.PRESETS["reels"] == (1080, 1920)
    print("[OK] presets table")


if __name__ == "__main__":
    _stub()
    p = test_make_mock()
    test_export(tempfile.mkdtemp(prefix="aifs_exp_"))
    print("\nALL MAKE/EXPORT TESTS PASSED")
