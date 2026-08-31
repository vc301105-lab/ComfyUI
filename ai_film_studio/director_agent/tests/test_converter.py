"""Contract test: manifest apply + UI->API conversion for every shipped workflow.

Chalane ka tarika (no ComfyUI needed):
  python3 tests/test_converter.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.dirname(HERE)
sys.path.insert(0, AGENT)

import comfy  # noqa: E402
import renderer  # noqa: E402

WORKFLOWS = os.path.join(os.path.dirname(AGENT), "workflows")


def fake_object_info(workflow):
    """Build object_info so har node ke widgets ko positional names milte hain."""
    info = {}
    for node in workflow.get("nodes", []):
        cls = node.get("type")
        if not cls or cls in info:
            continue
        wv = node.get("widgets_values") or []
        if isinstance(wv, dict):
            names = list(wv.keys())
        else:
            names = [f"w{i}" for i in range(len(wv))]
        used = {i.get("name") for i in node.get("inputs", [])}
        required = {n: ["X"] for n in names if n not in used}
        info[cls] = {"input": {
            "required": required, "optional": {},
            "input_order": {"required": list(required.keys()), "optional": []},
        }}
    return info


def values_of(api_node):
    return {k: v for k, v in api_node["inputs"].items() if isinstance(v, (str, int, float, bool))}


def main():
    manifest = renderer.load_manifest()
    failures = []
    for wf_name, m in manifest.items():
        if wf_name.startswith("_"):
            continue
        path = os.path.join(WORKFLOWS, wf_name)
        if not os.path.exists(path):
            print(f"[FAIL] {wf_name}: file missing")
            failures.append(wf_name)
            continue
        wf = json.load(open(path, encoding="utf-8"))
        client = comfy.ComfyClient("http://fake")
        client._object_info = fake_object_info(wf)

        uniq = f"UNIQ_{wf_name[:12]}"
        renderer._apply_manifest(wf, m, positive=f"{uniq}_POS", image=f"{uniq}_img.png",
                                 prefix=f"proj/{uniq}_prefix")
        api = client.ui_to_api(wf)

        # positive must land in manifest positive node
        pos_node = api.get(str(m["positive"]["node"]), {})
        pos_vals = list(values_of(pos_node).values())
        if not any(uniq + "_POS" in str(v) for v in pos_vals):
            failures.append(f"{wf_name}: positive not set")
        # image
        if m.get("image"):
            img_node = api.get(str(m["image"]["node"]), {})
            if not any(str(v).endswith("_img.png") for v in values_of(img_node).values()):
                failures.append(f"{wf_name}: image not set")
        # output prefix
        out_node = api.get(str(m["output"]["node"]), {})
        out_vals = list(values_of(out_node).values())
        if not any(uniq + "_prefix" in str(v) for v in out_vals):
            failures.append(f"{wf_name}: output prefix not set")

        print(f"[{'OK' if not any(wf_name in f for f in failures) else 'FAIL'}] "
              f"{wf_name} ({len(api)} nodes)")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("\nALL CONVERTER TESTS PASSED")


if __name__ == "__main__":
    main()
