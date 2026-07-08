#!/usr/bin/env python3
"""Phase 3: DeepSeek-v4-pro curriculum generation.
Calls deepseek-v4-pro (STRICT, anti-degrade) to produce easy/medium bowl positions
at controlled Y-axis offsets from the hard-scene bowl position, then writes ymls
using lw_benchhub's fix_object_pose_cfg mechanism (plumbed by §9 patches)."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import yaml
sys.path.insert(0, "/mnt/robot/stage4_flywheel")
from llm.deepseek_v4pro_call import call_deepseek_v4pro

BOWL = "akita_black_bowl"
OFFSETS = {"easy": 0.10, "medium": 0.22}   # meters along world Y, toward the robot
TOL = 0.02

PROBE = Path("/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json")
HARD_YML = Path("/mnt/robot/stage4_flywheel/configs/hard_scene.yml")
DIAG = Path("/mnt/robot/stage4_flywheel/metrics/baseline/diagnosis.json")
EXAMPLE_YML = Path("/mnt/robot/lw_benchhub/configs/envhub/example.yml")
OUT_DIR = Path("/mnt/robot/stage4_flywheel/configs")
GEN_DIR = Path("/mnt/robot/lw_benchhub/configs/envhub/generated_stage4")
LLM_DIR = Path("/mnt/robot/stage4_flywheel/llm")
OUT_DIR.mkdir(parents=True, exist_ok=True); GEN_DIR.mkdir(parents=True, exist_ok=True); LLM_DIR.mkdir(parents=True, exist_ok=True)

def build_prompt(example_yml, hard_yml, hard_pos, diagnosis):
    return (
        "You generate curriculum scene configs for the LW-BenchHub DoublePiper-Abs kitchen PnP task.\n\n"
        "Given the baseline example.yml and the hard OOD scene yml, return STRICT JSON that shifts the\n"
        "target bowl back toward the robot by the requested Y-axis offsets.\n\n"
        f"Target object: {BOWL}\n"
        f"Hard-scene bowl world position: {hard_pos}\n"
        f"Required Y offsets: easy = {OFFSETS['easy']:.2f} m, medium = {OFFSETS['medium']:.2f} m\n"
        f"Failure diagnosis: {diagnosis.get('mode','unknown')} ({', '.join(diagnosis.get('signals',[]))})\n\n"
        "Return ONLY a JSON object of this exact shape:\n"
        '{"easy": {"object": "akita_black_bowl", "position": [x, y_easy, z], "rationale": "..."},\n'
        ' "medium": {"object": "akita_black_bowl", "position": [x, y_medium, z], "rationale": "..."}}\n\n'
        "Rules:\n"
        "1. object must be exactly 'akita_black_bowl'.\n"
        "2. position is [x, y, z] in world coordinates (3 floats).\n"
        "3. y_easy = hard_y + 0.10.\n"
        "4. y_medium = hard_y + 0.22.\n"
        "5. Do not add keys outside the schema.\n\n"
        f"--- baseline example.yml ---\n{example_yml.read_text()}\n"
        f"--- hard_scene.yml ---\n{hard_yml.read_text()}\n")

def validate_curriculum_json(text, hard_pos):
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.M).strip()
    data = json.loads(text)
    assert set(data) == {"easy", "medium"}, "top-level keys must be exactly easy, medium"
    for level, off in OFFSETS.items():
        e = data[level]
        assert e.get("object") == BOWL, f"{level} object must be {BOWL}"
        pos = e.get("position")
        assert isinstance(pos, list) and len(pos) == 3 and all(isinstance(v, (int, float)) for v in pos)
        assert abs(pos[1] - (hard_pos[1] + off)) < TOL, \
            f"{level} Y mismatch: got {pos[1]}, expected ~{hard_pos[1] + off}"
    return data

def write_curriculum_ymls(hard_yml, curriculum):
    base = yaml.safe_load(hard_yml.read_text())
    for level in ("easy", "medium"):
        cfg = dict(base)
        cfg["fix_object_pose_cfg"] = {curriculum[level]["object"]: {"pos": curriculum[level]["position"]}}
        p = OUT_DIR / f"{level}_curriculum.yml"
        p.write_text(yaml.dump(cfg, sort_keys=False, default_flow_style=False), encoding="utf-8")
        (GEN_DIR / f"{level}_curriculum.yml").write_text(p.read_text(), encoding="utf-8")
        print(f"Wrote {p} (and copy to generated_stage4/)")

def main():
    probe = json.loads(PROBE.read_text())
    hard_pos = probe["best"]["bowl_world"]
    diagnosis = json.loads(DIAG.read_text()) if DIAG.is_file() else {"mode": "unknown", "signals": []}
    prompt = build_prompt(EXAMPLE_YML, HARD_YML, hard_pos, diagnosis)
    (LLM_DIR / "curriculum_prompt.json").write_text(json.dumps({"prompt": prompt}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[generate_curriculum] hard_pos={hard_pos} calling deepseek-v4-pro...", flush=True)
    text = call_deepseek_v4pro(
        "You are a robotics curriculum generator. Return ONLY strict JSON, no prose, no code fences.",
        prompt, max_tokens=4096)
    (LLM_DIR / "curriculum_response.json").write_text(json.dumps({"response": text}, ensure_ascii=False, indent=2), encoding="utf-8")
    curriculum = validate_curriculum_json(text, hard_pos)
    write_curriculum_ymls(HARD_YML, curriculum)
    print(json.dumps(curriculum, indent=2))

if __name__ == "__main__":
    main()
