from autosim.core.pipeline import AutoSimPipeline, AutoSimPipelineCfg
from isaaclab.envs import ManagerBasedEnv
from isaaclab.utils import configclass

import torch
import numpy as np

from autosim.decomposers import LLMDecomposerCfg

from ..prompt_utils import render_additional_prompt
from ..robot_profiles import (
    TaskRobotOverride,
    build_env_extra_info,
    configure_robot_runtime_settings,
    resolve_robot_settings,
)

TASK_ROBOT_OVERRIDES: dict[str, TaskRobotOverride] = {
    "x7s_joint_left": TaskRobotOverride(
        extra_target_link_names=("link20_tip",),
        reach_extra_target_mode="keep_relative_offset",
        object_reach_target_poses={
            "obj": [
                torch.tensor([-0.02, 0.0, 0.01, 1.0, 0.0, 0.0, 0.0]),
            ],
            "coffee_machine_main_group": [
                torch.tensor([0.0, -0.12, -0.03, 0.707, 0.0, 0.0, 0.707]),
            ],
        },
    ),
}


def get_task_robot_override(robot_profile: str) -> TaskRobotOverride:
    try:
        return TASK_ROBOT_OVERRIDES[robot_profile]
    except KeyError as exc:
        supported = ", ".join(tuple(TASK_ROBOT_OVERRIDES))
        raise ValueError(
            f"CoffeeSetupMugPipeline does not support robot profile '{robot_profile}'. Supported profiles: {supported}"
        ) from exc


@configclass
class CoffeeSetupMugPipelineCfg(AutoSimPipelineCfg):
    """Configuration for the CoffeeSetupMugPipeline."""

    robot_profile: str = "x7s_joint_left"

    decomposer: LLMDecomposerCfg = LLMDecomposerCfg()

    def __post_init__(self):
        resolved_robot = resolve_robot_settings(
            self.robot_profile,
            override=get_task_robot_override(self.robot_profile),
        )
        configure_robot_runtime_settings(self, resolved_robot)

        self.skills.moveto.extra_cfg.local_planner.max_linear_velocity = 0.4
        self.skills.moveto.extra_cfg.local_planner.max_angular_velocity = 0.8
        self.skills.moveto.extra_cfg.local_planner.predict_time = 0.4
        self.skills.moveto.extra_cfg.global_planner.safety_distance = 0.8
        self.skills.moveto.extra_cfg.global_planner.proximity_weight = 3.0
        self.skills.moveto.extra_cfg.waypoint_tolerance = 0.2
        self.skills.moveto.extra_cfg.goal_tolerance = 0.07
        self.skills.moveto.extra_cfg.yaw_tolerance = 0.008
        self.skills.moveto.extra_cfg.uws_dwa = False
        self.max_steps = 1000

        self.skills.lift.extra_cfg.lift_offset = 0.20

        self.occupancy_map.floor_prim_suffix = "Scene/floor_room"
        self.motion_planner.world_ignore_subffixes = ["Scene/floor_room"]
        self.motion_planner.world_only_subffixes = [
            "Scene/island_island_group",
            "Scene/island_panel_cab_right_island_group_1",
            "Scene/counter_main_main_group",
        ]


class CoffeeSetupMugPipeline(AutoSimPipeline):
    def __init__(self, cfg: AutoSimPipelineCfg):
        super().__init__(cfg)
        robot_profile = cfg.robot_profile
        self._resolved_robot = resolve_robot_settings(
            robot_profile,
            override=get_task_robot_override(robot_profile),
        )

    def load_env(self) -> ManagerBasedEnv:
        import gymnasium as gym
        import lw_benchhub_tasks.lightwheel_robocasa_tasks.single_stage.kitchen_coffee as kc
        from lw_benchhub.utils.env import ExecuteMode, parse_env_cfg

        kc.CoffeeSetupMug._get_obj_cfgs = patch_get_obj_cfgs
        env_cfg = parse_env_cfg(
            scene_backend="robocasa",
            task_backend="robocasa",
            task_name="CoffeeSetupMug",
            robot_name=self._resolved_robot.profile.robot_name,
            scene_name="robocasakitchen-2-2",
            robot_scale=1.0,
            device="cpu",
            num_envs=1,
            use_fabric=False,
            first_person_view=False,
            enable_cameras=False,
            execute_mode=ExecuteMode.TELEOP,
            usd_simplify=False,
            seed=42,
            sources=["objaverse", "lightwheel", "aigen_objs"],
            object_projects=[],
            rl_name=None,
            headless_mode=False,
            replay_cfgs={"add_camera_to_observation": True, "render_resolution": (640, 480)},
        )

        env_cfg.terminations.time_out = None

        env_cfg.scene.robot.init_state.pos[1] -= 0.8
        env_cfg.scene.robot.init_state.pos[2] += 0.3
        env_cfg.scene.robot.init_state.rot = (0.707, 0.0, 0.0, -0.707)

        env_id = f"Robocasa-CoffeeSetupMug-{self._resolved_robot.profile.robot_name}-v0"
        gym.register(
            id=env_id,
            entry_point="isaaclab.envs:ManagerBasedRLEnv",
            kwargs={},
            disable_env_checker=True,
        )

        env = gym.make(env_id, cfg=env_cfg, render_mode="rgb_array").unwrapped

        return env

    def get_env_extra_info(self):
        return build_env_extra_info(
            task_name="Robocasa-Task-CoffeeSetupMug",
            objects=self._env.scene.keys(),
            additional_prompt_contents=render_additional_prompt(),
            resolved_robot=self._resolved_robot,
        )


def patch_get_obj_cfgs(self):
    cfgs = []
    cfgs.append(
        dict(
            name="obj",
            obj_groups="mug",
            asset_name="Mug028.usd",
            placement=dict(
                fixture=self.counter,
                sample_region_kwargs={},
                size=(0.8, 0.15),
                pos=(0.0, -1.0),
                rotation=(np.pi / 2, np.pi / 2),
            ),
        )
    )

    return cfgs
