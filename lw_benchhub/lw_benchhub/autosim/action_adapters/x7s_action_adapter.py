from __future__ import annotations

import torch

from typing import TYPE_CHECKING

from autosim import ActionAdapterBase
from autosim.core.types import SkillOutput
from isaaclab.envs import ManagerBasedEnv

if TYPE_CHECKING:
    from .x7s_action_adapter_cfg import X7SActionAdapterCfg


class X7SActionAdapter(ActionAdapterBase):
    """Action adapter for the X7S robot."""

    def __init__(self, cfg: X7SActionAdapterCfg):
        super().__init__(cfg)
        self.register_apply_method("moveto", self._apply_moveto)
        self.register_apply_method("reach", self._apply_reach)
        self.register_apply_method("grasp", self._apply_gripper)
        self.register_apply_method("ungrasp", self._apply_gripper)
        self.register_apply_method("lift", self._apply_reach)
        self.register_apply_method("pull", self._apply_reach)
        self.register_apply_method("push", self._apply_reach)

    def _apply_moveto(self, skill_output: SkillOutput, env: ManagerBasedEnv) -> torch.Tensor:
        vx, vy, vyaw = skill_output.action  # [vx, vy, vyaw] in the world frame

        robot = env.scene["robot"]
        world_pose = robot.data.root_pose_w[0]  # [x, y, z, qw, qx, qy, qz]
        w, x, y, z = world_pose[3:7]
        sin_yaw = 2 * (w * z + x * y)
        cos_yaw = 1 - 2 * (y**2 + z**2)
        yaw = torch.atan2(sin_yaw, cos_yaw)
        cos_yaw = torch.cos(yaw)
        sin_yaw = torch.sin(yaw)
        vx_body = vx * cos_yaw + vy * sin_yaw
        vy_body = -vx * sin_yaw + vy * cos_yaw

        dt_control = env.cfg.sim.dt * env.cfg.decimation

        last_action = env.action_manager.action
        action = last_action[0, :].clone()

        base_x_idx = robot.joint_names.index(self.cfg.base_x_joint_name)
        base_y_idx = robot.joint_names.index(self.cfg.base_y_joint_name)
        base_yaw_idx = robot.joint_names.index(self.cfg.base_yaw_joint_name)

        action[base_x_idx] = (vx_body * dt_control) / 0.01
        action[base_y_idx] = (vy_body * dt_control) / 0.01
        action[base_yaw_idx] = (vyaw * dt_control) / 0.01

        return action

    def _apply_reach(self, skill_output: SkillOutput, env: ManagerBasedEnv) -> torch.Tensor:
        # [joint_positions] with isaaclab joint order
        target_joint_pos = skill_output.action

        robot = env.scene["robot"]
        current_joint_pos = robot.data.joint_pos[0]

        last_action = env.action_manager.action
        action = last_action[0, :].clone()

        base_action_ids, _ = robot.find_joints(
            env.action_manager.get_term("base_action").cfg.joint_names)
        body_action_ids, _ = robot.find_joints(
            env.action_manager.get_term("body_action").cfg.joint_names)
        left_arm_action_ids, _ = robot.find_joints(
            env.action_manager.get_term("left_arm_action").cfg.joint_names)
        right_arm_action_ids, _ = robot.find_joints(
            env.action_manager.get_term("right_arm_action").cfg.joint_names)

        action[0:3] = (target_joint_pos[base_action_ids]
                       - current_joint_pos[base_action_ids]) / 0.01  # delta position action
        action[3:5] = (target_joint_pos[body_action_ids]
                       - current_joint_pos[body_action_ids]) / 0.025  # delta position action
        action[5:12] = target_joint_pos[left_arm_action_ids]
        action[12:19] = target_joint_pos[right_arm_action_ids]

        return action

    def _apply_gripper(self, skill_output: SkillOutput, env: ManagerBasedEnv) -> torch.Tensor:
        """Apply the gripper action."""

        gripper_value = skill_output.action  # [ungrasp: 1.0, grasp: -1.0]

        last_action = env.action_manager.action
        action = last_action[0, :].clone()

        if self.cfg.use_left_gripper_action:
            action[19:20] = gripper_value  # left gripper action
        else:
            action[20:21] = gripper_value  # right gripper action

        return action
