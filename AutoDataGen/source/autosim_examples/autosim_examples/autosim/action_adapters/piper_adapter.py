from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from isaaclab.envs import ManagerBasedEnv

from autosim import ActionAdapterBase
from autosim.core.types import SkillOutput
from autosim.utils.data_util import as_torch

if TYPE_CHECKING:
    from .piper_adapter_cfg import PiperAbsAdapterCfg


class PiperAbsAdapter(ActionAdapterBase):
    """Action adapter for the DoublePiper-Abs dual-arm robot.

    Maps skill outputs into the 12-D action vector used by DoublePiper-Abs:
        [left_arm(5) | right_arm(5) | left_gripper(1) | right_gripper(1)]

    The action term skips joint4 on each arm; cuRobo configs lock joint4_l/joint4_r
    so planned trajectories do not depend on it.
    """

    def __init__(self, cfg: PiperAbsAdapterCfg):
        super().__init__(cfg)

        self.register_apply_method("reach", self._apply_reach)
        self.register_apply_method("grasp", self._apply_grasp)
        self.register_apply_method("lift", self._apply_reach)
        self.register_apply_method("ungrasp", self._apply_grasp)
        # RelativeReachSkill family (retract/pull/push) produce joint trajectories like lift;
        # route them through _apply_reach so they write the 5-DoF arm action (not the default
        # full 16-joint sim pos, which would cause a [16] vs [12] action-shape mismatch).
        self.register_apply_method("retract", self._apply_reach)
        self.register_apply_method("pull", self._apply_reach)
        self.register_apply_method("push", self._apply_reach)

        self._arm_assignment: dict[str, str] = {}
        self._current_arm: str | None = None

    def set_arm_assignment(self, assignment: dict[str, str]) -> None:
        """Set the per-object arm assignment from the reach gate."""
        self._arm_assignment = assignment

    @property
    def current_arm(self) -> str | None:
        return self._current_arm

    @current_arm.setter
    def current_arm(self, arm: str | None) -> None:
        self._current_arm = arm

    def _apply_reach(self, skill_output: SkillOutput, env: ManagerBasedEnv) -> torch.Tensor:
        """Write planned absolute joint positions to the active arm's action slice."""
        target_joint_pos = skill_output.action  # [num_sim_joints]

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

        arm_target = target_joint_pos[arm_action_ids]
        if arm_action_cfg.use_default_offset:
            arm_target = arm_target - default_joint_pos[arm_action_ids]
        arm_target = arm_target / arm_action_cfg.scale

        action[action_slice] = arm_target
        return action

    def _apply_grasp(self, skill_output: SkillOutput, env: ManagerBasedEnv) -> torch.Tensor:
        """Write the gripper command to the active arm's gripper action index."""
        action = env.action_manager.action[0, :].clone()

        arm = self._current_arm or self._arm_assignment.get(skill_output.info.get("target_object"))
        gripper_value = skill_output.action[0]  # GripperSkillBase: -1.0 close / +1.0 open

        if arm == "left":
            action[10] = gripper_value
        else:
            action[11] = gripper_value

        return action
