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

import numpy as np
import torch
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_mug_placement_base import LiberoMugPlacementBase


class L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug(LiberoMugPlacementBase):
    """
    L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug: put the yellow and white mug to the front of the white mug

    Steps:
        pick up the yellow and white mug
        put the yellow and white mug to the front of the white mug

    """

    task_name: str = "L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug"
    # EXCLUDE_LAYOUTS: list = LiberoEnvCfg.DINING_COUNTER_EXCLUDED_LAYOUTS
    enable_fixtures = ['microwave']

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.white_yellow_mug = "white_yellow_mug"
        self.porcelain_mug = "porcelain_mug"
        self.microwave = self.register_fixture_ref("microwave", dict(id=FixtureType.MICROWAVE))

    def _setup_scene(self, env, env_ids=None):
        super()._setup_scene(env, env_ids)
        self.microwave.set_joint_state(0.9, 1.0, env, self.microwave.door_joint_names)

    def _get_obj_cfgs(self):
        cfgs = []

        white_mug_placement = dict(
            fixture=self.counter,
            size=(0.3, 0.3),
            pos=(0.2, -0.6),
            margin=0.02,
            ensure_valid_placement=True,
        )
        yellow_white_mug_placement = dict(
            fixture=self.counter,
            size=(0.3, 0.3),
            pos=(-0.2, -0.2),
            rotation=-np.pi / 2.0,
            margin=0.02,
            ensure_valid_placement=True,
        )

        cfgs.append(
            dict(
                name=self.porcelain_mug,
                obj_groups="cup",
                graspable=False,
                placement=white_mug_placement,
                asset_name="Cup012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.white_yellow_mug,
                obj_groups="cup",
                graspable=True,
                placement=yellow_white_mug_placement,
                asset_name="Cup014.usd",
            )
        )

        return cfgs

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the yellow and white mug to the front of the white mug."
        return ep_meta

    def _check_success(self, env):
        return OU.check_place_obj1_side_by_obj2(
            env,
            self.white_yellow_mug,
            self.porcelain_mug,
            {
                "gripper_far": True,
                "contact": False,
                "side": "front",
                "side_threshold": 0.7,
                "margin_threshold": [0.001, 0.2],
                "stable_threshold": 0.5,
            }
        )
