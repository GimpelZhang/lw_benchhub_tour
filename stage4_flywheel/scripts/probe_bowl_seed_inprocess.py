#!/usr/bin/env python3
"""FAST in-process seed sweep: boot Isaac Sim ONCE, mutate context.seed + reset per seed.
~15-20x faster than the subprocess approach (one boot total). Only valid if ctx.seed mutation
re-samples the bowl pose (verified by _probe_inprocess_test.py)."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
os.environ.setdefault("ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT", "1")
os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "Y")
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

from isaaclab.app import AppLauncher  # noqa: F401
from lw_benchhub.utils.envhub_utils import export_env_for_envhub

BASE_YML = "/mnt/robot/lw_benchhub/configs/envhub/example.yml"
N = int(os.environ.get("PROBE_N_SEEDS", "64"))

raw_env, environment, task, render_mode, episode_length, app_launcher = export_env_for_envhub(config_path=BASE_YML)
env = raw_env
from lw_benchhub.core.context import get_context  # safe: AppLauncher exists
ctx = get_context()

rigid = getattr(env.scene, "rigid_objects", None) or getattr(env.scene, "_rigid_objects", {})
art = getattr(env.scene, "articulations", None) or getattr(env.scene, "_articulations", {})
bowl_obj = rigid["akita_black_bowl"]

def read_robot_pos():
    for name, a in art.items():
        if "piper" in name.lower() or "robot" in name.lower():
            return a.data.root_state_w[0, :3].detach().cpu().numpy()
    for name, a in art.items():
        return a.data.root_state_w[0, :3].detach().cpu().numpy()

candidates = []
robot_base_anchor = None
for seed in range(N):
    ctx.seed = seed
    env.reset()
    bowl = bowl_obj.data.root_pos_w[0].detach().cpu().numpy()
    rpos = read_robot_pos()
    dist = float(((bowl - rpos) ** 2).sum() ** 0.5)
    candidates.append({"seed": seed, "bowl_world": bowl.tolist(),
                       "robot_world": rpos.tolist(), "dist_to_robot": dist})
    if seed == 0:
        robot_base_anchor = rpos.tolist()
    print(f"seed {seed:3d}: dist={dist:.3f} bowl={[round(x,3) for x in bowl]}", flush=True)

best = max(candidates, key=lambda x: x["dist_to_robot"])
out = Path("/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json")
out.write_text(json.dumps({"robot_base_anchor": robot_base_anchor,
                           "best_seed": best["seed"], "best": best,
                           "all": candidates, "n_probed": len(candidates),
                           "method": "inprocess"}, indent=2), encoding="utf-8")
print(json.dumps({"best_seed": best["seed"], "dist_to_robot": best["dist_to_robot"],
                  "n_probed": len(candidates), "method": "inprocess"}, indent=2))
try:
    app_launcher.close()
except Exception:
    pass
