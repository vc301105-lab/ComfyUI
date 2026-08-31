"""Mock ComfyUI HTTP server (pure stdlib) — GPU ke bina E2E testing.

ComfyUI ke required endpoints simulate karta hai:
  GET  /object_info        -> classes/inputs (workflows + built-in templates)
  POST /upload/image       -> {name, subfolder, type}
  POST /prompt             -> {prompt_id} (short delay ke baad completed)
  GET  /history/<id>       -> {outputs: {images: [...]}} (Save/mp4)
  GET  /view?filename=...  -> fake PNG / MP4 bytes

Use: srv = MockComfy(ui_workflow); srv.url ; srv.stop()
"""
import base64
import json
import os
import re
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

# built-in template nodes jo workflows me nahi hote
TEMPLATE_SPECS = {
    "CheckpointLoaderSimple": ["ckpt_name"],
    "CLIPTextEncode": ["clip", "text"],
    "EmptyLatentImage": ["width", "height", "batch_size"],
    "KSampler": ["model", "positive", "negative", "latent_image", "seed",
                 "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    "VAEDecode": ["samples", "vae"],
    "SaveImage": ["images", "filename_prefix"],
    "CLIPVisionLoader": ["clip_name"],
    "IPAdapterUnifiedLoader": ["model", "preset", "lora_strength", "provider",
                               "cache_model", "clip_vision"],
    "IPAdapter": ["model", "ipadapter", "image", "weight", "weight_face",
                  "weight_type", "combine_embeds", "start_at", "end_at",
                  "embeds_scaling"],
    "LoadImage": ["image", "upload"],
    "UNETLoader": ["unet_name", "weight_dtype"],
    "VAELoader": ["vae_name"],
    "EmptySD3LatentImage": ["width", "height", "batch_size"],
    "SaveVideo": ["filename_prefix", "format", "codec"],
    "CreateVideo": ["images", "audio", "fps"],
}

SAVE_CLASSES = {"SaveImage", "VHS_VideoCombine", "SaveVideo", "CreateVideo"}


class MockComfy:
    def __init__(self, ui_workflow):
        self.specs = dict(TEMPLATE_SPECS)
        for node in ui_workflow.get("nodes", []):
            cls = node.get("type")
            if not cls or cls in self.specs:
                continue
            wv = node.get("widgets_values") or []
            if isinstance(wv, dict):
                names = list(wv.keys())
            else:
                names = [f"w{i}" for i in range(len(wv))]
            names += [i.get("name") for i in node.get("inputs", [])]
            self.specs[cls] = names
        self.history = {}
        self.object_info = {
            cls: {"input": {
                "required": {n: ["X"] for n in names},
                "optional": {},
                "input_order": {"required": names, "optional": []},
            }}
            for cls, names in self.specs.items()
        }
        server = self
        root = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, code, obj):
                data = json.dumps(obj).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                path = urlparse(self.path).path
                qs = parse_qs(urlparse(self.path).query)
                if path == "/object_info":
                    return self._json(200, root.object_info)
                if path.startswith("/history/"):
                    pid = path.split("/")[-1]
                    return self._json(200, {pid: root.history[pid]}
                                      if pid in root.history else {})
                if path == "/view":
                    filename = (qs.get("filename") or ["mock.png"])[0]
                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        data = PNG_1PX
                    else:
                        data = b"MOCKVIDEO"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                return self._json(404, {"error": "not found"})

            def do_POST(self):
                path = urlparse(self.path).path
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                if path == "/upload/image":
                    m = re.search(r'filename="([^"]+)"',
                                  self.headers.get("Content-Disposition", ""))
                    name = m.group(1) if m else "upload.png"
                    return self._json(200, {"name": name, "subfolder": "", "type": "input"})
                if path == "/prompt":
                    try:
                        payload = json.loads(body.decode("utf-8"))
                    except Exception:
                        return self._json(400, {"error": {"type": "bad_request"}})
                    prompt = payload.get("prompt") or {}
                    node_errors = {}
                    for nid, node in prompt.items():
                        if node.get("class_type") not in root.specs:
                            node_errors[nid] = {
                                "errors": [{"message": f"unknown class {node.get('class_type')}"}]}
                    if node_errors:
                        return self._json(400, {"error": {"type": "invalid_prompt",
                                                          "node_errors": node_errors}})
                    pid = uuid.uuid4().hex
                    # async completion
                    def complete(p=pid, pr=prompt):
                        time.sleep(0.15)
                        outputs = {}
                        for nid, node in pr.items():
                            if node.get("class_type") in SAVE_CLASSES:
                                ext = ".png" if node["class_type"] == "SaveImage" else ".mp4"
                                outputs[nid] = {"images": [{
                                    "filename": f"mock_out_{nid}{ext}",
                                    "subfolder": "", "type": "output"}]}
                        root.history[p] = {
                            "status": {"status_str": "success", "completed": True,
                                       "messages": []},
                            "outputs": outputs,
                        }
                    threading.Thread(target=complete, daemon=True).start()
                    return self._json(200, {"prompt_id": pid, "number": 0,
                                            "node_errors": {}})
                return self._json(404, {"error": "not found"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
