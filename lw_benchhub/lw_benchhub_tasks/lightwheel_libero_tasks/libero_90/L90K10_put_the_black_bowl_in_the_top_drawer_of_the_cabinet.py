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

import torch
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_drawer_tasks_base import DrawerTasksWithoutWineRackBase


class L90K10PutTheBlackBowlInTheTopDrawerOfTheCabinet(DrawerTasksWithoutWineRackBase):
    """
    L90K10PutTheBlackBowlInTheTopDrawerOfTheCabinet: put the black bowl in the top drawer of the cabinet (Scene10)

    Steps:
        1. open the top drawer of the cabinet
        2. pick up the black bowl
        3. put the black bowl in the top drawer of the cabinet

    """

    task_name: str = "L90K10PutTheBlackBowlInTheTopDrawerOfTheCabinet"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the black bowl in the top drawer of the cabinet."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        # According to task.csv, need: akita_black_bowl, butter, chocolate_pudding
        bowl_placement = dict(
            fixture=self.table,
            pos=(-0.3, -0.8),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.5),
        )
        butter_placement_1 = dict(
            fixture=self.table,
            pos=(0.3, -0.80),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.3, 0.3),
        )
        butter_placement_2 = dict(
            fixture=self.table,
            pos=(0.3, -0.3),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.3, 0.3),
        )
        chocolate_pudding_placement = dict(
            fixture=self.table,
            pos=(-0.3, -0.3),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.3, 0.3),
        )

        cfgs.append(
            dict(
                name=self.akita_black_bowl,
                obj_groups="bowl",
                graspable=True,
                placement=bowl_placement,
                asset_name="Bowl008.usd",
                object_scale=0.7,
            )
        )
        cfgs.append(
            dict(
                name=self.butter_1,
                obj_groups="butter",
                graspable=True,
                placement=butter_placement_1,
                asset_name="Butter001.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.butter_2,
                obj_groups="butter",
                graspable=True,
                placement=butter_placement_2,
                asset_name="Butter001.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.chocolate_pudding,
                obj_groups="chocolate_pudding",
                graspable=True,
                placement=chocolate_pudding_placement,
                asset_name="ChocolatePudding001.usd",
            )
        )
        return cfgs

    def _check_success(self, env):
        bowl_in_drawer = OU.obj_inside_of(env, self.akita_black_bowl, self.drawer)
        gripper_far = OU.gripper_obj_far(env, self.akita_black_bowl)
        return bowl_in_drawer & gripper_far
