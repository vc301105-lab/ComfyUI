"""State helpers: project dirs + resumable state.json."""

import json
import os


def project_dir(cfg, name):
    d = os.path.join(cfg["project_root"], name)
    os.makedirs(os.path.join(d, "keyframes"), exist_ok=True)
    os.makedirs(os.path.join(d, "scenes"), exist_ok=True)
    os.makedirs(os.path.join(d, "audio"), exist_ok=True)
    os.makedirs(os.path.join(d, "meta"), exist_ok=True)
    return d


def state_path(project):
    return os.path.join(project, "meta", "state.json")


def load_state(project):
    p = state_path(project)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(project, state):
    with open(state_path(project), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_plan(project):
    p = os.path.join(project, "plan.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_plan(project, plan):
    with open(os.path.join(project, "plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
