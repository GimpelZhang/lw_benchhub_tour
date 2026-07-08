#!/usr/bin/env python3
"""Phase 2 Task 2.3 — add collision_spheres to cuRobo yml + raise collision_activation_distance.

Modifies:
  1. piper_curobo_left.yml + piper_curobo_right.yml: replace `collision_spheres: {}` with gripper
     sphere definitions (gripper_base, link7, link8). The mesh_link_names are kept (combined effect).
  2. doublepiper_kitchen_pnp_cfg.py: set motion_planner.collision_activation_distance = 0.07 in
     __post_init__ (>=0.06 to INCREASE the safety margin — the patch's suggested 0.02-0.04 is WRONG:
     default is 0.05, so 0.02-0.04 TIGHTENS the margin, wrong direction. See §4.3.1 correction).

NOTE: §2 pre-check found gripper force = 0N during hover reach. §5.5 already proved mesh collision
does NOT fix the push. collision_spheres are a coarser approximation and likely also ineffective.
Apply only if Gate A fails AND descend (Task 2.2) alone doesn't fix the bowl displacement.

Idempotent: no-op if already patched. Backs up yml to .bak_patch01.
"""
import shutil, sys
from pathlib import Path

LEFT = Path("/mnt/robot/stage4_flywheel/curobo/piper_curobo_left.yml")
RIGHT = Path("/mnt/robot/stage4_flywheel/curobo/piper_curobo_right.yml")

# Sphere definitions (from plan §4.3.2; UNVERIFIED — must be checked against actual URDF link frames
# before relying on them. These are placeholder geometry for the gripper links.)
SPHERES_LEFT = """    collision_spheres:
      gripper_base_l:
        - {"center": [0.0, 0.0, 0.02], "radius": 0.035}
        - {"center": [0.0, 0.0, 0.05], "radius": 0.03}
      link7_l:
        - {"center": [0.0, 0.01, 0.04], "radius": 0.015}
      link8_l:
        - {"center": [0.0, -0.01, 0.04], "radius": 0.015}
"""
SPHERES_RIGHT = """    collision_spheres:
      gripper_base_r:
        - {"center": [0.0, 0.0, 0.02], "radius": 0.035}
        - {"center": [0.0, 0.0, 0.05], "radius": 0.03}
      link7_r:
        - {"center": [0.0, 0.01, 0.04], "radius": 0.015}
      link8_r:
        - {"center": [0.0, -0.01, 0.04], "radius": 0.015}
"""

for path, spheres, arm in [(LEFT, SPHERES_LEFT, "left"), (RIGHT, SPHERES_RIGHT, "right")]:
    src = path.read_text()
    if "collision_spheres:\n      gripper_base_" in src:
        print(f"already patched ({arm})"); continue
    bak = path.with_suffix(".yml.bak_patch01")
    if not bak.exists():
        shutil.copyfile(path, bak)
    old = "    collision_spheres: {}\n"
    assert src.count(old) == 1, f"({arm}) collision_spheres anchor count={src.count(old)}"
    src = src.replace(old, spheres)
    path.write_text(src)
    print(f"[{arm}] collision_spheres added")

# collision_activation_distance: try to set in doublepiper_kitchen_pnp_cfg.py __post_init__
cfg_path = Path("/mnt/robot/AutoDataGen/source/autosim_examples/autosim_examples/autosim/pipelines/doublepiper_kitchen_pnp/doublepiper_kitchen_pnp_cfg.py")
if cfg_path.exists():
    cfg_src = cfg_path.read_text()
    if "collision_activation_distance = 0.07" in cfg_src:
        print("cfg already has collision_activation_distance=0.07")
    else:
        bak = cfg_path.with_suffix(".py.bak_patch01")
        if not bak.exists():
            shutil.copyfile(cfg_path, bak)
        # Find __post_init__ and append the override; if no __post_init__, add one.
        if "def __post_init__" in cfg_src:
            old_pi = "    def __post_init__(self) -> None:\n"
            new_pi = ("    def __post_init__(self) -> None:\n"
                      "        # Phase 2: raise collision_activation_distance (default 0.05 -> 0.07) to increase\n"
                      "        # the cuRobo safety margin. >=0.06 INCREASES the margin (patch's 0.02-0.04 is WRONG).\n"
                      "        try:\n"
                      "            self.motion_planner.collision_activation_distance = 0.07\n"
                      "        except Exception:\n"
                      "            pass\n")
            if cfg_src.count(old_pi) == 1:
                cfg_src = cfg_src.replace(old_pi, new_pi)
                cfg_path.write_text(cfg_src)
                print("[cfg] collision_activation_distance=0.07 added to __post_init__")
            else:
                print(f"[cfg] __post_init__ anchor count={cfg_src.count(old_pi)} (skip — set manually)")
        else:
            print("[cfg] no __post_init__ (skip — set collision_activation_distance=0.07 manually)")
else:
    print(f"cfg not found: {cfg_path}")

print("PHASE 2 TASK 2.3 PATCH APPLIED")
