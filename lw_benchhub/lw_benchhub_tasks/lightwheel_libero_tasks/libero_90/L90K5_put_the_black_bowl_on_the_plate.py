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

import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_black_bowl_and_plate_base import LiberoBlackBowlAndPlateBase


class L90K5PutTheBlackBowlOnThePlate(LiberoBlackBowlAndPlateBase):
    """
    L90K5PutTheBlackBowlOnThePlate: put the black bowl on the plate

    Steps:
        pick up the black bowl
        put the black bowl on the plate

    """

    task_name: str = "L90K5PutTheBlackBowlOnThePlate"

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        # names used in success checks
        self.akita_black_bowl = "akita_black_bowl"
        self.plate = "plate"
        self.ketchup = "ketchup"

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        self.top_drawer_joint_name = list(self.drawer._joint_infos.keys())[0]
        self.drawer.set_joint_state(0.8, 1.0, env, [self.top_drawer_joint_name])

    def _get_obj_cfgs(self):
        cfgs = []

        plate_placement = dict(
            fixture=self.counter,
            pos=(0.55, -0.85),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.35, 0.35),
        )
        bowl_placement = dict(
            fixture=self.counter,
            pos=(-0.05, -0.25),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.35, 0.35),
        )
        ketchup_placement = dict(
            fixture=self.counter,
            pos=(0.20, -0.8),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.25, 0.25),
        )

        cfgs.append(
            dict(
                name=self.plate,
                obj_groups="plate",
                graspable=False,
                placement=plate_placement,
                asset_name="Plate012.usd",
                init_robot_here=True,
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
                name=self.ketchup,
                obj_groups="ketchup",
                graspable=True,
                placement=ketchup_placement,
                asset_name="Ketchup003.usd",
            )
        )

        return cfgs

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the black bowl on the plate."
        return ep_meta

    def _check_success(self, env):
        success = OU.check_place_obj1_on_obj2(
            env,
            self.akita_black_bowl,
            self.plate,
            th_z_axis_cos=0.95,
            th_xy_dist=0.25,
            th_xyz_vel=0.5,
        )
        return success
