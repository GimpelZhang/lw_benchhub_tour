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


class L90K10CloseTheTopDrawerOfTheCabinetAndPutTheBlackBowlOnTopOfIt(LiberoDrawerTasksBase):
    """
    L90K10CloseTheTopDrawerOfTheCabinetAndPutTheBlackBowlOnTopOfIt: close the top drawer of the cabinet and put the black bowl on top of it

    Steps:
        1. close the top drawer of the cabinet
        2. put the black bowl on top of the drawer

    """

    task_name: str = "L90K10CloseTheTopDrawerOfTheCabinetAndPutTheBlackBowlOnTopOfIt"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Close the top drawer of the cabinet and put the black bowl on top of it."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        # According to task.csv, need: akita_black_bowl, butter, chocolate_pudding
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

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        # Get the top drawer joint name (first joint)
        if hasattr(self.drawer, '_joint_infos') and self.drawer._joint_infos:
            self.top_drawer_joint_name = list(self.drawer._joint_infos.keys())[0]
            # Set the top drawer to semi-open state
            self.drawer.set_joint_state(0.1, 0.2, env, [self.top_drawer_joint_name])
        else:
            # Use default joint name if joint info is not available
            self.top_drawer_joint_name = "drawer_joint_1"

    def _check_success(self, env):
        # Check if the top drawer is closed
        drawer_closed = self.drawer.is_closed(env, [self.top_drawer_joint_name])
        bowl_pos = env.scene.rigid_objects[self.akita_black_bowl].data.root_pos_w[0, :].cpu().numpy()
        bowl_on_drawer = OU.point_in_fixture(bowl_pos, self.drawer, only_2d=True)
        bowl_on_drawer_tensor = torch.tensor(bowl_on_drawer, dtype=torch.bool, device=env.device).repeat(env.num_envs)
        # Check if gripper is far from the bowl
        gripper_far = OU.gripper_obj_far(env, self.akita_black_bowl)

        return drawer_closed & bowl_on_drawer_tensor & gripper_far
