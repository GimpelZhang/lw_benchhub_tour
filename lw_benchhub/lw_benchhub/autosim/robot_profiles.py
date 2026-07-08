from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import torch
from autosim.core.types import EnvExtraInfo

from .action_adapters.x7s_action_adapter_cfg import X7SActionAdapterCfg

# Shared autosim content roots used by all robot-specific motion-planner configs.
AUTOSIM_CONTENT_ROOT = Path(__file__).parent / "content"


@dataclass
class RobotProfile:
    """Robot-only settings reused across multiple task pipelines."""

    profile_id: str
    """Stable autosim-side identifier used to select this robot profile."""
    robot_name: str
    """LW-BenchHub robot registry name forwarded into ``parse_env_cfg``."""
    action_adapter_factory: Callable[[], object]
    """Factory that creates the autosim action-adapter config for this robot."""
    motion_planner_robot_config_file: str
    """Robot-specific cuRobo / planner config file name under autosim content."""
    robot_base_link_name: str
    """Base link name exposed to autosim through ``EnvExtraInfo``."""
    ee_link_name: str
    """Preferred end-effector link name exposed to autosim through ``EnvExtraInfo``."""


@dataclass
class TaskRobotOverride:
    """Per-task-per-robot values that depend on both the task and the robot choice."""

    object_reach_target_poses: dict[str, list[torch.Tensor]] | None = None
    """Concrete reach target poses owned by this task-robot combination."""
    extra_target_link_names: tuple[str, ...] | None = None
    """Robot tip links used as extra reach targets for this task-robot combination."""
    reach_extra_target_mode: str | None = None
    """Reach target mode for the selected robot and task combination."""


@dataclass
class ResolvedRobotSettings:
    """Final robot settings after merging the shared profile and task-specific override."""

    profile: RobotProfile
    """Shared robot profile selected by the pipeline."""
    override: TaskRobotOverride
    """Task-local robot overrides merged on top of the shared profile."""

    @property
    def robot_base_link_name(self) -> str:
        return self.profile.robot_base_link_name

    @property
    def ee_link_name(self) -> str:
        return self.profile.ee_link_name

    @property
    def motion_planner_robot_config_file(self) -> str:
        return self.profile.motion_planner_robot_config_file


ROBOT_PROFILES: dict[str, RobotProfile] = {
    "x7s_joint_left": RobotProfile(
        profile_id="x7s_joint_left",
        robot_name="X7S-Joint",
        action_adapter_factory=X7SActionAdapterCfg,
        motion_planner_robot_config_file="x7s.yml",
        robot_base_link_name="base_link",
        ee_link_name="left_hand_link",
    ),
    "x7s_joint_right": RobotProfile(
        profile_id="x7s_joint_right",
        robot_name="X7S-Joint",
        action_adapter_factory=lambda: X7SActionAdapterCfg(use_left_gripper_action=False),
        motion_planner_robot_config_file="x7s_right_ee.yml",
        robot_base_link_name="base_link",
        ee_link_name="right_hand_link",
    ),
}


# Robot profile selection must always be explicit at the pipeline level.

def get_robot_profile(profile_id: str) -> RobotProfile:
    """Resolve a registered autosim robot profile by id."""

    try:
        return ROBOT_PROFILES[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(ROBOT_PROFILES))
        raise KeyError(f"Unknown autosim robot profile '{profile_id}'. Available: {available}") from exc


def resolve_robot_settings(profile_id: str, override: TaskRobotOverride | None = None) -> ResolvedRobotSettings:
    """Merge the shared robot profile with optional task-specific overrides."""

    profile = get_robot_profile(profile_id)
    return ResolvedRobotSettings(profile=profile, override=override if override is not None else TaskRobotOverride())


def configure_robot_runtime_settings(pipeline_cfg, resolved_robot: ResolvedRobotSettings) -> None:
    """Fill shared robot-derived runtime settings for adapter, planning, and reach behavior."""

    # Action adapter
    pipeline_cfg.action_adapter = resolved_robot.profile.action_adapter_factory()

    # Motion planner
    pipeline_cfg.motion_planner.robot_config_file = resolved_robot.motion_planner_robot_config_file
    pipeline_cfg.motion_planner.curobo_asset_path = str(AUTOSIM_CONTENT_ROOT / "assets")
    pipeline_cfg.motion_planner.curobo_config_path = str(AUTOSIM_CONTENT_ROOT / "configs" / "robot")

    # Reach behavior
    if resolved_robot.override.extra_target_link_names:
        pipeline_cfg.skills.reach.extra_cfg.extra_target_link_names = list(resolved_robot.override.extra_target_link_names)
    if resolved_robot.override.reach_extra_target_mode is not None:
        pipeline_cfg.skills.reach.extra_cfg.extra_target_mode = resolved_robot.override.reach_extra_target_mode


def build_env_extra_info(
    *,
    task_name: str,
    objects,
    additional_prompt_contents: str,
    resolved_robot: ResolvedRobotSettings,
    object_navigate_sample_range: dict[str, tuple[float, float]] = {},
    robot_name: str = "robot",
) -> EnvExtraInfo:
    """Build autosim-facing metadata by combining task-level info with task-robot overrides."""

    reach_target_poses = {}
    if resolved_robot.override.object_reach_target_poses:
        reach_target_poses = {
            **reach_target_poses,
            **resolved_robot.override.object_reach_target_poses,
        }
    else:
        raise ValueError("No object reach target poses provided for the task-robot combination.")

    return EnvExtraInfo(
        task_name=task_name,
        objects=objects,
        additional_prompt_contents=additional_prompt_contents,
        robot_name=robot_name,
        robot_base_link_name=resolved_robot.robot_base_link_name,
        ee_link_name=resolved_robot.ee_link_name,
        object_reach_target_poses=reach_target_poses,
        object_navigate_sample_range=object_navigate_sample_range,
    )
