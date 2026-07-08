#!/usr/bin/env python3
"""Standalone cuRobo config-load test for T3 #1 risk.
Validates that piper_curobo_left.yml + the generated double_piper_description.urdf
build an IKSolver. No Isaac Sim needed (pure cuRobo)."""
from __future__ import annotations
import math, os, sys
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

from curobo.types.base import TensorDeviceType
from curobo.util_file import load_yaml
from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig

CUROBO_CFG_DIR = "/mnt/robot/stage4_flywheel/curobo"

def test_arm(arm: str):
    yml = f"piper_curobo_{arm}.yml"
    print(f"\n===== testing {yml} =====")
    cfg_dict = load_yaml(f"{CUROBO_CFG_DIR}/{yml}")
    print("  top-level keys:", list(cfg_dict.keys()))
    rc = cfg_dict.get("robot_cfg", {})
    print("  robot_cfg keys:", list(rc.keys()) if isinstance(rc, dict) else type(rc))
    # cspace may be under robot_cfg or at top level; find it for logging.
    cspace = rc.get("cspace") if isinstance(rc, dict) else None
    if cspace:
        print("  cspace.joint_names:", cspace.get("joint_names"))
    kin = rc.get("kinematics", {}) if isinstance(rc, dict) else {}
    print("  base_link:", kin.get("base_link"), "| ee_link:", kin.get("ee_link"))
    tdtype = TensorDeviceType()
    ik_cfg = IKSolverConfig.load_from_robot_config(
        cfg_dict, None,
        rotation_threshold=math.pi,
        position_threshold=0.01,
        num_seeds=16,
        self_collision_check=False,
        self_collision_opt=False,
        tensor_args=tdtype,
        use_cuda_graph=False,
    )
    solver = IKSolver(ik_cfg)
    print(f"  IKSolver built OK for {arm} arm")
    import torch
    from curobo.types.math import Pose
    pos = torch.tensor([[0.3, 0.15, 0.4]], device=tdtype.device, dtype=tdtype.dtype)
    rot = torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=tdtype.device, dtype=tdtype.dtype)
    result = solver.solve_single(Pose(position=pos, quaternion=rot))
    err = result.position_error[0].cpu().item()
    print(f"  IK smoke: target [0.3,0.15,0.4] -> position_error={err:.4f} m")
    return True

if __name__ == "__main__":
    ok = True
    for arm in ("left", "right"):
        try:
            test_arm(arm)
        except Exception as e:
            ok = False
            print(f"  FAILED {arm}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print("\nCUROBO_CONFIG_TEST:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
