#!/usr/bin/env python3
"""T3 §14 checklist: verify DoublePiper joint/link/camera names against the live USD.
Boots the env ONCE (via export_env_for_envhub) and prints the names T3 cuRobo configs depend on.
Run this BEFORE finalizing piper_curobo_{left,right}.yml base_link/ee_link/joint_names."""
from __future__ import annotations
import json, os
from pathlib import Path
os.environ.setdefault("ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT", "1")
os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "Y")
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

from isaaclab.app import AppLauncher  # noqa: F401
from lw_benchhub.utils.envhub_utils import export_env_for_envhub

YML = os.environ.get("DP_VERIFY_YML", "/mnt/robot/lw_benchhub/configs/envhub/example.yml")
raw_env, environment, task, render_mode, episode_length, app_launcher = export_env_for_envhub(config_path=YML)
env = raw_env
env.reset()

scene = env.scene
art = getattr(scene, "articulations", None) or getattr(scene, "_articulations", {})
robot = None
for name, a in art.items():
    if "piper" in name.lower() or "robot" in name.lower():
        robot = a; print(f"ROBOT_ARTICULATION_NAME: {name}"); break
if robot is None:
    robot = next(iter(art.values())); print(f"ROBOT_ARTICULATION_NAME (fallback): {next(iter(art))}")

print("JOINT_NAMES:", robot.data.joint_names)
print("BODY_NAMES:", robot.data.body_names)
print("ACTION_TERMS:", list(env.action_manager.action_terms.keys()) if hasattr(env, "action_manager") else "n/a")
for term_name in ("left_arm_action", "right_arm_action"):
    try:
        t = env.action_manager.get_term(term_name)
        print(f"  {term_name}.cfg.joint_names:", t.cfg.joint_names)
        print(f"  {term_name}.cfg.scale:", getattr(t.cfg, "scale", None))
        print(f"  {term_name}.cfg.use_default_offset:", getattr(t.cfg, "use_default_offset", None))
    except Exception as e:
        print(f"  {term_name}: ERROR {e}")
sensors = getattr(scene, "sensors", {}) or {}
print("SENSORS:", list(sensors.keys()))
if "first_person_camera" in sensors:
    cam = sensors["first_person_camera"]
    out = cam.data.output
    print("  first_person_camera output keys:", list(out.keys()) if hasattr(out, "keys") else type(out))
    rgb = out["rgb"]
    print("  rgb shape/dtype:", tuple(rgb.shape), rgb.dtype)

# save to json
Path("/mnt/robot/stage4_flywheel/metrics/doublepiper_joints.json").write_text(json.dumps({
    "joint_names": list(robot.data.joint_names),
    "body_names": list(robot.data.body_names),
    "sensors": list(sensors.keys()),
}, indent=2))
print("SAVED /mnt/robot/stage4_flywheel/metrics/doublepiper_joints.json")
try:
    app_launcher.close()
except Exception:
    pass
