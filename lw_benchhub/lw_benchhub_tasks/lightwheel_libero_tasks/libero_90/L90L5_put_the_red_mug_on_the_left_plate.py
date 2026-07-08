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


class L90L5PutTheRedMugOnTheLeftPlate(LiberoMugPlacementBase):
    """
    L90L5PutTheRedMugOnTheLeftPlate: put the red mug on the left plate

    Steps:
        pick up the red mug
        put the red mug on the left plate

    """

    task_name: str = "L90L5PutTheRedMugOnTheLeftPlate"
    # EXCLUDE_LAYOUTS: list = LiberoEnvCfg.DINING_COUNTER_EXCLUDED_LAYOUTS

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.red_coffee_mug = "red_coffee_mug"
        self.plate_left = "plate_left"
        self.plate_right = "plate_right"
        self.porcelain_mug = "porcelain_mug"
        self.white_yellow_mug = "white_yellow_mug"

    def _get_obj_cfgs(self):
        cfgs = []

        plate_left_placement = dict(
            fixture=self.counter,
            size=(0.5, 0.5),
            pos=(-0.6, -0.4),
            margin=0.02,
            ensure_valid_placement=True,
        )
        plate_right_placement = dict(
            fixture=self.counter,
            size=(0.5, 0.5),
            pos=(0.6, -0.4),
            margin=0.02,
            ensure_valid_placement=True,
        )
        red_mug_placement = dict(
            fixture=self.counter,
            size=(0.5, 0.5),
            pos=(0.0, -1.2),
            margin=0.02,
            ensure_valid_placement=True,
        )
        white_yellow_mug_placement = dict(
            fixture=self.counter,
            size=(0.5, 0.5),
            pos=(-0.3, -0.8),
            margin=0.02,
            ensure_valid_placement=True,
        )
        porcelain_mug_placement = dict(
            fixture=self.counter,
            size=(0.5, 0.5),
            pos=(0.3, -0.8),
            margin=0.02,
            ensure_valid_placement=True,
        )

        cfgs.append(
            dict(
                name=self.plate_left,
                obj_groups="plate",
                graspable=False,
                placement=plate_left_placement,
                asset_name="Plate012.usd",
                init_robot_here=True,
            )
        )
        cfgs.append(
            dict(
                name=self.plate_right,
                obj_groups="plate",
                graspable=False,
                placement=plate_right_placement,
                asset_name="Plate012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.red_coffee_mug,
                obj_groups="cup",
                graspable=True,
                placement=red_mug_placement,
                asset_name="Cup030.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.porcelain_mug,
                obj_groups="cup",
                graspable=True,
                placement=porcelain_mug_placement,
                asset_name="Cup012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.white_yellow_mug,
                obj_groups="cup",
                graspable=True,
                placement=white_yellow_mug_placement,
                asset_name="Cup014.usd",
            )
        )

        return cfgs

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the red mug on the left plate."
        return ep_meta

    def _check_success(self, env):
        success = OU.check_place_obj1_on_obj2(
            env,
            'red_coffee_mug',
            'plate_left'
        )
        return success
