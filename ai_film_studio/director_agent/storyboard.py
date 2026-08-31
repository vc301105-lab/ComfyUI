"""Storyboard: deterministic keyframe prompt builder (no LLM required)."""


def build_keyframe_prompts(plan, llm=None):
    """Return {scene_id: prompt}. Works offline via template; optional LLM
    refinement when llm is provided."""
    style = plan.get("style", "cinematic")
    chars = {c.get("name"): c.get("appearance", "") for c in plan.get("characters", [])}
    suffix = (", cinematic lighting, 8k, highly detailed, depth of field, "
              "film still, " + style)

    scenes = []
    for sc in plan["scenes"]:
        char_desc = ""
        for d in sc.get("dialogue", []):
            name = d.get("character")
            if name in chars and chars[name]:
                char_desc = f", {chars[name]}"
                break
        base = sc.get("image_prompt") or sc.get("description", "")
        prompt = (f"{base}{char_desc}, {sc.get('shot', '')}, "
                  f"{sc.get('location', '')}, {sc.get('time', 'day')}{suffix}")
        scenes.append({"scene_id": sc["id"], "prompt": prompt})

    if llm is not None:
        # Optional LLM pass (guarded; failures fall back to deterministic).
        from prompts import read_prompt
        try:
            system = read_prompt("02_storyboard.md").format(
                style_suffix=suffix.strip(", "))
            user = plan["title"] + "\n" + "\n".join(
                f"S{sc['id']}: {sc['description']} | {sc['shot']} | {sc['location']} {sc['time']}"
                for sc in plan["scenes"])
            data = llm.chat_json(system, user)
            refined = {int(k["scene_id"]): k["prompt"] for k in data.get("keyframes", [])}
            for s in scenes:
                if s["scene_id"] in refined:
                    s["prompt"] = refined[s["scene_id"]]
        except Exception as e:
            print(f"[storyboard] LLM refine skipped: {e}")
    return scenes
