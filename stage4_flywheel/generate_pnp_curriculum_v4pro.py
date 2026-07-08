#!/usr/bin/env python3
"""T3 §9: PnP curriculum generator. Seed-based difficulty gradient for the
DoublePiperKitchenPnpPipeline. Deterministic mapping is ground truth;
DeepSeek-v4-pro provides rationale (validated against the deterministic result)."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
sys.path.insert(0, "/mnt/robot/stage4_flywheel")
from llm.deepseek_v4pro_call import call_deepseek_v4pro

PROBE = Path("/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json")
BASE_YML = Path("/mnt/robot/lw_benchhub/configs/envhub/example.yml")
OUT_DIR = Path("/mnt/robot/stage4_flywheel/curriculum")
GEN_DIR = Path("/mnt/robot/lw_benchhub/configs/envhub/generated_stage4")
LLM_DIR = Path("/mnt/robot/stage4_flywheel/llm")
OUT_DIR.mkdir(parents=True, exist_ok=True); GEN_DIR.mkdir(parents=True, exist_ok=True); LLM_DIR.mkdir(parents=True, exist_ok=True)

def deterministic_mapping(candidates):
    """easy = closest to robot (prefer 42 if in closest 10%); hard = farthest; medium = median."""
    srt = sorted(candidates, key=lambda c: c["dist_to_robot"])
    n = len(srt)
    easy_candidates = srt[: max(1, n // 10)]
    easy = next((c for c in easy_candidates if c["seed"] == 42), easy_candidates[0])
    hard = srt[-1]
    medium = srt[n // 2]
    return {"easy": easy, "medium": medium, "hard": hard}, srt

def llm_rationale(srt, mapping):
    """Optional: ask DeepSeek-v4-pro to confirm the easy/medium/hard assignment with rationale."""
    prompt = (
        "You assign difficulty labels to robot manipulation scene seeds for a kitchen pick-and-place task.\n"
        "A seed places the target bowl at a distance from the robot. Closer = easier; farther = harder.\n\n"
        f"Sorted candidates (seed, dist_to_robot_m), closest first:\n"
        + json.dumps([{"seed": c["seed"], "dist_to_robot": round(c["dist_to_robot"], 3)} for c in srt], indent=2)
        + "\n\nReturn ONLY strict JSON: {\"easy\": {\"seed\": <int>, \"rationale\": \"...\"}, "
        "\"medium\": {\"seed\": <int>, \"rationale\": \"...\"}, \"hard\": {\"seed\": <int>, \"rationale\": \"...\"}}.\n"
        "Rules: easy = one of the 3 closest seeds; hard = the single farthest seed; medium = a middle seed. "
        "Do not add other keys."
    )
    text = call_deepseek_v4pro(
        "You are a robotics curriculum designer. Return ONLY strict JSON, no prose, no code fences.",
        prompt, max_tokens=2048)
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.M).strip()
    return json.loads(text)

def write_yml(seed, level):
    text = re.sub(r"^seed:\s*\d+", f"seed: {seed}", BASE_YML.read_text(), count=1, flags=re.M)
    p = OUT_DIR / f"scene_{level}.yml"
    p.write_text(text, encoding="utf-8")
    (GEN_DIR / f"scene_{level}.yml").write_text(text, encoding="utf-8")
    print(f"Wrote {p} (seed={seed}) + copy to generated_stage4/")

def main():
    probe = json.loads(PROBE.read_text())
    candidates = probe["all"]
    mapping, srt = deterministic_mapping(candidates)
    print("Deterministic mapping:")
    for lvl in ("easy", "medium", "hard"):
        print(f"  {lvl}: seed={mapping[lvl]['seed']} dist={mapping[lvl]['dist_to_robot']:.3f}")

    audit = {"deterministic": {k: {"seed": v["seed"], "dist_to_robot": v["dist_to_robot"]}
                              for k, v in mapping.items()}}
    try:
        llm_map = llm_rationale(srt, mapping)
        audit["llm"] = llm_map
        # validate: LLM seeds must respect the difficulty ordering (dist_easy <= dist_medium <= dist_hard)
        det_d = {k: mapping[k]["dist_to_robot"] for k in mapping}
        llm_d = {k: next((c["dist_to_robot"] for c in srt if c["seed"] == llm_map[k]["seed"]), None) for k in llm_map}
        ok = (llm_d["easy"] is not None and llm_d["easy"] <= llm_d["medium"] <= llm_d["hard"]
              and llm_d["easy"] <= det_d["medium"])
        audit["llm_validated"] = ok
        print(f"LLM rationale {'VALIDATED' if ok else 'REJECTED (using deterministic)'}")
        if not ok:
            audit["llm_reject_reason"] = "LLM assignment violates dist_easy <= dist_medium <= dist_hard"
    except Exception as e:
        audit["llm_error"] = str(e)
        print(f"LLM rationale skipped/failed: {e}")

    (LLM_DIR / "t3_curriculum_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    for lvl in ("easy", "medium", "hard"):
        write_yml(mapping[lvl]["seed"], lvl)
    print("T3 curriculum generation complete.")

if __name__ == "__main__":
    main()
