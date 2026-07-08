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

from .lift_obj import agents as lift_obj_agents

import gymnasium as gym
gym.register(
    id="Robocasa-Rl-G1LiftObjStateRL",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:G1LiftObjStateRL",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Rl-G1LiftObjVisualRL",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:G1LiftObjVisualRL",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Rl-LeRobotLiftObjStateRL",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:LeRobotLiftObjStateRL",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Rl-LeRobotLiftObjVisualRL",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:LeRobotLiftObjVisualRL",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Rl-LeRobotLiftObjDigitalTwin",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:LeRobotLiftObjDigitalTwin",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Rl-LeRobot100LiftObjStateRL",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.lift_obj.lift_obj:LeRobot100LiftObjStateRL",
        "skrl_cfg_entry_point": f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
    },
    disable_env_checker=True,
)
