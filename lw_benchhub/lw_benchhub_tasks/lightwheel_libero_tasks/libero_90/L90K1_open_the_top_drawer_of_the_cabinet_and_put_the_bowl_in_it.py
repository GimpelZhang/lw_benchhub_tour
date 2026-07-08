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


class L90K1OpenTheTopDrawerOfTheCabinetAndPutTheBowlInIt(LiberoDrawerTasksBase):
    """
    L90K1OpenTheTopDrawerOfTheCabinetAndPutTheBowlInIt: open the top drawer of the cabinet and put the bowl in it

    Steps:
        open the top drawer of the cabinet
        pick up the bowl
        put the bowl in the top drawer of the cabinet

    """

    task_name: str = "L90K1OpenTheTopDrawerOfTheCabinetAndPutTheBowlInIt"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Open the top drawer of the cabinet and put the bowl in it."
        return ep_meta

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        if hasattr(self.drawer, '_joint_infos') and self.drawer._joint_infos:
            self.top_drawer_joint_name = list(self.drawer._joint_infos.keys())[0]
            self.drawer.set_joint_state(0.0, 0.0, env, [self.top_drawer_joint_name])
        else:
            self.top_drawer_joint_name = "drawer_joint_1"

    def _get_obj_cfgs(self):
        cfgs = []

        bowl_placement = dict(
            fixture=self.table,
            pos=(0.0, -0.60),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.5),
        )
        plate_placement = dict(
            fixture=self.table,
            pos=(0.0, -0.80),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.7, 0.7),
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
                name=self.plate,
                obj_groups="plate",
                graspable=False,
                placement=plate_placement,
                asset_name="Plate012.usd",
            )
        )

        return cfgs

    def _check_success(self, env):
        bowl_in_drawer = OU.obj_inside_of(env, self.akita_black_bowl, self.drawer)
        gripper_far = OU.gripper_obj_far(env, self.akita_black_bowl)
        return bowl_in_drawer & gripper_far
