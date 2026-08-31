"""QC reviewer + dubbing unit tests (stub ffmpeg/ffprobe, fake LLM)."""
import json
import os
import shutil
import stat
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.dirname(HERE)
sys.path.insert(0, AGENT)

import config as config_mod  # noqa: E402
import qcr  # noqa: E402
import dub  # noqa: E402
import planner  # noqa: E402
from state import load_plan, load_state, project_dir, save_plan, save_state  # noqa: E402

STUB = os.path.join(tempfile.gettempdir(), "aifs_qc_bin")


def _stub_bins():
    os.makedirs(STUB, exist_ok=True)
    ff = os.path.join(STUB, "ffmpeg")
    with open(ff, "w") as f:
        f.write("""#!/bin/bash
# stub ffmpeg: QC detection lines -> stderr; otherwise copy last arg if input exists
echo "[blackdetect] black_start:0.5 black_end:1.5 black_duration:1.0" >&2
echo "pts_time:2.0" >&2
echo "psnr:average:28.5" >&2
out="${@: -1}"
if [ "$out" = "-" ]; then exit 0; fi
src=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-i" ]; then src="$a"; break; fi
  prev="$a"
done
if [ -f "$src" ]; then cp "$src" "$out" 2>/dev/null; else touch "$out" 2>/dev/null; fi
exit 0
""")
    os.chmod(ff, os.stat(ff).st_mode | stat.S_IEXEC)
    fp = os.path.join(STUB, "ffprobe")
    with open(fp, "w") as f:
        f.write("""#!/bin/bash
echo '{"streams":[{"codec_type":"video","codec_name":"h264","width":832,"height":480,
"avg_frame_rate":"24/1","duration":"5.2"},{"codec_type":"audio","codec_name":"aac"}],
"format":{"duration":"5.2"}}'
""")
    os.chmod(fp, os.stat(fp).st_mode | stat.S_IEXEC)
    os.environ["PATH"] = STUB + os.pathsep + os.environ.get("PATH", "")


def _touch(path):
    with open(path, "wb") as f:
        f.write(b"x" * 64)


def test_qc():
    tmp = tempfile.mkdtemp(prefix="aifs_qc_")
    try:
        cfg = config_mod.load_config()
        cfg["project_root"] = tmp
        proj = project_dir(cfg, "qcproj")
        plan = planner.build_plan(cfg, None, "t", scene_count=2, mock=True)
        save_plan(proj, plan)
        # fake rendered scenes
        st = {}
        for sid in (1, 2):
            p = os.path.join(proj, "scenes", f"mock_s{sid}.mp4")
            _touch(p)
            st[f"scene_{sid:02d}"] = {"video": f"mock_s{sid}.mp4"}
        save_state(proj, st)
        rep = qcr.review_project(proj, expected_seconds=5)
        assert rep["summary"]["scenes_checked"] == 2
        assert rep["summary"]["scenes_missing"] == 0
        for s in rep["scenes"].values():
            assert s["width"] == 832 and s["has_audio"] is True
            assert s["black_segments"][0][0] == 0.5
            assert s["cuts"] == 1
        assert rep["continuity"][0]["from"] == 1
        assert rep["continuity"][0]["to"] == 2
        assert rep["continuity"][0]["psnr"] == 28.5
        print(qcr.report_text(rep))
        print("[OK] qcr.review_project")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class FakeLLM:
    def chat_json(self, system, user):
        return {"translations": {"1:0": "Hello world", "2:0": "Let's do it"}}


def test_dub_translate():
    cfg = config_mod.load_config()
    plan = planner.build_plan(cfg, None, "t", scene_count=2, mock=True)
    tr = dub.translate_lines(cfg, plan, "en", FakeLLM())
    assert tr == {"1:0": "Hello world", "2:0": "Let's do it"}
    # patched scene
    sc = dub._patched_scene(plan["scenes"][0], tr)
    assert sc["dialogue"][0]["line"] == "Hello world"
    print("[OK] dub.translate_lines + patched")


def test_dub_offline_error():
    cfg = config_mod.load_config()
    plan = planner.build_plan(cfg, None, "t", scene_count=1, mock=True)
    try:
        dub.translate_lines(cfg, plan, "en", llm=None)
        raise SystemExit("expected error")
    except SystemExit:
        print("[OK] dub without llm -> SystemExit")


if __name__ == "__main__":
    _stub_bins()
    test_qc()
    test_dub_translate()
    test_dub_offline_error()
    print("\nALL QC/DUB TESTS PASSED")
