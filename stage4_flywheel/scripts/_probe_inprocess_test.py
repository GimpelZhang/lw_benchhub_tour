#!/usr/bin/env python3
"""Test whether mutating context.seed + env.reset() re-samples the bowl pose in ONE boot."""
from __future__ import annotations
import json, os
from pathlib import Path
os.environ.setdefault("ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT", "1")
os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "Y")
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

from isaaclab.app import AppLauncher  # noqa: F401
from lw_benchhub.utils.envhub_utils import export_env_for_envhub
# Do NOT import lw_benchhub.core.context at top level — context.py imports
# isaaclab.utils.dataclass at module level -> pxr crash before AppLauncher exists.

BASE_YML = "/mnt/robot/lw_benchhub/configs/envhub/example.yml"
raw_env, environment, task, render_mode, episode_length, app_launcher = export_env_for_envhub(config_path=BASE_YML)
env = raw_env
from lw_benchhub.core.context import get_context  # safe: AppLauncher now exists
ctx = get_context()

def read_bowl():
    rigid = getattr(env.scene, "rigid_objects", None) or getattr(env.scene, "_rigid_objects", {})
    return rigid["akita_black_bowl"].data.root_pos_w[0].detach().cpu().numpy().tolist()

results = []
for seed in [42, 0, 10, 99]:
    ctx.seed = seed
    env.reset()
    bowl = read_bowl()
    results.append({"seed": seed, "bowl_world": bowl})
    print(f"seed {seed}: bowl={bowl}", flush=True)

poses = [r["bowl_world"] for r in results]
unique = len(set(tuple(p) for p in poses))
print(f"UNIQUE_POSES={unique}/4", flush=True)
if unique >= 3:
    print("INPROCESS_RESEED_WORKS", flush=True)
else:
    print("INPROCESS_RESEED_DOES_NOT_VARY", flush=True)
Path("/mnt/robot/stage4_flywheel/metrics/baseline/_inprocess_test.json").write_text(
    json.dumps(results + [{"unique_poses": unique}], indent=2))
try:
    app_launcher.close()
except Exception:
    pass
