from dataclasses import field

from isaaclab.utils import configclass

from autosim.core.pipeline import AutoSimPipelineCfg

from ...action_adapters.piper_adapter_cfg import PiperAbsAdapterCfg
from ...decomposers import DeepSeekV4ProLLMDecomposerCfg


@configclass
class DoublePiperKitchenPnpPipelineCfg(AutoSimPipelineCfg):
    """Configuration for the DoublePiper kitchen pick-and-place pipeline."""

    config_path: str = ""
    """Path to the lw_benchhub envhub YAML scene config (injected by runner)."""

    output_dir: str = "/mnt/robot/stage4_flywheel/demos"
    """Directory where head-view media artifacts are written."""

    decomposer: DeepSeekV4ProLLMDecomposerCfg = field(default_factory=DeepSeekV4ProLLMDecomposerCfg)
    """DeepSeek-v4-pro decomposer (Anthropic Messages protocol, no model degrade)."""

    action_adapter: PiperAbsAdapterCfg = field(default_factory=PiperAbsAdapterCfg)
    """Dual-arm absolute joint-position action adapter for DoublePiper-Abs."""

    def __post_init__(self):
        # Primary planner = LEFT arm (base initialize() builds this as self._motion_planner).
        self.motion_planner.robot_config_file = "piper_curobo_left.yml"
        self.motion_planner.curobo_config_path = "/mnt/robot/stage4_flywheel/curobo"
        self.motion_planner.robot_prim_path = "/World/envs/env_0/Robot"
        self.motion_planner.world_ignore_subffixes = []
        self.motion_planner.world_only_subffixes = []
        self.motion_planner.env_scene_prefix = None

        # Phase 2 (Stage4_Patch_01 §4.3.3): raise collision_activation_distance (default 0.05 -> 0.07)
        # to INCREASE the cuRobo safety margin. Per §4.3.1 correction, the original plan's 0.02-0.04
        # was the WRONG direction (default is 0.05, so <0.05 tightens the margin -> more bowl pushing).
        # >=0.06 increases the margin. Combined with the gripper collision_spheres in
        # piper_curobo_{left,right}.yml (§4.3.2), this gives cuRobo a real gripper collision model.
        self.motion_planner.collision_activation_distance = 0.07

        # More MotionGen seeds (default 12) for the reach(plate) trajectory — plate is at the
        # workspace edge; extra seeds help the trajectory optimizer find a valid path (non-deterministic
        # at lower seed counts).
        self.motion_planner.num_trajopt_seeds = 96
        self.motion_planner.num_graph_seeds = 96

        # Patch-02: rotation_threshold is now exposed on CuroboPlannerCfg (was hardcoded pi). Default
        # pi = position-only planning (rotation ignored for success), which is the ONLY mode that
        # plans successfully at the bowl's hover pose (the bowl sits at the workspace edge, behind
        # the robot base; reaching above it with a constrained orientation fails planning - tested
        # identity, bowl-inverse, 0.1 & 0.5 thresholds, all fail at reach_hover). Position-only
        # plans but leaves the gripper's default orientation (fingers ~0.30m past the bowl) so the
        # grasp closes on empty air -> TASK_SUCCESS=False. Kept at default (pi) so the pipeline runs
        # end-to-end. A true fix needs a reachable top-down grasp pose, which seed 48's bowl
        # placement does not afford for the right arm. See docs/Stage4_Patch_02_report.md.

        self.occupancy_map.floor_prim_suffix = "floor"

        self.skills.lift.extra_cfg.move_axis = "-z"  # EE z points down (like Franka); -z lifts UP (reachable)
        self.skills.lift.extra_cfg.move_offset = 0.10
