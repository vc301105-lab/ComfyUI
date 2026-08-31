"""ComfyUI HTTP API client (no websocket dependency — history polling).

- Converts UI-format workflow JSON -> API format using /object_info
  (same mapping ComfyUI's own frontend uses).
- upload_image / submit / wait / download_output.
"""
import json
import os
import time
import urllib.parse
import urllib.request

import uuid


class ComfyError(RuntimeError):
    pass


def _post(url, payload, timeout=30):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post_multipart(url, field_name, filepath, timeout=120):
    boundary = "----AIFilmStudio" + uuid.uuid4().hex
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class ComfyClient:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.client_id = uuid.uuid4().hex
        self._object_info = None

    # ---------------- object info ----------------
    def object_info(self):
        if self._object_info is None:
            self._object_info = _get(self.base + "/object_info", timeout=120)
        return self._object_info

    def _spec(self, class_type):
        info = self.object_info().get(class_type)
        if not info:
            return None
        return info.get("input", {})

    # ---------------- UI workflow -> API format ----------------
    def ui_to_api(self, wf):
        """Convert {nodes, links} UI workflow to {id: {class_type, inputs}}."""
        # ComfyUI frontend converter logic (mirrors graphToPrompt)
        if not isinstance(wf, dict) or "nodes" not in wf:
            return wf  # already API-ish
        link_map = {}
        for link in wf.get("links", []):
            # [link_id, origin_id, origin_slot, target_id, target_slot, type]
            link_map[link[0]] = link
        api = {}
        missing = set()
        for node in wf.get("nodes", []):
            nid = str(node.get("id"))
            cls = node.get("type")
            if not cls:
                continue
            spec = None
            if node.get("widgets_values"):
                spec = self._spec(cls)
                if spec is None:
                    missing.add(cls)
                    continue
            spec = spec or {}
            required = spec.get("required") or {}
            optional = spec.get("optional") or {}
            order = spec.get("input_order") or {}
            ordered = list(order.get("required") or required.keys()) + \
                      list(order.get("optional") or optional.keys())
            if not ordered:
                ordered = list(required.keys()) + list(optional.keys())

            # names of inputs that are linkable/converted (present in UI inputs)
            used = {i.get("name") for i in node.get("inputs", []) if i.get("name")}
            widgets = node.get("widgets_values") or []
            inputs = {}
            if isinstance(widgets, dict):
                # VHS_VideoCombine jaise nodes: widgets_values = {name: value}
                known = set(required) | set(optional) | set(ordered)
                for k, v in widgets.items():
                    if k in known:
                        inputs[k] = v
            else:
                widget_names = [n for n in ordered if n not in used]
                for name, val in zip(widget_names, widgets):
                    inputs[name] = val
            for inp in node.get("inputs", []):
                link_id = inp.get("link")
                if link_id is not None and link_id in link_map:
                    link = link_map[link_id]
                    inputs[inp["name"]] = [str(link[1]), link[2]]
            api[nid] = {"class_type": cls, "inputs": inputs}
        if missing:
            raise ComfyError(
                "ComfyUI /object_info me in custom-node classes nahi mile: "
                + ", ".join(sorted(missing))
                + ". Related custom node install nahi hai — setup/02_install_custom_nodes.sh "
                  "se install karein.")
        return api

    # ---------------- uploads / queue ----------------
    def upload_image(self, filepath, overwrite=True):
        filename = os.path.basename(filepath)
        res = _post_multipart(self.base + "/upload/image", "image", filepath)
        if res.get("name") != filename and not overwrite:
            raise ComfyError(f"Upload name mismatch: {res}")
        return {"name": res.get("name", filename),
                "subfolder": res.get("subfolder", ""),
                "type": res.get("type", "input")}

    def submit(self, api_workflow):
        res = _post(self.base + "/prompt",
                    {"prompt": api_workflow, "client_id": self.client_id}, timeout=60)
        if "error" in res:
            raise ComfyError(f"ComfyUI prompt error: {json.dumps(res['error'])[:500]}")
        return res.get("prompt_id")

    def wait(self, prompt_id, timeout=7200, poll=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            hist = _get(f"{self.base}/history/{prompt_id}", timeout=60)
            if prompt_id in hist:
                entry = hist[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error" or status.get("completed") is False \
                        and status.get("status_str") == "error":
                    raise ComfyError(f"Execution error: {json.dumps(status)[:800]}")
                if status.get("completed"):
                    return entry
            time.sleep(poll)
        raise ComfyError(f"Timeout waiting for prompt {prompt_id}")

    # ---------------- outputs ----------------
    def download_outputs(self, entry, out_dir, suffix=""):
        """Return list of saved file paths (videos + images) from a history entry."""
        os.makedirs(out_dir, exist_ok=True)
        saved = []
        outputs = entry.get("outputs", {})
        for node_id, out in outputs.items():
            for kind in ("videos", "images", "gifs", "audio"):
                for item in out.get(kind, []) or []:
                    filename = item.get("filename")
                    if not filename:
                        continue
                    params = urllib.parse.urlencode({
                        "filename": filename,
                        "subfolder": item.get("subfolder", ""),
                        "type": item.get("type", "output"),
                    })
                    url = f"{self.base}/view?{params}"
                    base, ext = os.path.splitext(filename)
                    local = os.path.join(out_dir, f"{base}{suffix}{ext}")
                    with urllib.request.urlopen(url, timeout=600) as r:
                        with open(local, "wb") as f:
                            f.write(r.read())
                    saved.append(local)
        return saved
