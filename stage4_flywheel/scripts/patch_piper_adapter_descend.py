#!/usr/bin/env python3
"""Phase 2 Task 2.1 — register `descend` in PiperAbsAdapter.

Adds:
  - self._ik_solvers cache (lazy cuRobo IKSolver per arm)
  - _get_ik_solver(arm): lazy-build cuRobo IKSolver from piper_curobo_{arm}.yml (NOT PiperPinocchioIK stub)
  - _apply_descend(target_joint_pos, env): write 5-DoF cuRobo IK solution to active arm, gripper open

cuRobo cspace order [joint1,2,3,5,6] == action term joint order, so the 5-D IK solution maps directly
to action[0:5] (left) / action[5:10] (right) with the same offset/scale as _apply_reach.

Idempotent: no-op if already patched. Backs up to .bak_patch01.
"""
import shutil, sys
from pathlib import Path

PATH = Path("/mnt/robot/AutoDataGen/source/autosim_examples/autosim_examples/autosim/action_adapters/piper_adapter.py")
src = PATH.read_text()

if "_apply_descend" in src:
    print("ALREADY PATCHED — no-op."); sys.exit(0)

BAK = PATH.with_suffix(".py.bak_patch01")
if not BAK.exists():
    shutil.copyfile(PATH, BAK)

# 1: add _ik_solvers cache in __init__ (after self._current_arm)
old1 = "        self._arm_assignment: dict[str, str] = {}\n        self._current_arm: str | None = None\n"
new1 = ("        self._arm_assignment: dict[str, str] = {}\n"
        "        self._current_arm: str | None = None\n"
        "        self._ik_solvers: dict = {}  # Phase 2: lazy cuRobo IKSolver cache for descend\n")
assert src.count(old1) == 1, f"old1 count={src.count(old1)}"
src = src.replace(old1, new1)
print("[1 ik_solvers cache] applied")

# 2: add _get_ik_solver + _apply_descend methods after _apply_grasp (end of class)
old2 = "        if arm == \"left\":\n            action[10] = gripper_value\n        else:\n            action[11] = gripper_value\n\n        return action\n"
new2 = old2 + '''
    def _get_ik_solver(self, arm: str):
        """Phase 2: lazy-build a cuRobo IKSolver for the active arm (descend waypoints).

        Uses cuRobo IKSolver (NOT PiperPinocchioIK — that is a lazy-stub due to missing
        pinocchio.casadi in the cmeel wheel). Verified by test_curobo_config.py (<1 cm error).
        """
        if arm in self._ik_solvers:
            return self._ik_solvers[arm]
        import math
        from curobo.types.base import TensorDeviceType
        from curobo.util_file import load_yaml
        from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig
        cfg_dict = load_yaml(f"/mnt/robot/stage4_flywheel/curobo/piper_curobo_{arm}.yml")
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
        self._ik_solvers[arm] = (solver, tdtype)
        return self._ik_solvers[arm]

    def _apply_descend(self, target_joint_pos, env) -> torch.Tensor:
        """Phase 2: write a descend waypoint's 5-DoF absolute joint positions to the active arm.

        Mirrors _apply_reach but takes the cuRobo IK solution tensor directly (5-D, cspace order =
        action term joint order: joint1,2,3,5,6). Gripper held open during descend. Called by
        DoublePiperKitchenPnpPipeline._execute_descend (NOT via register_apply_method).
        """
        robot = env.scene["robot"]
        default_joint_pos = as_torch(robot.data.default_joint_pos)[0, :]
        action = env.action_manager.action[0, :].clone()

        arm = self._current_arm
        if arm == "left":
            term_name, action_slice = "left_arm_action", slice(0, 5)
        else:
            term_name, action_slice = "right_arm_action", slice(5, 10)

        arm_action_cfg = env.action_manager.get_term(term_name).cfg
        arm_action_ids, _ = robot.find_joints(arm_action_cfg.joint_names)

        arm_target = target_joint_pos  # 5-D, already in action-term order (cuRobo cspace == action term)
        if arm_action_cfg.use_default_offset:
            arm_target = arm_target - default_joint_pos[arm_action_ids]
        arm_target = arm_target / arm_action_cfg.scale

        action[action_slice] = arm_target
        action[10 if arm == "left" else 11] = 1.0  # keep gripper open during descend
        return action
'''
assert src.count(old2) == 1, f"old2 count={src.count(old2)}"
src = src.replace(old2, new2)
print("[2 _get_ik_solver + _apply_descend] applied")

PATH.write_text(src)
print("PHASE 2 TASK 2.1 PATCH APPLIED:", PATH)
