from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import torch
from isaaclab.envs import ManagerBasedEnv

from autosim import SkillRegistry
from autosim.capabilities.motion_planning import CuroboPlanner
from autosim.core.pipeline import AutoSimPipeline
from autosim.core.types import EnvExtraInfo, PipelineOutput, WorldState
from autosim.skills import CuroboSkillExtraCfg, NavigateSkillExtraCfg
from autosim.utils.data_util import as_torch

from .doublepiper_kitchen_pnp_cfg import DoublePiperKitchenPnpPipelineCfg
from .reach_gate import select_arm_per_object

if TYPE_CHECKING:
    from isaaclab.app import AppLauncher


PnP_TASK_DESCRIPTION = """## Task Description (DoublePiper-Abs Kitchen Pick-and-Place)
The robot must pick up the black bowl and place it on the plate.
- Manipulated object: akita_black_bowl (graspable bowl).
- Target receptacle: plate (bowl must rest on it).
- Supporting fixture: dining_table.
Success: akita_black_bowl is on plate AND gripper is far from akita_black_bowl.
Recommended skill sequence (use ONLY available atomic skills):
1. reach(target_object="akita_black_bowl", target_type="object")
2. grasp(target_object="akita_black_bowl", target_type="object")
3. lift(target_object="akita_black_bowl", target_type="object")
4. reach(target_object="plate", target_type="object")
5. ungrasp(target_object="akita_black_bowl", target_type="object")
6. (optional) retract(target_object="none", target_type="position")
Constraints: exact object names "akita_black_bowl","plate","dining_table"; target_type ∈ {object,fixture,interactive_element,position}; total_steps = #skills; skill_sequence = flat list of skill_type strings.
"""

TARGET_OBJECTS = ["akita_black_bowl", "plate"]


class DoublePiperKitchenPnpPipeline(AutoSimPipeline):
    """Pipeline that drives DoublePiper-Abs through a bowl-on-plate task.

    Key differences from the FrankaCubeLift template:
      - Uses lw_benchhub ``export_env_for_envhub`` instead of ``gym.make``.
      - Holds two single-arm cuRobo planners (left/right) instead of one.
      - Routes each skill to an arm chosen by the reach gate.
      - Records the ``first_person_camera`` head-view RGB stream per step.
    """

    cfg: DoublePiperKitchenPnpPipelineCfg

    def __init__(self, cfg: DoublePiperKitchenPnpPipelineCfg) -> None:
        # Stable cache key for the decomposer. The config_path stem is included so
        # different curriculum scenes do not collide in the decomposer cache.
        if cfg.config_path:
            stem = Path(cfg.config_path).stem
            self._task_name = f"Robocasa-L90K1PutTheBlackBowlOnThePlate-DoublePiper-Abs-{stem}-v0"
        else:
            self._task_name = "Robocasa-L90K1PutTheBlackBowlOnThePlate-DoublePiper-Abs-v0"

        # Reference to the single AppLauncher created by the runner. Set by the
        # runner before pipeline.run() to avoid a second AppLauncher inside
        # export_env_for_envhub.
        self._app_launcher_ref: AppLauncher | None = None

        # Head-view recording state (filled by the runner per run).
        self._scene_label: str = "scene"
        self._run_id: int = 1
        self._head_view_frames: list = []  # init here so _save_head_view_media is safe even if initialize() fails

        # Fine-tuning dataset recording state (opt-in via enable_dataset_recording()).
        # Records per-step (observation.state, action, 3 camera RGBs) aligned at the
        # PRE-step state s_t with the action a_t applied that step (lerobot convention).
        self._record_dataset: bool = False
        self._episode_states: list = []
        self._episode_actions: list = []
        self._episode_left_hand: list = []
        self._episode_right_hand: list = []
        self._episode_first_person: list = []
        # cuRobo MotionGen is non-deterministic; retry plan() on failure so
        # workspace-edge reaches (e.g. reach(plate)) find a valid path.
        self._max_plan_attempts: int = 5

        super().__init__(cfg)

    def load_env(self) -> ManagerBasedEnv:
        from lw_benchhub.utils import monkey_patch as mp

        mp.patch_create_teleop_device()
        mp.patch_xform_prim_view_auto_standardize()

        from lw_benchhub.utils.envhub_utils import export_env_for_envhub

        raw_env, _, _, _, _, _ = export_env_for_envhub(
            config_path=self.cfg.config_path,
            app_launcher=self._app_launcher_ref,
        )
        return raw_env

    def get_env_extra_info(self) -> EnvExtraInfo:
        objects = [n for n in self._env.scene.keys() if n in ("akita_black_bowl", "plate", "dining_table")]
        return EnvExtraInfo(
            task_name=self._task_name,
            objects=objects,
            robot_name="robot",
            robot_base_link_name="root",
            ee_link_name="hand_link_l",  # primary = left; right is handled at runtime
            object_reach_target_poses={
                "akita_black_bowl": [torch.tensor([0.0, 0.0, 0.05, 1.0, 0.0, 0.0, 0.0])],
                "plate": [torch.tensor([0.0, 0.0, 0.05, 1.0, 0.0, 0.0, 0.0])],
            },
            additional_prompt_contents=PnP_TASK_DESCRIPTION,
        )

    def initialize(self) -> None:
        if self._initialized:
            return

        # The base initialize() builds an OccupancyMap (for the `moveto` skill) which
        # fails on DoublePiper — the scene has no prim at /World/envs/env_0/<floor_prim_suffix>
        # (the floor is inside the Scene USD). DoublePiper is fixed-base and `moveto` is
        # skipped via PiperAbsAdapterCfg.skip_apply_skills, so the occupancy map is unused.
        # Monkey-patch get_occupancy_map to a no-op before calling super().initialize().
        import autosim.core.pipeline as _pipeline_mod
        _orig_get_occupancy_map = _pipeline_mod.get_occupancy_map
        _pipeline_mod.get_occupancy_map = lambda env, cfg: None

        # Base initialize() builds the left planner as self._motion_planner.
        try:
            super().initialize()
        finally:
            _pipeline_mod.get_occupancy_map = _orig_get_occupancy_map
        self._occupancy_map = None  # DoublePiper is fixed-base (no moveto)

        self._planner_left = self._motion_planner
        self._eef_link_idx_left = self._eef_link_idx

        # Build the right planner from a copy of the left planner config.
        right_cfg = self.cfg.motion_planner.copy()
        right_cfg.robot_config_file = "piper_curobo_right.yml"
        self._planner_right = CuroboPlanner(
            env=self._env,
            robot=self._robot,
            cfg=right_cfg,
            env_id=self._env_id,
        )
        self._eef_link_idx_right = self._robot.data.body_names.index("hand_link_r")

        # Run the reach gate once and pass arm assignment to the action adapter.
        self._arm_assignment = select_arm_per_object(
            env=self._env,
            target_objects=TARGET_OBJECTS,
            curobo_config_path=self.cfg.motion_planner.curobo_config_path,
            env_id=self._env_id,
        )
        self._logger.info(f"Reach gate arm assignment: {self._arm_assignment}")
        self._action_adapter.set_arm_assignment(self._arm_assignment)

        self._head_view_frames: list[np.ndarray] = []
        # §2 pre-check diagnostic state (contact force + bowl movement during reach on bowl).
        # Guarded: logging only; never alters pipeline behavior. Reused by Phase 2 tuning.
        self._diag_skill_type: str | None = None
        self._diag_target_object: str | None = None
        self._diag_label: str = ""
        self._diag_max_force: float = 0.0
        self._diag_force_first_contact_step: int = -1
        self._diag_bowl_start = None
        self._diag_bowl_first_move_step: int = -1

    def reset_env(self) -> None:
        super().reset_env()
        self._head_view_frames = []
        if self._record_dataset:
            self.reset_episode_record()

    def enable_dataset_recording(self) -> None:
        """Opt in to per-step fine-tuning dataset recording (state + action + 3 cameras)."""
        self._record_dataset = True

    def reset_episode_record(self) -> None:
        self._episode_states = []
        self._episode_actions = []
        self._episode_left_hand = []
        self._episode_right_hand = []
        self._episode_first_person = []

    def get_episode_record(self) -> dict:
        """Return the recorded episode as lists of per-step numpy arrays."""
        return {
            "states": self._episode_states,
            "actions": self._episode_actions,
            "left_hand_camera_rgb": self._episode_left_hand,
            "right_hand_camera_rgb": self._episode_right_hand,
            "first_person_camera_rgb": self._episode_first_person,
        }

    def run(self) -> PipelineOutput:
        try:
            output = super().run()
        finally:
            self._save_head_view_media()
        return output

    def _check_skill_extra_cfg(self) -> None:
        """Keep base logic but default every CuroboSkill to the left planner.

        Per-skill arm routing overrides the planner in execute_skill_sequence().
        """
        if (
            self.cfg.skills.moveto.extra_cfg.use_dwa
            and self.cfg.skills.moveto.extra_cfg.local_planner.dt is None
        ):
            physics_dt = self._env.cfg.sim.dt
            decimation = self._env.cfg.decimation
            self.cfg.skills.moveto.extra_cfg.local_planner.dt = physics_dt * decimation

        for skill_cfg_field in fields(self.cfg.skills):
            skill_cfg = self.cfg.skills.get(skill_cfg_field.name)
            if isinstance(skill_cfg.extra_cfg, CuroboSkillExtraCfg):
                skill_cfg.extra_cfg.curobo_planner = self._planner_left
            if isinstance(skill_cfg.extra_cfg, NavigateSkillExtraCfg):
                skill_cfg.extra_cfg.occupancy_map = self._occupancy_map

    def execute_skill_sequence(self, decompose_result):
        self._check_skill_extra_cfg()
        self.reset_env()

        for subtask in decompose_result.subtasks:
            for skill_info in subtask.skills:
                skill = SkillRegistry.create(
                    skill_info.skill_type,
                    self.cfg.skills.get(skill_info.skill_type).extra_cfg,
                )

                arm = self._arm_for_object(skill_info.target_object)
                self._current_arm = arm
                self._action_adapter.current_arm = arm

                # ReachSkill.step reads self._planner; set it before planning.
                skill._planner = self._planner_left if arm == "left" else self._planner_right

                if self._action_adapter.should_skip_apply(skill):
                    self._logger.info(f"Skill {skill_info.skill_type} skipped due to action adapter setting.")
                    continue

                goal = skill.extract_goal_from_info(skill_info, self._env, self._env_extra_info)

                # §2 diagnostic context (label overridden for the hover reach below).
                self._diag_skill_type = skill_info.skill_type
                self._diag_target_object = skill_info.target_object
                self._diag_label = skill_info.skill_type

                # Pre-grasp hover for the bowl: reach ABOVE the bowl first, then descend to the
                # grasp pose. Without this, the cuRobo approach path pushes the bowl sideways
                # (cuRobo/PhysX collision-model mismatch on the small target object), so the
                # gripper closes on empty space and every subsequent skill moves an empty gripper.
                if skill_info.skill_type == "reach" and skill_info.target_object == "akita_black_bowl":
                    pre_goal = self._make_pregrasp_goal(goal, hover_z=0.15)
                    self._diag_label = "reach_hover"
                    pre_success, pre_steps, pre_done = self._execute_single_skill(skill, pre_goal)
                    self._logger.info(
                        f"Pre-grasp hover reach executed.({pre_steps} steps, success={pre_success})"
                    )
                    self._log_object_positions(after_skill="reach_hover")
                    if pre_done:
                        return PipelineOutput(success=True, generated_actions=self._generated_actions)
                    if not pre_success:
                        raise ValueError("Pre-grasp hover reach failed.")

                success, steps, episode_done = self._execute_single_skill(skill, goal)

                if episode_done:
                    self._logger.info(f"Episode completed during skill {skill_info.skill_type}.({steps} steps)")
                    return PipelineOutput(success=True, generated_actions=self._generated_actions)

                if not success:
                    self._logger.error(f"Skill {skill_info.skill_type} execution failed with {steps} steps.")
                    raise ValueError(f"Skill {skill_info.skill_type} execution failed with {steps} steps.")

                self._logger.info(f"Skill {skill_info.skill_type} executed successfully.({steps} steps)")
                self._log_object_positions(after_skill=skill_info.skill_type)

            self._logger.info(
                f"Subtask {subtask.subtask_name} executed successfully with {len(subtask.skills)} skills."
            )

        # Verify task success (bowl on plate + gripper far). All 6 skills running does NOT
        # guarantee the bowl ended up on the plate — the grasp may slip during lift/reach,
        # or the ungrasp may release off-target. The early-return path (episode_done) already
        # confirms task success via the env's `terminated` flag; this final-return path does NOT.
        # Without this check, failure trajectories get labeled success=True (harmful for fine-tuning).
        task_success = self._check_task_success()
        return PipelineOutput(success=task_success, generated_actions=self._generated_actions)

    def _log_object_positions(self, after_skill: str) -> None:
        """Log bowl + plate world positions after each skill (grasp-failure diagnostics)."""
        try:
            bowl = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].cpu().tolist()
            plate = self._env.scene["plate"].data.root_pos_w[self._env_id][:3].cpu().tolist()
            self._logger.info(
                f"[after {after_skill}] bowl={[round(x, 3) for x in bowl]} "
                f"plate={[round(x, 3) for x in plate]}"
            )
        except Exception:
            pass

    def _log_diag_summary(self) -> None:
        """§2 pre-check: log max gripper contact force + bowl displacement for reach(bowl)."""
        if self._diag_target_object != "akita_black_bowl" or self._diag_skill_type != "reach":
            return
        try:
            bowl_disp = 0.0
            bowl_end_str = "n/a"
            try:
                bowl_end = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].cpu()
                bowl_end_str = [round(x, 3) for x in bowl_end.tolist()]
                if self._diag_bowl_start is not None:
                    bowl_disp = float(torch.linalg.norm(bowl_end - self._diag_bowl_start))
            except Exception:
                pass
            self._logger.info(
                f"[diag summary {self._diag_label}] max_gripper_force={self._diag_max_force:.3f} N "
                f"first_contact_step(>0.5N)={self._diag_force_first_contact_step} "
                f"bowl_disp={bowl_disp:.4f} m bowl_first_move_step(>1cm)={self._diag_bowl_first_move_step} "
                f"bowl_end={bowl_end_str}"
            )
        except Exception as e:
            self._logger.warning(f"diag summary error: {e}")

    def _make_pregrasp_goal(self, goal, hover_z: float):
        """Clone a reach goal with the target Z raised by hover_z (robot-root frame ≈ world Z).

        Forces a top-down approach: the hover target is directly above the grasp pose, so the
        subsequent descent to the grasp pose is a short vertical motion (no lateral sweep that
        would push the bowl).
        """
        import copy
        pre = copy.copy(goal)
        pre.target_pose = goal.target_pose.clone()
        pre.target_pose[:, 2] = pre.target_pose[:, 2] + hover_z
        return pre

    def _check_task_success(self) -> bool:
        """Call the env's task-success condition (bowl_in_plate & gripper_obj_far) + log diagnostics.

        The env's `terminated` flag is wired to `check_success_caller` via termination_cfg, so
        this is the SAME condition that would have triggered an early return mid-episode. Calling
        it here catches the final-return case where all 6 skills ran but the task never succeeded.
        """
        try:
            arena_env = self._env.cfg.isaaclab_arena_env
            success_tensor = arena_env.task.check_success_caller(self._env)
            task_success = bool(success_tensor[self._env_id].item())
        except Exception as e:
            self._logger.warning(f"check_success_caller failed: {e}; marking task failed.")
            task_success = False
        try:
            bowl_pos = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3]
            plate_pos = self._env.scene["plate"].data.root_pos_w[self._env_id][:3]
            dist = float(torch.linalg.norm(bowl_pos - plate_pos))
            self._logger.info(
                f"TASK_SUCCESS={task_success}; bowl={[round(x, 3) for x in bowl_pos.cpu().tolist()]}; "
                f"plate={[round(x, 3) for x in plate_pos.cpu().tolist()]}; bowl-plate dist={dist:.4f} m"
            )
        except Exception:
            self._logger.info(f"TASK_SUCCESS={task_success} (position diagnostic unavailable)")
        return task_success

    def _execute_single_skill(self, skill, goal):
        # cuRobo MotionGen is non-deterministic (random seeds per call); retry
        # plan() on failure so workspace-edge reaches (e.g. reach(plate)) find a
        # valid path without re-creating the env.
        plan_success = False
        for attempt in range(self._max_plan_attempts):
            world_state = self._build_world_state()
            plan_success = skill.plan(world_state, goal)
            if plan_success:
                break
            self._logger.warning(
                f"Skill plan failed (attempt {attempt + 1}/{self._max_plan_attempts}); retrying."
            )
        if not plan_success:
            self._logger.error("Skill plan failed after all retries.")
            return False, 0, False

        steps = 0
        # §2 diagnostic: reset per-skill accumulators; capture bowl start position.
        self._diag_max_force = 0.0
        self._diag_force_first_contact_step = -1
        self._diag_bowl_first_move_step = -1
        try:
            self._diag_bowl_start = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].detach().cpu()
        except Exception:
            self._diag_bowl_start = None
        while plan_success and steps < self.cfg.max_steps:
            world_state = self._build_world_state()
            output = skill.step(world_state)

            adapter_result = self._action_adapter.apply(skill, output, self._env)
            action = self._last_action.clone()
            action[self._env_id, : adapter_result.shape[0]] = adapter_result

            # Record (s_t, a_t, cameras@s_t) BEFORE the step (lerobot convention).
            if self._record_dataset:
                self._record_dataset_frame(world_state, action)

            _, _, terminated, truncated, _ = self._env.step(action)
            self._last_action = action
            self._generated_actions.append(action)

            self._record_head_view_frame()

            # §2 diagnostic: contact force + bowl movement during reach on bowl.
            if self._diag_target_object == "akita_black_bowl" and self._diag_skill_type == "reach":
                try:
                    arm = self._current_arm
                    body_names = self._robot.data.body_names
                    gripper_links = (["gripper_base_l", "link7_l", "link8_l"] if arm == "left"
                                     else ["gripper_base_r", "link7_r", "link8_r"])
                    max_force = 0.0
                    for ln in gripper_links:
                        if ln in body_names:
                            idx = body_names.index(ln)
                            f = float(torch.linalg.norm(
                                self._robot.data.net_contact_forces[self._env_id, idx]).cpu())
                            if f > max_force:
                                max_force = f
                    if max_force > self._diag_max_force:
                        self._diag_max_force = max_force
                    if self._diag_force_first_contact_step < 0 and max_force > 0.5:
                        self._diag_force_first_contact_step = steps
                    if self._diag_bowl_start is not None:
                        bowl_now = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].detach().cpu()
                        move = float(torch.linalg.norm(bowl_now - self._diag_bowl_start))
                        if self._diag_bowl_first_move_step < 0 and move > 0.01:
                            self._diag_bowl_first_move_step = steps
                    if steps % 10 == 0 or max_force > 0.5:
                        self._logger.info(
                            f"[diag {self._diag_label}] step={steps} max_force={max_force:.3f} N "
                            f"(run_max={self._diag_max_force:.3f})"
                        )
                except Exception as e:
                    self._logger.warning(f"diag instrumentation error: {e}")

            steps += 1
            if bool((terminated[self._env_id] | truncated[self._env_id]).item()):
                self._log_diag_summary()
                return True, steps, True
            if output.done:
                self._log_diag_summary()
                return True, steps, False

        if steps >= self.cfg.max_steps:
            world_state = self._build_world_state()
            current_pos = world_state.robot_base_pose[:2]
            if goal.target_pose is not None:
                target_pos = goal.target_pose[:2]
                dist = float(torch.linalg.norm(current_pos - target_pos))
                self._logger.warning(
                    f"Max steps reached. Current pos: ({current_pos[0]:.3f}, {current_pos[1]:.3f}), "
                    f"Target pos: ({target_pos[0]:.3f}, {target_pos[1]:.3f}), Distance: {dist:.3f}m"
                )

        self._log_diag_summary()
        return False, steps, False

    def _build_world_state(self) -> WorldState:
        """Build world state using the EE link of the currently active arm."""
        ee_idx = self._eef_link_idx_right if getattr(self, "_current_arm", None) == "right" else self._eef_link_idx_left

        joint_pos_limits = as_torch(self._robot.data.joint_pos_limits)[self._env_id, :, :]
        lower, upper = joint_pos_limits[:, 0], joint_pos_limits[:, 1]
        robot_joint_pos = torch.clamp(
            as_torch(self._robot.data.joint_pos)[self._env_id, :], min=lower, max=upper
        )
        robot_joint_vel = as_torch(self._robot.data.joint_vel)[self._env_id, :]
        robot_ee_pose = as_torch(self._robot.data.body_link_pose_w)[self._env_id, ee_idx]

        robot_base_pose = as_torch(self._robot.data.body_link_pose_w)[self._env_id, self._robot_base_link_idx]
        x, y, z, w = robot_base_pose[3:7]
        sin_yaw = 2 * (w * z + x * y)
        cos_yaw = 1 - 2 * (y**2 + z**2)
        yaw = torch.atan2(sin_yaw, cos_yaw)
        robot_base_pose = torch.stack((robot_base_pose[0], robot_base_pose[1], yaw))

        robot_root_pose = as_torch(self._robot.data.root_pose_w)[self._env_id]
        sim_joint_names = self._robot.data.joint_names

        objects_dict = {}
        if self._target_objects is None:
            self._target_objects = self._decompose_result.get_target_objects()
        for obj_name in self._target_objects:
            obj = self._env.scene[obj_name]
            if hasattr(obj, "data") and hasattr(obj.data, "root_pose_w") and obj_name != self._robot_name:
                objects_dict[obj_name] = as_torch(obj.data.root_pose_w)[self._env_id]

        return WorldState(
            robot_joint_pos=robot_joint_pos,
            robot_joint_vel=robot_joint_vel,
            robot_ee_pose=robot_ee_pose,
            robot_base_pose=robot_base_pose,
            robot_root_pose=robot_root_pose,
            sim_joint_names=sim_joint_names,
            objects=objects_dict,
        )

    def _arm_for_object(self, target_object: str) -> str:
        arm = self._arm_assignment.get(target_object)
        if arm is None:
            self._logger.warning(f"No reach-gate assignment for '{target_object}'; defaulting to left arm.")
            arm = "left"
        return arm

    def _record_head_view_frame(self) -> None:
        sensors = getattr(self._env.scene, "sensors", {}) or {}
        if "first_person_camera" not in sensors:
            return
        rgb = sensors["first_person_camera"].data.output["rgb"][self._env_id]
        self._head_view_frames.append(rgb.detach().cpu().numpy())

    def _record_dataset_frame(self, world_state, action) -> None:
        """Record one fine-tuning frame: state(s_t) + action(a_t) + 3 cameras(@s_t)."""
        self._episode_states.append(world_state.robot_joint_pos.detach().cpu().numpy().copy())
        # action tensor is [num_envs, 16]; the SmolVLA 12-D action is the first 12 slots
        # ([left_arm(5)|right_arm(5)|left_grip(1)|right_grip(1)], absolute joint targets).
        self._episode_actions.append(action[self._env_id, :12].detach().cpu().numpy().copy())
        sensors = getattr(self._env.scene, "sensors", {}) or {}
        for cam_key, buf in (
            ("left_hand_camera", self._episode_left_hand),
            ("right_hand_camera", self._episode_right_hand),
            ("first_person_camera", self._episode_first_person),
        ):
            if cam_key in sensors:
                rgb = sensors[cam_key].data.output["rgb"][self._env_id]
                buf.append(rgb.detach().cpu().numpy().copy())
            else:
                buf.append(None)

    def _save_head_view_media(self) -> None:
        if not self._head_view_frames:
            return

        frames = self._normalize_frames(self._head_view_frames)
        out = Path(self.cfg.output_dir) / self._scene_label
        out.mkdir(parents=True, exist_ok=True)

        mp4_path = out / f"run_{self._run_id:03d}_head_view.mp4"
        png_path = out / f"run_{self._run_id:03d}_frame0.png"

        import mediapy

        mediapy.write_video(str(mp4_path), frames, fps=50)

        from PIL import Image

        Image.fromarray(frames[0]).save(png_path)

    def _normalize_frames(self, frames: list[np.ndarray]) -> np.ndarray:
        """Coerce camera frames to uint8 [T, H, W, 3]."""
        normalized = []
        for f in frames:
            # Drop batch dimension if present.
            if f.ndim == 4 and f.shape[0] == 1:
                f = f.squeeze(0)

            # Convert float [0, 1] -> uint8 [0, 255].
            if f.dtype in (np.float32, np.float64):
                if f.max() <= 1.0:
                    f = (f * 255).astype(np.uint8)
                else:
                    f = f.astype(np.uint8)

            # Drop alpha channel if present.
            if f.ndim == 3 and f.shape[-1] == 4:
                f = f[..., :3]

            normalized.append(f)

        return np.stack(normalized, axis=0)
