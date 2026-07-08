from autosim.core.pipeline import AutoSimPipeline, AutoSimPipelineCfg
from isaaclab.utils import configclass

import torch

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
        reach_extra_target_mode="keep_initial_relative_offset",
        object_reach_target_poses={
            "dessert1": [
                torch.tensor([0.003, -0.019, 0.025, 0.705, -0.002, 0.05, 0.707]),
            ],
            "receptacle": [
                torch.tensor([0.003, -0.049, 0.085, 0.705, -0.002, 0.05, 0.707]),
            ],
        },
    ),
    "x7s_joint_right": TaskRobotOverride(
        extra_target_link_names=("link11_tip",),
        reach_extra_target_mode="keep_initial_relative_offset",
        object_reach_target_poses={
            "dessert1": [
                torch.tensor([0.003, -0.019, 0.025, 0.705, -0.002, 0.05, 0.707]),
            ],
            "receptacle": [
                torch.tensor([0.003, -0.049, 0.085, 0.705, -0.002, 0.05, 0.707]),
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
            f"DessertUpgradePipeline does not support robot profile '{robot_profile}'. Supported profiles: {supported}"
        ) from exc


@configclass
class DessertUpgradePipelineCfg(AutoSimPipelineCfg):
    """Configuration for the DessertUpgradePipeline."""

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
            "Scene/counter_main_main_group",
            "Scene/counter_1_left_group",
            "Scene/counter_1_right_group",
        ]


class DessertUpgradePipeline(AutoSimPipeline):
    def __init__(self, cfg: AutoSimPipelineCfg):
        super().__init__(cfg)
        robot_profile = cfg.robot_profile
        self._resolved_robot = resolve_robot_settings(
            robot_profile,
            override=get_task_robot_override(robot_profile),
        )

    def load_env(self):
        import gymnasium as gym
        import lw_benchhub_tasks.lightwheel_robocasa_tasks.multi_stage.serving_food.dessert_upgrade as du
        from lw_benchhub.utils.env import ExecuteMode, parse_env_cfg

        du.DessertUpgrade._get_obj_cfgs = patch_get_obj_cfgs
        env_cfg = parse_env_cfg(
            scene_backend="robocasa",
            task_backend="robocasa",
            task_name="DessertUpgrade",
            robot_name=self._resolved_robot.profile.robot_name,
            scene_name="robocasakitchen-6-2",
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
            resample_robot_placement_on_reset=False,
        )

        env_cfg.scene.robot.init_state.pos[0] -= 0.2
        env_cfg.scene.robot.init_state.pos[1] -= 1.6

        env_cfg.terminations.time_out = None
        env_cfg.terminations.success = None

        env_id = f"Robocasa-DessertUpgrade-{self._resolved_robot.profile.robot_name}-v0"
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
            task_name="Robocasa-Task-DessertUpgrade",
            objects=["dessert1", "receptacle"],
            additional_prompt_contents=f"{render_additional_prompt()}\n\n Only grasp the dessert1 and place it in the receptacle. After grasping the dessert1, you should lift it up.",
            resolved_robot=self._resolved_robot,
        )


def patch_get_obj_cfgs(self):
    cfgs = []
    cfgs.append(
        dict(
            name="receptacle",
            obj_groups="tray",
            asset_name="Tray033.usd",
            graspable=False,
            placement=dict(
                fixture=self.counter,
                sample_region_kwargs=dict(top_size=(1.0, 0.4)),
                size=(1, 0.35),
                pos=(0, -0.6),
                offset=(0.0, -0.0),
                rotation=(0.0, 0.0),
            ),
        )
    )

    cfgs.append(
        dict(
            name="dessert1",
            obj_groups=["cake"],
            asset_name="Cake005.usd",
            graspable=True,
            placement=dict(
                fixture=self.counter,
                size=(1, 0.15),
                pos=(0, -1),
                rotation=(0.0, 0.0),
            ),
        )
    )

    return cfgs
