# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Run a simple zero-action agent on a USD scene."""

import argparse
import os

import torch

import isaaclab.sim as sim_utils
from isaaclab.app import AppLauncher
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass


# add argparse arguments
parser = argparse.ArgumentParser(description="Zero agent for Isaac Lab environments with USD file loading.")
parser.add_argument(
    "--usd_path",
    type=str,
    required=True,
    help="Path to the USD file to load.",
)
parser.add_argument(
    "--disable_fabric",
    action="store_true",
    help="Disable fabric and use USD I/O operations.",
)
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


@configclass
class UsdViewerEnvCfg(DirectRLEnvCfg):
    """Minimal configuration for zero-agent USD viewer."""

    decimation = 1
    episode_length_s = 1000.0
    action_space = 0
    observation_space = 0
    state_space = 0

    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=args_cli.num_envs,
        env_spacing=50.0,
        replicate_physics=False,
    )


class UsdViewerEnv(DirectRLEnv):
    """Environment that only loads a USD scene."""

    cfg: UsdViewerEnvCfg

    def __init__(self, cfg: UsdViewerEnvCfg, usd_path: str, **kwargs):
        self._usd_path = usd_path
        super().__init__(cfg, **kwargs)

    def _setup_scene(self):
        if not os.path.exists(self._usd_path):
            raise FileNotFoundError(f"USD file not found: '{self._usd_path}'")

        print(f"[INFO]: Loading USD file: {self._usd_path}")
        spawn_cfg = sim_utils.UsdFileCfg(usd_path=self._usd_path)
        spawn_cfg.func("/World/envs/env_.*/Scene", spawn_cfg)

        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

        self.scene.clone_environments(copy_from_source=False)

    def _get_observations(self) -> dict:
        return {}

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        pass

    def _apply_action(self) -> None:
        pass

    def _get_rewards(self) -> torch.Tensor:
        return torch.zeros(self.num_envs, device=self.device)

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        terminated = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        time_out = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        return terminated, time_out


def main():
    """Run a zero-action agent on the given USD scene."""
    usd_path = args_cli.usd_path
    if not os.path.exists(usd_path):
        raise FileNotFoundError(f"USD file not found: '{usd_path}'")

    env_cfg = UsdViewerEnvCfg()
    env_cfg.sim.device = args_cli.device
    if args_cli.disable_fabric:
        env_cfg.sim.use_fabric = False
    env = UsdViewerEnv(cfg=env_cfg, usd_path=usd_path)

    print(f"[INFO]: Observation space: {env.observation_space}")
    print(f"[INFO]: Action space: {env.action_space}")

    while simulation_app.is_running():
        with torch.inference_mode():
            actions = torch.zeros(env.action_space.shape, device=env.unwrapped.device)
            env.step(actions)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
