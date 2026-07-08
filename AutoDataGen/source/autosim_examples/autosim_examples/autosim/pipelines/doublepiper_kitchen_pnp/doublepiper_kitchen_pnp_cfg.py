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

        # More MotionGen seeds (default 12) for the reach(plate) trajectory — plate is at the
        # workspace edge; extra seeds help the trajectory optimizer find a valid path (non-deterministic
        # at lower seed counts).
        self.motion_planner.num_trajopt_seeds = 96
        self.motion_planner.num_graph_seeds = 96

        self.occupancy_map.floor_prim_suffix = "floor"

        self.skills.lift.extra_cfg.move_axis = "-z"  # EE z points down (like Franka); -z lifts UP (reachable)
        self.skills.lift.extra_cfg.move_offset = 0.10
