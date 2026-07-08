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
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_drawer_tasks_base import LiberoDrawerTasksBase


class L90K10CloseTheTopDrawerOfTheCabinet(LiberoDrawerTasksBase):
    """
    L90K10CloseTheTopDrawerOfTheCabinet: close the top drawer of the cabinet (Scene10)

    Steps:
        close the top drawer of the cabinet

    """

    task_name: str = "L90K10CloseTheTopDrawerOfTheCabinet"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Close the top drawer of the cabinet."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        bowl_placement = dict(
            fixture=self.table,
            pos=(0.0, -0.60),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.5),
        )
        butter_placement = dict(
            fixture=self.table,
            pos=(-0.3, -0.80),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.3, 0.3),
        )
        chocolate_pudding_placement = dict(
            fixture=self.table,
            pos=(0.3, -0.80),
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
            )
        )
        cfgs.append(
            dict(
                name=self.butter,
                obj_groups="butter",
                graspable=True,
                placement=butter_placement,
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
        cabinet_closed = self.drawer.is_closed(env, [self.top_drawer_joint_name])
        return cabinet_closed
