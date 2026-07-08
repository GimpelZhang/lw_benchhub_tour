import json, re, pathlib
out = pathlib.Path("/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_run")
log = pathlib.Path("/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_eval.log")
m = {"success_rate": None, "avg_episode_length": None, "error_summary": None}
if (out / "eval_metrics.json").is_file():
    d = json.loads((out / "eval_metrics.json").read_text())
    raw = d.get("success_rate", 0.0)
    m["success_rate"] = raw / 100.0 if isinstance(raw, (int, float)) and raw > 1.0 else float(raw)
    m["avg_episode_length"] = d.get("avg_episode_length")
else:
    t = log.read_text(errors="ignore") if log.is_file() else ""
    for line in reversed(t.splitlines()):
        mm = re.search(r"running_success_rate[=:]\s*([0-9.]+)", line)
        if mm:
            m["success_rate"] = float(mm.group(1)) / 100.0; break
    if m["success_rate"] is None:
        if re.search(r"RuntimeError:\s*The size of tensor a \((\d+)\) must match the size of tensor b \((\d+)\)", t):
            m["error_summary"] = "obs-dim mismatch (embodiment OOD)"
        elif re.search(r"gym\.error\.NameNotFound|NameNotFound", t):
            m["error_summary"] = "gym.NameNotFound"
        elif re.search(r"Traceback \(most recent call last\):", t):
            err = next((re.match(r"^\s*([A-Za-z][A-Za-z0-9_.]*Error.*)", l).group(1).strip()
                        for l in reversed(t.splitlines()) if re.match(r"^\s*[A-Za-z].*Error", l)), "unhandled traceback")
            m["error_summary"] = err[:160]
rc = "N/A"
if log.is_file():
    mm = re.search(r"^EXIT_CODE:\s*(\d+)", log.read_text(errors="ignore"), re.MULTILINE)
    if mm: rc = int(mm.group(1))
report = {"exit_code": rc, "success_rate": m["success_rate"],
          "success_rate_pct": f"{m['success_rate']:.2%}" if isinstance(m["success_rate"], float) else None,
          "avg_episode_length": m["avg_episode_length"], "error_summary": m["error_summary"]}
pathlib.Path("/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_metrics.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
