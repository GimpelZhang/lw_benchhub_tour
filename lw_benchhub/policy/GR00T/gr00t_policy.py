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

import os
import sys
import importlib.util
from pathlib import Path

current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
isaac_gr00t_path = os.path.join(parent_directory, "Isaac-GR00T")
sys.path.append(isaac_gr00t_path)

import numpy as np
import torch
from typing import Dict, Any
from policy.base import BasePolicy

try:
    from gr00t.configs.data.embodiment_configs import MODALITY_CONFIGS
    from gr00t.policy.gr00t_policy import Gr00tPolicy
    from gr00t.data.embodiment_tags import EmbodimentTag
except ImportError as e:
    print(f"gr00t not found, please install gr00t first: {e}, if you not run gr00t policy, please ignore this error")


def _load_modality_config(config_path: str):
    """Dynamically load a modality config .py file to trigger register_modality_config."""
    spec = importlib.util.spec_from_file_location("modality_config", config_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


class GR00TPolicy(BasePolicy):
    """GR00T Policy Implementation"""

    def __init__(self, usr_args):
        super().__init__(usr_args)

    def _load_policy(self):
        """Load the policy from the model path."""
        # If a modality config file path is provided, load it to register the config
        modality_config_path = self.usr_args.get("modality_config_path", None)
        if modality_config_path:
            _load_modality_config(modality_config_path)

        embodiment_tag = self.usr_args["embodiment_tag"]
        if embodiment_tag in MODALITY_CONFIGS:
            self.data_config = MODALITY_CONFIGS[embodiment_tag]
        else:
            raise ValueError(
                f"Invalid embodiment_tag: '{embodiment_tag}'. "
                f"Available: {list(MODALITY_CONFIGS.keys())}"
            )

        return Gr00tPolicy(
            model_path=self.usr_args["checkpoint"],
            embodiment_tag=EmbodimentTag(embodiment_tag),
            device=self.simulation_device,
            strict=False,
        )

    def get_model(self, usr_args):
        """Get GR00T model instance"""
        observation_config = usr_args.get("observation_config", None)
        self.simulation_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.observation_config = observation_config or {}
        self.model = self._load_policy()

    def _build_observation(self, obs: dict) -> dict:
        """Build the nested observation dict expected by Gr00tPolicy.get_action.

        Target format:
            video:    {key: np.ndarray(B, T, H, W, C) uint8}
            state:    {key: np.ndarray(B, T, D) float32}
            language: {key: [[instruction]]}
        """
        custom_mapping = self.observation_config.get("custom_mapping", {})
        video_keys = self.data_config["video"].modality_keys
        state_keys = self.data_config["state"].modality_keys
        language_key = self.data_config["language"].modality_keys[0]

        result = {"video": {}, "state": {}, "language": {}}

        # --- language ---
        result["language"][language_key] = [[self.instruction]]

        # --- video ---
        for vk in video_keys:
            cam_name = custom_mapping.get(vk, vk)
            img = obs[cam_name]
            if torch.is_tensor(img):
                img = img.cpu().numpy()
            if img.dtype != np.uint8:
                img = img.astype(np.uint8)
            # ensure shape (B, T, H, W, C)
            while img.ndim < 5:
                img = img[np.newaxis, ...]
            result["video"][vk] = img

        # --- state ---
        for sk in state_keys:
            src_key = custom_mapping.get(sk, sk)
            state = obs[src_key]
            if torch.is_tensor(state):
                state = state.cpu().numpy()
            state = state.astype(np.float32)
            # ensure shape (B, T, D)
            while state.ndim < 3:
                state = state[np.newaxis, ...]
            result["state"][sk] = state

        return result

    def encode_obs(self, observation):
        """Preprocess raw env observation into Gr00tPolicy input format."""
        observation = super().encode_obs(observation, transpose=False, keep_dim_env=True)
        return self._build_observation(observation)

    def _mapping_action(self, actions: dict) -> torch.Tensor:
        """Concatenate action dict values into a single tensor (B, horizon, D)."""
        parts = [torch.tensor(v, device=self.simulation_device, dtype=torch.float32)
                 for v in actions.values()]
        return torch.cat(parts, dim=-1)

    def get_action(self, observation):
        action_dict, _ = self.model.get_action(observation)
        return self._mapping_action(action_dict)

    def custom_action_mapping(self, action: torch.Tensor) -> torch.Tensor:
        # define your own action mapping here
        return action

    def custom_obs_mapping(self, obs):
        # define your own obs mapping here
        return obs

    def eval(self, task_env: Any, observation: Dict[str, Any],
             usr_args: Dict[str, Any], video_writer: Any) -> bool:
        terminated = False
        states_list = []
        for _ in range(usr_args['time_out_limit']):
            encoded = self.encode_obs(observation)
            encoded = self.custom_obs_mapping(encoded)
            actions = self.get_action(encoded)
            actions = self.custom_action_mapping(actions)
            for i in range(self.usr_args["num_feedback_actions"]):
                observation, terminated, extras = self.step_environment(task_env, actions[:, i], usr_args)
                if usr_args.get('save_states', False) and 'state' in extras:
                    states_list.append(extras['state'])
                self.add_video_frame(video_writer, observation, usr_args['record_camera'])
                if terminated:
                    break
            if terminated:
                break
        if usr_args.get('save_states', False) and states_list:
            torch.save(states_list, Path(usr_args['save_path']) / 'states.pt')
        return terminated

    def reset_model(self):
        pass
