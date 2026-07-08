# Copyright 2025 Lightwheel Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple script to replay saved states from policy evaluation."""

import argparse
from pathlib import Path

import gymnasium as gym
import mediapy as media
import numpy as np
import torch
import yaml

from isaaclab.app import AppLauncher
from lw_benchhub.distributed.restful import DotDict
from lw_benchhub.utils.env import ExecuteMode, parse_env_cfg
from lw_benchhub.utils.place_utils.env_utils import reset_physx

parser = argparse.ArgumentParser(description="Replay saved states.")
parser.add_argument("--config", type=str, required=True, help="Config yaml file")
parser.add_argument("--state_file", type=str, required=True, help="Path to state file")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

with open(args.config, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

app_launcher = AppLauncher(vars(args))
simulation_app = app_launcher.app

env_cfg_dict = DotDict(config["env_cfg"])
env_cfg = parse_env_cfg(scene_backend=env_cfg_dict.scene_backend, task_backend=env_cfg_dict.task_backend,
                        task_name=env_cfg_dict.task, robot_name=env_cfg_dict.robot, scene_name=env_cfg_dict.layout,
                        robot_scale=env_cfg_dict.get('robot_scale', 1.0), execute_mode=ExecuteMode.EVAL,
                        device=env_cfg_dict.device, num_envs=env_cfg_dict.num_envs, enable_cameras=True, replay_cfgs={"add_camera_to_observation": True})
env_name = f"local-{env_cfg_dict.task}-{env_cfg_dict.robot}-v0"
gym.register(id=env_name, entry_point="isaaclab.envs:ManagerBasedRLEnv", kwargs={}, disable_env_checker=True)
env = gym.make(env_name, cfg=env_cfg).unwrapped

reset_physx(env)
env.reset()

states_list = torch.load(args.state_file, map_location=env.device)
video_path = Path(args.state_file).parent / 'replay_video.mp4'
cameras = ['first_person_camera_rgb', 'right_hand_camera_rgb']
with media.VideoWriter(path=video_path, shape=(1024, 1024 * len(cameras)), fps=30) as v:
    for step_idx, state in enumerate(states_list):
        obs, _ = env.reset_to_check_state(state, torch.tensor([0], device=env.device), seed=env.cfg.seed, is_relative=True)
        env.sim.render()
        images = [obs['policy'][cam].cpu().numpy()[0] for cam in cameras if cam in obs['policy']]
        if images:
            combined = np.concatenate(images, axis=1)
            v.add_image(combined)
        print(f"Replayed step {step_idx}/{len(states_list)-1}")

print(f"Replayed all {len(states_list)} steps, video saved to {video_path}")

env.close()
simulation_app.close()
