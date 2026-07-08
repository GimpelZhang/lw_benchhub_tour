"""Pure-IK arm-selection reach gate for the DoublePiper kitchen PnP pipeline.

Takes a live Isaac Lab environment (already booted by the pipeline) and selects
whether the left or right arm should manipulate each target object. The math is
adapted from ``validate_scene_objects_reach_v5.py``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv


ARM_LATERAL_OFFSET = 0.15  # ±0.15 m laterally from robot torso to each arm base
POSITION_THRESHOLD = 0.01  # 1 cm IK position residual to be considered "reached"
DEFAULT_NUM_SEEDS = 16


def _world_to_arm_local(
    obj_world: np.ndarray,
    robot_pos_world: np.ndarray,
    robot_yaw: float,
    arm_side: str,
) -> tuple[np.ndarray, list[float]]:
    """Transform a world XYZ into the arm-base local frame.

    The robot torso has world position ``robot_pos_world`` and yaws by
    ``robot_yaw`` around +Z. The arm base sits at torso + R_yaw @ (0, ±lateral, 0).
    Returns ``R_yaw.T @ (obj_world - arm_base_world)`` and the arm base world pos.
    """
    cy, sy = math.cos(robot_yaw), math.sin(robot_yaw)
    R = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
    lateral = ARM_LATERAL_OFFSET if arm_side == "left" else -ARM_LATERAL_OFFSET
    arm_base_world = np.asarray(robot_pos_world) + R @ np.array([0.0, lateral, 0.0])
    return R.T @ (np.asarray(obj_world) - arm_base_world), arm_base_world.tolist()


def _build_ik_solver(robot_config_file: str, curobo_config_path: str, num_seeds: int):
    """Build a cuRobo IK solver from a single-arm Piper config."""
    import torch
    from curobo.types.base import TensorDeviceType
    from curobo.util_file import load_yaml
    from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig

    tdtype = TensorDeviceType()
    cfg_dict = load_yaml(f"{curobo_config_path}/{robot_config_file}")
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


def _solve_single(ik_solver, tdtype, xyz_local: list[float]) -> float:
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


def _get_robot_root_pose(env: ManagerBasedEnv, env_id: int = 0) -> tuple[np.ndarray, float]:
    """Read the robot torso position and yaw from the live articulation."""
    robot = env.scene["robot"]
    state = robot.data.root_state_w[env_id].detach().cpu().numpy()
    px, py, pz, qw, qx, qy, qz = state[:7]
    yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
    return np.array([px, py, pz], dtype=float), yaw


def select_arm_per_object(
    env: ManagerBasedEnv,
    target_objects: list[str],
    curobo_config_path: str,
    env_id: int = 0,
    num_seeds: int = DEFAULT_NUM_SEEDS,
) -> dict[str, str | None]:
    """Run per-object IK for both arms and return the selected arm per object.

    Returns:
        Mapping from object name to ``"left"``, ``"right"``, or ``None``
        (unreachable). When both arms reach, the arm with the smaller residual
        is chosen.
    """
    robot_pos_world, robot_yaw = _get_robot_root_pose(env, env_id)
    left_solver, left_tdtype = _build_ik_solver("piper_curobo_left.yml", curobo_config_path, num_seeds)
    right_solver, right_tdtype = _build_ik_solver("piper_curobo_right.yml", curobo_config_path, num_seeds)

    assignment: dict[str, str | None] = {}
    rigid_objects = env.scene.rigid_objects

    for obj_name in target_objects:
        obj = rigid_objects[obj_name]
        obj_world = obj.data.root_pos_w[env_id].detach().cpu().numpy()

        local_l, _ = _world_to_arm_local(obj_world, robot_pos_world, robot_yaw, "left")
        local_r, _ = _world_to_arm_local(obj_world, robot_pos_world, robot_yaw, "right")

        err_l = _solve_single(left_solver, left_tdtype, local_l.tolist())
        err_r = _solve_single(right_solver, right_tdtype, local_r.tolist())

        reach_l = (not math.isnan(err_l)) and err_l < POSITION_THRESHOLD
        reach_r = (not math.isnan(err_r)) and err_r < POSITION_THRESHOLD

        if reach_l and reach_r:
            arm = "left" if err_l <= err_r else "right"
        elif reach_l:
            arm = "left"
        elif reach_r:
            arm = "right"
        else:
            arm = None

        assignment[obj_name] = arm

    return assignment
