"""Unit tests for post-production helpers (SRT writer, cmd template)."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.dirname(HERE)
sys.path.insert(0, AGENT)

import subs  # noqa: E402
import media  # noqa: E402


def test_srt():
    segs = [(0.5, 2.25, "Namaste duniya"), (2.5, 4.0, "Yeh ek test line hai")]
    path = os.path.join(tempfile.mkdtemp(), "test.srt")
    subs.write_srt(segs, path)
    data = open(path, encoding="utf-8").read()
    assert "00:00:00,500 --> 00:00:02,250" in data, data
    assert "Namaste duniya" in data and "Yeh ek test line hai" in data
    print("[OK] write_srt")


def test_template_command():
    cfg = {"probe": {"command": 'printf "%OUT%|%TEXT%" > "%OUT%"'}}
    out = os.path.join(tempfile.mkdtemp(), "out.txt")
    media.template_command(cfg, "probe", {"OUT": out, "TEXT": "hello"})
    assert os.path.exists(out)
    assert open(out).read() == f"{out}|hello"
    print("[OK] template_command placeholder replacement")


def test_template_empty():
    cfg = {"probe": {"command": ""}}
    assert media.template_command(cfg, "probe", {}) is None
    print("[OK] template_command empty -> None")


if __name__ == "__main__":
    test_srt()
    test_template_command()
    test_template_empty()
    print("\nALL POST TESTS PASSED")
