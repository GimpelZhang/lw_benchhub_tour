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

from isaaclab_arena.assets.background import Background
from isaaclab_arena.environments.isaaclab_arena_manager_based_env import IsaacLabArenaManagerBasedRLEnvCfg
from isaaclab_arena.scene.scene import Scene

from lw_benchhub.core.context import get_context
from lw_benchhub.core.models.scenes.scene_parser import get_fixture_cfgs, parse_fixtures
from lw_benchhub.utils.isaaclab_utils import NoDeepcopyMixin
from lw_benchhub.utils.isaaclab_utils.assets.general_asset_arena import GeneralAssetArena
from lw_benchhub.utils.usd_utils import OpenUsd as usd


class LocalScene(Scene, NoDeepcopyMixin):
    def __init__(self, **kwargs):
        super().__init__()
        self.context = get_context()
        self.num_envs = self.context.num_envs
        self.scene_name = self.context.scene_name
        self.scene_usd_path = self.context.scene_name
        self.scene_backend = self.context.scene_backend
        self.scene_type = "local"
        self.stage = None
        self.fixtures = {}
        self.fxtr_placements = {}
        self.is_replay_mode = False
        assert self.scene_usd_path.endswith(".usd"), "Scene USD path must end with .usd"
        if self.context.usd_simplify:
            self.stage = usd.get_stage(self.scene_usd_path)

    def setup_env_config(self, orchestrator):
        # Parse fixtures from local USD scene to support fixture-dependent tasks.
        self.stage = usd.get_stage(self.scene_usd_path)
        self.fixtures = parse_fixtures(
            self.stage,
            self.context.num_envs,
            self.context.seed,
            self.context.device,
        )
        self.fxtr_placements = {}
        self.fixture_cfgs = get_fixture_cfgs(self)
        print(f"[LocalScene Debug] Parsed fixtures count: {len(self.fixtures)}")

        if self.context.enable_full_local_scene:
            background = GeneralAssetArena(
                name="Scene",
                usd_path=self.scene_usd_path,
                object_min_z=0.1,
            )
        else:
            background = Background(
                name="Scene",
                usd_path=self.scene_usd_path,
                object_min_z=0.1,
            )
        # flush self.assets
        self.assets = {}
        self.add_asset(background)

    def get_ep_meta(self):
        return {
            "floorplan_version": None,
        }

    def modify_env_cfg(self, env_cfg: IsaacLabArenaManagerBasedRLEnvCfg):
        env_cfg.scene_backend = self.scene_backend
        env_cfg.sim.render.enable_translucency = True
        env_cfg.num_envs = self.num_envs

        if self.context.enable_global_illumination:
            env_cfg.sim.render.enable_global_illumination = True

        return env_cfg
