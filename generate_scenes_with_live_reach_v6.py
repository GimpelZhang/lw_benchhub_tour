#!/usr/bin/env python3
"""Stage 2 v5 — LLM scene generator with LIVE isaaclab+IK reach gate.

Like v4's generator, but the reach check actually BOOTS lw_benchhub's
isaaclab env per candidate scene (no more CSV-only math). This is the
final "what v3 wanted" stage from CLAUDE.md §14.7.

Output:
  /mnt/robot/lw_benchhub/configs/envhub/generated_v6/scene_variation_{1,2,3}.yml
  /mnt/robot/pathB_logs_v6/scene_reach_reports/scene_{1,2,3}_reach.json
  /mnt/robot/pathB_logs_v6/final_manifest.json
"""
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from openai import OpenAI

REPO_ROOT = Path("/mnt/robot")
LWB_ROOT = REPO_ROOT / "lw_benchhub"
TEMPLATE = LWB_ROOT / "configs/envhub/example.yml"
MAPPING_CSV = LWB_ROOT / "configs/layout_task_mapping/layout_task_mapping.csv"
OUTPUT_DIR = LWB_ROOT / "configs/envhub/generated_v6"
LOG_ROOT = REPO_ROOT / "pathB_logs_v6"
REACH_REPORT_DIR = LOG_ROOT / "scene_reach_reports"
VALIDATOR = REPO_ROOT / "validate_scene_objects_reach_v5.py"
# v5 difference: validator runs in SAME env as lerobot-eval (lerobot-arena)
LEROBOT_PY = Path("/mnt/robot/conda/envs/lerobot-arena/bin/python")
LEROBOT_ENV_SH = Path("/mnt/robot/lerobot_arena_curobo_env.sh")
HEADLESS_SH = Path("/mnt/robot/headless_env.sh")

N_SCENES = 3
MAX_ROUNDS = 6
REACH_THRESHOLD = 0.50

MUTABLE_FIELDS = {
    "task", "layout", "seed",
    "episode_length_s",
    "max_scene_retry", "max_object_placement_retry",
    "resample_objects_placement_on_reset",
    "resample_robot_placement_on_reset",
}


def load_template() -> dict:
    return yaml.safe_load(TEMPLATE.read_text())


def load_legal_combinations() -> set:
    combos = set()
    with open(MAPPING_CSV) as f:
        for row in csv.DictReader(f):
            if row["robot"] == "DoublePiper-Abs":
                combos.add((row["layout"], row["task"]))
    return combos


SYSTEM_PROMPT = """You generate scenario configurations for the LW-BenchHub
robotics simulator. The robot is fixed as DoublePiper-Abs.

You will be given:
  - The baseline YAML schema.
  - The list of (layout, task) pairs LEGAL for this robot.
  - The list of (layout, task) pairs PREVIOUSLY REJECTED by the LIVE
    isaaclab + cuRobo IK reachability check (this is the real thing —
    we boot the env, reset, read object world poses, and IK them).
    Avoid these.
  - The list of fields you ARE allowed to change.

Produce a JSON object of the form:
{
  "scenes": [
    {"name": "<short_kebab_slug>", "rationale": "<one sentence>", "overrides": {"<field>": <value>}}
  ]
}

Rules:
  1. Overrides must ONLY contain keys from the allowed whitelist.
  2. (layout, task) MUST be a LEGAL pair.
  3. (layout, task) MUST NOT be REJECTED.
  4. Generate EXACTLY {N_SCENES} entries with varied (layout, task).
  5. seed should be different integers in [0, 100].
  6. episode_length_s should be in [20.0, 35.0].
  7. PREFER tabletop tasks (counter, dining_table, stove) over floor tasks
     — floor objects in libero-5-5/8-8 tend to be out of arm reach.
  8. Output JSON only."""


def build_user_prompt(template, legal, banned) -> str:
    sample = []
    by_layout = {}
    for layout, task in sorted(legal):
        if (layout, task) in banned:
            continue
        if by_layout.get(layout, 0) < 5:
            sample.append((layout, task))
            by_layout[layout] = by_layout.get(layout, 0) + 1
    legal_str = "\n".join("  - layout=" + l + ", task=" + t for l, t in sample)
    banned_str = ("\n".join("  - layout=" + l + ", task=" + t for l, t in sorted(banned))
                  if banned else "  (none yet)")
    return (
        "# Baseline configuration:\n"
        "BEGIN_YAML\n" + yaml.dump(template, sort_keys=False) + "END_YAML\n\n"
        "# Allowed override fields:\n" + str(sorted(MUTABLE_FIELDS)) + "\n\n"
        "# Legal (layout, task) pairs (sample):\n" + legal_str + "\n\n"
        "# REJECTED (do not reuse):\n" + banned_str + "\n\n"
        "Generate exactly " + str(N_SCENES) + " scene variations as JSON."
    )


def validate_schema(name, overrides, legal, banned) -> list:
    errs = []
    bad = set(overrides) - MUTABLE_FIELDS
    if bad:
        errs.append(name + ": illegal keys " + str(bad))
    l = overrides.get("layout"); t = overrides.get("task")
    if l and t:
        if (l, t) not in legal:
            errs.append(name + f": ({l},{t}) not in CSV")
        if (l, t) in banned:
            errs.append(name + f": ({l},{t}) already rejected")
    return errs


def merge_and_save(base, overrides, path: Path):
    merged = dict(base); merged.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(merged, f, sort_keys=False, default_flow_style=False)


def run_reach(scene_yml: Path, report: Path) -> dict:
    """Run live v5 validator in lerobot-arena env."""
    report.parent.mkdir(parents=True, exist_ok=True)
    cmd = (
        "set +u && source " + str(HEADLESS_SH) + " && "
        "source " + str(LEROBOT_ENV_SH) + " && "
        "unset CUDA_VISIBLE_DEVICES && "
        "cd /mnt/robot/lw_benchhub && "
        + str(LEROBOT_PY) + " " + str(VALIDATOR)
        + " " + str(scene_yml)
        + " --threshold " + str(REACH_THRESHOLD)
        + " --report-json " + str(report)
    )
    print("  [v5 reach] cmd:", cmd[:200], "...")
    proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        print("  [v5 reach] ERROR rc=" + str(proc.returncode))
        print("  stdout(tail):", proc.stdout[-800:])
        print("  stderr(tail):", proc.stderr[-800:])
        # Write partial report so we can inspect later
        if not report.exists():
            report.write_text(json.dumps({
                "passed": False, "reach_ratio": 0.0,
                "error": True, "rc": proc.returncode,
                "stderr_tail": proc.stderr[-2000:],
                "stdout_tail": proc.stdout[-2000:],
            }, indent=2))
        try:
            return json.loads(report.read_text())
        except Exception:
            return {"passed": False, "reach_ratio": 0.0, "error": True}
    try:
        return json.loads(report.read_text())
    except Exception as e:
        print("  [v5 reach] PARSE ERROR:", e)
        return {"passed": False, "reach_ratio": 0.0, "error": True}


def ask_llm(client, model, template, legal, banned, attempt) -> list:
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{N_SCENES}", str(N_SCENES))},
        {"role": "user", "content": build_user_prompt(template, legal, banned)},
    ]
    resp = client.chat.completions.create(
        model=model, messages=msgs,
        response_format={"type": "json_object"},
        temperature=0.4 + 0.15 * attempt,
        timeout=90,
    )
    return json.loads(resp.choices[0].message.content)["scenes"]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REACH_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    template = load_template()
    legal = load_legal_combinations()
    banned: set = set()
    print("-> legal pairs:", len(legal))

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    for ri in range(1, MAX_ROUNDS + 1):
        print(f"\n===== Round {ri}/{MAX_ROUNDS} =====")
        print("  banned so far:", len(banned), "pairs")
        try:
            scenes = ask_llm(client, model, template, legal, banned, ri - 1)
        except Exception as e:
            print("  LLM failure:", type(e).__name__, str(e)[:200])
            continue

        errs = []
        for s in scenes:
            errs.extend(validate_schema(s["name"], s.get("overrides", {}), legal, banned))
        if errs:
            print("  schema errors, discard round:")
            for e in errs:
                print("   ", e)
            continue

        tentative = []
        for idx, s in enumerate(scenes, 1):
            p = OUTPUT_DIR / f"scene_variation_{idx}.yml"
            merge_and_save(template, s["overrides"], p)
            tentative.append((idx, s, p))

        round_failed = False
        reports = {}
        for idx, s, p in tentative:
            ov = s["overrides"]
            print(f"\n  [scene {idx}] {ov.get('layout')}/{ov.get('task')}")
            r = run_reach(p, REACH_REPORT_DIR / f"scene_{idx}_reach.json")
            reports[idx] = r
            rr = r.get("reach_ratio")
            rr_s = "nan" if rr is None or rr != rr else str(round(rr, 3))
            print(f"    n_obj={r.get('n_objects',0)} n_reach={r.get('n_reachable_either_arm',0)} "
                  f"ratio={rr_s} threshold={REACH_THRESHOLD} -> "
                  f"{'PASS' if r.get('passed') else 'FAIL'}")
            if not r.get("passed"):
                banned.add((ov["layout"], ov["task"]))
                round_failed = True

        if not round_failed:
            print(f"\n*** ALL {N_SCENES} scenes passed v5 LIVE reach gate in round {ri} ***")
            (LOG_ROOT / "final_manifest.json").write_text(json.dumps({
                "scenes": [{"idx": idx, "path": str(p),
                            "rationale": s.get("rationale", ""),
                            "overrides": s["overrides"],
                            "reach_ratio": reports[idx].get("reach_ratio"),
                            "n_objects": reports[idx].get("n_objects", 0),
                            "n_reachable_either_arm": reports[idx].get("n_reachable_either_arm", 0),
                            "robot_pose": reports[idx].get("robot_pose"),
                            "per_object_count": len(reports[idx].get("per_object", []))}
                           for idx, s, p in tentative],
                "rounds_used": ri,
                "banned": [list(b) for b in banned],
                "reach_threshold": REACH_THRESHOLD,
                "check_kind": "v5: live isaaclab env + cuRobo IK in lerobot-arena",
            }, indent=2, default=str))
            return 0

    print(f"\n!!! Exhausted {MAX_ROUNDS} rounds, {len(banned)} pairs banned.")
    # Save final manifest so we can inspect what was tried
    (LOG_ROOT / "final_manifest.json").write_text(json.dumps({
        "scenes": [], "rounds_used": MAX_ROUNDS,
        "banned": [list(b) for b in banned],
        "reach_threshold": REACH_THRESHOLD, "exhausted": True,
    }, indent=2, default=str))
    return 1


if __name__ == "__main__":
    sys.exit(main())
