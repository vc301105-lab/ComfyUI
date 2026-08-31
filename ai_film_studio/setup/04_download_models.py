#!/usr/bin/env python3
"""Model downloader — manifest-based, license-aware, disk-check.

Usage (ComfyUI root se):
  python3 setup/04_download_models.py --tier all            # sab
  python3 setup/04_download_models.py --tier core           # video engines
  python3 setup/04_download_models.py --tier optional       # image/consistency
  python3 setup/04_download_models.py --tier audio          # TTS/music
  python3 setup/04_download_models.py --dry-run             # sirf plan
  python3 setup/04_download_models.py --name "Wan 2.2"      # substring filter
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMFY_ROOT = os.path.dirname(os.path.dirname(HERE))   # repo root (models/ yahan se)
MANIFEST = os.path.join(HERE, "models.json")


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def hf_cli():
    return shutil.which("huggingface-cli")


def disk_free(path):
    return shutil.disk_usage(path).free // (1024 ** 3)


def download(entry, dry_run, force):
    repo = entry["repo"]
    local = os.path.join(COMFY_ROOT, entry["local_dir"])
    os.makedirs(local, exist_ok=True)
    if not dry_run and os.path.exists(local) and os.listdir(local) and not force:
        print(f"  [skip] {entry['name']} (already exists: {local})")
        return "skip"
    print(f"  [get ] {entry['name']} -> {local}")
    print(f"         license: {entry.get('license')} "
          f"{' [VERIFY repo id!]' if entry.get('verify') else ''} "
          f"~{entry.get('size_gb')}GB")
    if dry_run:
        return "dry"
    cli = hf_cli()
    if not cli:
        print("  [ERR ] huggingface-cli nahi mila — setup/01_setup_venv.sh chalein")
        return "error"
    files = entry.get("files")
    cmd = [cli, "download", repo, "--local-dir", local]
    if files:
        cmd += ["--include"] + files
    print("  $", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, timeout=86400)
    except Exception as e:
        print(f"  [ERR ] download failed: {e}")
        return "error"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["core", "optional", "audio", "all"], default="core")
    ap.add_argument("--name", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    manifest = load_manifest()
    entries = []
    if args.tier == "all":
        for tier in ("core", "optional", "audio"):
            entries += manifest.get(tier, [])
    else:
        entries += manifest.get(args.tier, [])
    if args.name:
        entries = [e for e in entries if args.name.lower() in e["name"].lower()]

    total = sum(e.get("size_gb", 0) for e in entries)
    print(f"Plan: {len(entries)} models, ~{total}GB | free disk: {disk_free(COMFY_ROOT)}GB")
    if not args.dry_run and disk_free(COMFY_ROOT) < total * 1.05:
        print(f"[WARN] disk kam lag raha hai — free {disk_free(COMFY_ROOT)}GB, needs ~{total}GB")
        if args.tier == "all":
            print("       Tip: --tier core se shuru karein, audio baad me.")

    results = {}
    for e in entries:
        results[e["name"]] = download(e, args.dry_run, args.force)
    ok = sum(1 for v in results.values() if v in ("ok", "skip"))
    err = [k for k, v in results.items() if v == "error"]
    print(f"\nDone: {ok}/{len(entries)} ok | errors: {err or 'none'}")
    if not verify_hf_token() and not args.dry_run:
        print("[TIP] private/big repos ke liye: huggingface-cli login")


def verify_hf_token():
    return bool(os.environ.get("HF_TOKEN"))


if __name__ == "__main__":
    main()
