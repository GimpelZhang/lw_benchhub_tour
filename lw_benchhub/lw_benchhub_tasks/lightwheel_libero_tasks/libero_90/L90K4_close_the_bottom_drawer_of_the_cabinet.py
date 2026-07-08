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


class L90K4CloseTheBottomDrawerOfTheCabinet(LiberoDrawerTasksBase):
    """
    L90K4CloseTheBottomDrawerOfTheCabinet: close the bottom drawer of the cabinet

    Steps:
        close the bottom drawer of the cabinet

    """

    task_name: str = "L90K4CloseTheBottomDrawerOfTheCabinet"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Close the bottom drawer of the cabinet."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        bowl_placement = dict(
            fixture=self.table,
            pos=(0.0, -0.30),
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
                name=f"wine_bottle",
                obj_groups=["bottle"],
                graspable=True,
                washable=True,
                object_scale=0.8,
                asset_name="Bottle054.usd",
                init_robot_here=True,
                placement=dict(
                    fixture=self.table,
                    size=(0.50, 0.35),
                    margin=0.02,
                    pos=(0.2, -0.3),
                ),
            )
        )

        return cfgs

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        if hasattr(self.drawer, '_joint_infos') and self.drawer._joint_infos:
            joint_names = list(self.drawer._joint_infos.keys())
            self.bottom_drawer_joint_name = joint_names[-1]
            self.top_drawer_joint_name = joint_names[0]
            self.drawer.set_joint_state(0, 0, env, [self.top_drawer_joint_name])
            self.drawer.set_joint_state(0.8, 0.9, env, [self.bottom_drawer_joint_name])
        else:
            # Use default joint name if joint info is not available
            self.bottom_drawer_joint_name = "drawer_joint_2"

    def _check_success(self, env):
        cabinet_closed = self.drawer.is_closed(env, [self.bottom_drawer_joint_name])
        return cabinet_closed & OU.gripper_obj_far(env, self.drawer.name)
