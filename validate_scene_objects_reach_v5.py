#!/usr/bin/env python3
"""Stage 2 v5 — LIVE isaaclab + cuRobo scene-content reachability gate.

This is what v3/v4 wanted but couldn't deliver: instead of static AST
extraction (v3) or CSV-only world-pose math (v4), v5 boots the SAME
lw_benchhub task env that SmolVLA will be evaluated on, calls env.reset(),
reads each rigid_object's `data.root_pos_w` and the robot's actual world
pose from `data.root_state_w`, then runs cuRobo IK per object per arm —
ALL inside the lerobot-arena env.

Pre-requisites (one-time per machine, handled in CLAUDE.md §16 setup):
  - lerobot-arena has env-local conda cuda-toolkit 12.8 (matches torch cu128)
  - cuRobo compiled and installed inside lerobot-arena
  - lw_benchhub outer namespace stub fixed (re-exports inner package)
  - source /mnt/robot/lerobot_arena_curobo_env.sh AFTER conda activate lerobot-arena

USAGE
  python validate_scene_objects_reach_v5.py <scene_yml> \
      [--threshold R] [--num-seeds N] [--report-json PATH]

Exit 0 = passed (or no rigid objects to check); 1 = failed reach gate;
Exit >= 2 = bug / setup error.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# AppLauncher MUST come before anything that touches isaaclab internals
# ---------------------------------------------------------------------------
os.environ.setdefault("ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT", "1")
os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "Y")
# isaacsim ships its own setuptools_scm in pip_prebundle/. Setting this
# env var BEFORE either isaaclab or curobo import keeps curobo's import-time
# setuptools_scm.get_version() happy if it fires. (We additionally renamed
# curobo's .git -> .git_disabled so curobo skips setuptools_scm entirely
# and reads importlib.metadata.version("nvidia_curobo") instead.)
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

PIPER_CUROBO_YML = "/mnt/robot/piper_curobo.yml"
ARM_LATERAL_OFFSET = 0.15  # ±0.15 m laterally from robot torso to each arm base

DEFAULT_NUM_SEEDS = 16
DEFAULT_THRESHOLD = 0.50
POSITION_THRESHOLD = 0.01  # 1 cm IK position residual to be considered "reached"


def _ensure_env() -> None:
    """Fail loudly if curobo / numpy lock / cuda env aren't in shape."""
    import numpy
    if numpy.__version__ != "1.26.0":
        raise RuntimeError(
            f"numpy version drift: {numpy.__version__} != 1.26.0. "
            "Run: pip install --no-deps numpy==1.26.0"
        )


def _world_to_arm_local(obj_world, robot_pos_world, robot_yaw, arm_side: str):
    """Transform a world XYZ into the arm-base local frame.

    The robot torso has world position robot_pos_world and yaws by robot_yaw
    around +Z. The arm base sits at torso + R_yaw @ (0, ±lateral, 0).
    We return R_yaw.T @ (obj_world - arm_base_world).
    """
    import numpy as np
    cy, sy = math.cos(robot_yaw), math.sin(robot_yaw)
    R = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
    lateral = ARM_LATERAL_OFFSET if arm_side == "left" else -ARM_LATERAL_OFFSET
    arm_base_world = np.asarray(robot_pos_world) + R @ np.array([0.0, lateral, 0.0])
    return R.T @ (np.asarray(obj_world) - arm_base_world), arm_base_world.tolist()


def _build_ik_solver(num_seeds: int):
    """Build a cuRobo IK solver from the single-arm piper config (same as v3/v4)."""
    import torch
    from curobo.types.base import TensorDeviceType
    from curobo.util_file import load_yaml
    from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig

    tdtype = TensorDeviceType()
    cfg_dict = load_yaml(PIPER_CUROBO_YML)
    ik_cfg = IKSolverConfig.load_from_robot_config(
        cfg_dict,
        None,
        rotation_threshold=math.pi,  # position-only IK; rotation irrelevant
        position_threshold=POSITION_THRESHOLD,
        num_seeds=num_seeds,
        self_collision_check=False,
        self_collision_opt=False,
        tensor_args=tdtype,
        use_cuda_graph=False,
    )
    return IKSolver(ik_cfg), tdtype


def _solve_single(ik_solver, tdtype, xyz_local):
    """Solve position-only IK at a point; return residual position error (m) or NaN."""
    import torch
    from curobo.types.math import Pose
    pos = torch.tensor([xyz_local], device=tdtype.device, dtype=tdtype.dtype)
    rot = torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=tdtype.device, dtype=tdtype.dtype)
    target = Pose(position=pos, quaternion=rot)
    result = ik_solver.solve_single(target)
    try:
        err = result.position_error[0].cpu().item()
    except Exception:
        err = float("nan")
    return err


def _boot_env(config_path: Path):
    """Run lw_benchhub's export_env_for_envhub, then reset, then return raw_env+app.

    Retries on transient lightwheel_sdk SSL errors (api.lightwheel.net is
    occasionally flaky; v4 scene 3 was the canary).
    """
    from isaaclab.app import AppLauncher  # noqa: F401 — keep import for ordering
    from lw_benchhub.utils.envhub_utils import export_env_for_envhub
    import time

    last_exc = None
    for attempt in range(3):
        try:
            raw_env, environment, task, render_mode, episode_length, app_launcher = export_env_for_envhub(
                config_path=str(config_path)
            )
            # First reset = full scene generation
            raw_env.reset()
            return raw_env, app_launcher
        except Exception as e:
            msg = str(e)
            # Only retry on SSL/connection errors from lightwheel_sdk
            transient = any(s in msg for s in (
                "SSLError", "SSLEOFError", "EOF occurred", "Max retries exceeded",
                "Connection aborted", "TimeoutError", "Read timed out",
            ))
            if not transient or attempt == 2:
                raise
            last_exc = e
            print(f"[v5] transient lightwheel/SSL error on boot attempt {attempt + 1}, "
                  f"retrying in 5s: {msg[:160]}", flush=True)
            time.sleep(5)
    raise last_exc


def _dump_scene_poses(raw_env):
    """Pull rigid object world positions + robot world pose from the live env."""
    import torch
    # 1) rigid objects
    objects = []
    scene = raw_env.scene
    # The scene has both rigid_objects (dict) and articulations (dict).
    rigid_dict = getattr(scene, "rigid_objects", None) or getattr(scene, "_rigid_objects", {})
    for name, ro in rigid_dict.items():
        try:
            pos_w = ro.data.root_pos_w[0].detach().cpu().numpy().tolist()
            objects.append({"name": name, "world_pos": pos_w})
        except Exception as e:
            objects.append({"name": name, "world_pos": None, "_error": str(e)})

    # 2) robot world pose — DoublePiper has a single root articulation
    robot_pose = None
    art_dict = getattr(scene, "articulations", None) or getattr(scene, "_articulations", {})
    for name, art in art_dict.items():
        if "piper" in name.lower() or "robot" in name.lower():
            try:
                state = art.data.root_state_w[0].detach().cpu().numpy().tolist()
                # state: [px, py, pz, qw, qx, qy, qz, ...] — take first 7
                px, py, pz, qw, qx, qy, qz = state[:7]
                # convert quaternion → yaw around +Z
                # yaw = atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
                yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
                robot_pose = {
                    "name": name,
                    "world_pos": [px, py, pz],
                    "world_quat_wxyz": [qw, qx, qy, qz],
                    "yaw_rad": yaw,
                }
                break
            except Exception as e:
                robot_pose = {"name": name, "_error": str(e)}
                break
    return objects, robot_pose


def _evaluate(objects, robot_pose, ik_solver, tdtype):
    """Run per-object IK in each arm frame and compile a report."""
    import numpy as np
    if robot_pose is None or "_error" in (robot_pose or {}):
        return [], 0, 0, float("nan"), "no robot pose in scene"

    rp = robot_pose["world_pos"]
    yaw = robot_pose["yaw_rad"]
    per_obj = []
    n_reach = 0
    n_total = 0
    for obj in objects:
        if obj.get("world_pos") is None:
            per_obj.append({**obj, "left_err": None, "right_err": None, "either_arm_reach": False})
            continue
        n_total += 1
        ow = np.asarray(obj["world_pos"], dtype=float)
        local_l, arm_base_l = _world_to_arm_local(ow, rp, yaw, "left")
        local_r, arm_base_r = _world_to_arm_local(ow, rp, yaw, "right")
        err_l = _solve_single(ik_solver, tdtype, local_l.tolist())
        err_r = _solve_single(ik_solver, tdtype, local_r.tolist())
        reach_l = (not math.isnan(err_l)) and err_l < POSITION_THRESHOLD
        reach_r = (not math.isnan(err_r)) and err_r < POSITION_THRESHOLD
        either = reach_l or reach_r
        if either:
            n_reach += 1
        per_obj.append({
            "name": obj["name"],
            "world_pos": obj["world_pos"],
            "arm_base_left_world": arm_base_l,
            "arm_base_right_world": arm_base_r,
            "local_left": local_l.tolist(),
            "local_right": local_r.tolist(),
            "left_err": None if math.isnan(err_l) else err_l,
            "right_err": None if math.isnan(err_r) else err_r,
            "either_arm_reach": either,
        })
    ratio = float("nan") if n_total == 0 else (n_reach / n_total)
    return per_obj, n_total, n_reach, ratio, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("scene_yml", type=Path)
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    p.add_argument("--num-seeds", type=int, default=DEFAULT_NUM_SEEDS)
    p.add_argument("--report-json", type=Path, default=None)
    args = p.parse_args()

    try:
        _ensure_env()
    except Exception as e:
        print("[v5] env precheck FAILED:", e)
        return 2

    report: dict = {
        "scene_yml": str(args.scene_yml),
        "threshold": args.threshold,
        "passed": False,
        "n_objects": 0,
        "n_reachable_either_arm": 0,
        "reach_ratio": None,
        "per_object": [],
        "robot_pose": None,
        "check_kind": "v5-live-isaaclab+curobo-ik",
    }

    try:
        # Read minimal YAML metadata for the report
        import yaml
        cfg = yaml.safe_load(Path(args.scene_yml).read_text())
        report["layout"] = cfg.get("layout")
        report["task"] = cfg.get("task")
        report["robot"] = cfg.get("robot")
        report["seed"] = cfg.get("seed")

        # ORDERING: boot isaaclab FIRST (it owns the kit GPU context), THEN
        # build cuRobo IK (which initializes its own CUDA tensors). Reverse
        # ordering tends to crash with cudaErrorIllegalAddress when isaaclab
        # later tries to allocate USD-backed textures.
        print("[v5] booting lw_benchhub env from", args.scene_yml, flush=True)
        raw_env, app_launcher = _boot_env(args.scene_yml)
        try:
            print("[v5] env booted; dumping scene poses...", flush=True)
            objects, robot_pose = _dump_scene_poses(raw_env)
            report["robot_pose"] = robot_pose
            print(f"[v5] dumped {len(objects)} rigid objects, robot pose={robot_pose}", flush=True)

            print("[v5] building cuRobo IK solver...", flush=True)
            ik_solver, tdtype = _build_ik_solver(num_seeds=args.num_seeds)
            print("[v5] cuRobo IK solver ready", flush=True)

            per_obj, n_total, n_reach, ratio, err = _evaluate(objects, robot_pose, ik_solver, tdtype)
            report["per_object"] = per_obj
            report["n_objects"] = n_total
            report["n_reachable_either_arm"] = n_reach
            report["reach_ratio"] = None if math.isnan(ratio) else ratio
            if err:
                report["error_note"] = err
            # Empty rigid_objects → pass-by-default (consistent with v3/v4)
            if n_total == 0:
                report["passed"] = True
            else:
                report["passed"] = (ratio >= args.threshold)
        finally:
            try:
                raw_env.close()
            except Exception:
                pass
            try:
                app_launcher.close()
            except Exception:
                pass
    except Exception:
        report["error_note"] = traceback.format_exc()
        report["passed"] = False
        if args.report_json:
            args.report_json.parent.mkdir(parents=True, exist_ok=True)
            args.report_json.write_text(json.dumps(report, indent=2))
        print("[v5] FATAL during validation:", file=sys.stderr)
        print(report["error_note"], file=sys.stderr)
        return 2

    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2))
    print(f"[v5] n_obj={report['n_objects']} n_reach={report['n_reachable_either_arm']} "
          f"ratio={report['reach_ratio']} threshold={args.threshold} -> "
          f"{'PASS' if report['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
