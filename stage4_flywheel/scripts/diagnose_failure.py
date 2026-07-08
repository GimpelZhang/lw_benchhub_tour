from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

def parse_success_rate(p: Path) -> float | None:
    if not p.is_file(): return None
    raw = json.loads(p.read_text()).get("success_rate")
    return raw / 100.0 if isinstance(raw, (int, float)) and raw > 1.0 else float(raw) if isinstance(raw, (int, float)) else None

def parse_exit_code(p: Path) -> int | None:
    if not p.is_file(): return None
    m = re.search(r"EXIT_CODE:\s*(-?\d+)", p.read_text(errors="ignore"))
    return int(m.group(1)) if m else None

def classify(metrics_path: Path, log_path: Path, reach_path: Path, bowl="akita_black_bowl") -> dict[str, Any]:
    diag = {"success_rate": parse_success_rate(metrics_path), "exit_code": parse_exit_code(log_path),
            "mode": "unknown", "signals": []}
    log = log_path.read_text(errors="ignore") if log_path.is_file() else ""
    rr = json.loads(reach_path.read_text()) if reach_path.is_file() else {}
    bowl_reach = next((o for o in rr.get("per_object", []) if bowl in o.get("name", "")), None)
    avg_len = json.loads(metrics_path.read_text()).get("avg_episode_length") if metrics_path.is_file() else None
    sr = diag["success_rate"]
    # Only classify by log keywords if success_rate is unavailable (eval didn't produce a rate).
    if sr is None:
        if any(s in log for s in ["size mismatch", "mat1 and mat2 shapes", "observation dimension"]):
            diag["mode"] = "obs-dim-mismatch"; diag["signals"].append("tensor/shape error in log"); return diag
        if "NameNotFound" in log or "not found in gym registry" in log:
            diag["mode"] = "gym.NameNotFound"; diag["signals"].append("gym NameNotFound in log"); return diag
    if sr is not None and sr < 0.05:
        if bowl_reach and not bowl_reach.get("either_arm_reach", True):
            diag["mode"] = "reach-failure"; diag["signals"].append(f"{bowl} not reachable (IK residual > 1cm)")
        elif avg_len is not None and avg_len < 50:
            diag["mode"] = "reach-failure"; diag["signals"].append("episode terminates early (<50 steps)")
        else:
            diag["mode"] = "grasp-failure"; diag["signals"].append("arm reaches object but success checker never fires")
    elif sr is not None and 0.05 <= sr < 1.0:
        diag["mode"] = "transport-failure"; diag["signals"].append("some successes but object dropped during transport")
    else:
        diag["mode"] = "unhandled traceback"; diag["signals"].append("success_rate missing; inspect log manually")
    return diag

if __name__ == "__main__":
    base = Path("/mnt/robot/stage4_flywheel/metrics/baseline")
    d = classify(base / "hard_scene_metrics.json",
                 base / "hard_scene_eval.log", base / "reach_report.json")
    Path("/mnt/robot/stage4_flywheel/metrics/baseline/diagnosis.json").write_text(json.dumps(d, indent=2))
    print(json.dumps(d, indent=2))
