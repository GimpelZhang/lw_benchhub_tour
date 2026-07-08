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
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_goal_tasks_base import LiberoGoalTasksBase


class LGOpenTheMiddleDrawerOfTheCabinet(LiberoGoalTasksBase):
    """
    LGOpenTheMiddleDrawerOfTheCabinet: open the middle layer of the drawer

    Steps:
        1. open the middle drawer of the cabinet

    """

    task_name: str = "LGOpenTheMiddleDrawerOfTheCabinet"
    # EXCLUDE_LAYOUTS: list = LiberoEnvCfg.DINING_COUNTER_EXCLUDED_LAYOUTS

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Open the middle layer of the drawer."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        # According to task.csv, need: akita_black_bowl, cream_cheese, plate, wine_bottle
        plate_placement = dict(
            fixture=self.table,
            pos=(0.4, -0.30),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.7, 0.5),
        )
        bowl_placement = dict(
            fixture=self.table,
            pos=(-0.3, 0.20),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.6, 0.7),
        )
        wine_bottle_placement = dict(
            fixture=self.table,
            pos=(-0.1, -0.30),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.5),
        )
        cream_cheese_placement = dict(
            fixture=self.table,
            pos=(0, -0.70),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.7, 0.5),
        )

        cfgs.append(
            dict(
                name=self.plate,
                obj_groups="plate",
                graspable=False,
                placement=plate_placement,
                asset_name="Plate012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.akita_black_bowl,
                obj_groups="bowl",
                graspable=True,
                placement=bowl_placement,
                asset_name="Bowl008.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.wine_bottle,
                obj_groups="bottle",
                graspable=True,
                placement=wine_bottle_placement,
                object_scale=0.8,
                asset_name="Bottle054.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.cream_cheese,
                obj_groups="cream_cheese",
                graspable=True,
                placement=cream_cheese_placement,
                asset_name="CreamCheeseStick013.usd",
            )
        )

        return cfgs

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        # Get the middle drawer joint name (second joint if available, else first)
        if hasattr(self.drawer, '_joint_infos') and self.drawer._joint_infos:
            joint_names = list(self.drawer._joint_infos.keys())
            self.middle_drawer_joint_name = joint_names[1]  # Second joint is middle drawer
            self.drawer.set_joint_state(0.0, 0.0, env, [self.middle_drawer_joint_name])
        else:
            # Use default joint name if joint info is not available
            self.middle_drawer_joint_name = "drawer_joint_2"

    def _check_success(self, env):
        # Check if the middle drawer is open
        drawer_open = self.drawer.is_open(env, [self.middle_drawer_joint_name], th=0.6)
        return drawer_open & OU.gripper_obj_far(env, self.drawer.name, th=0.4)
