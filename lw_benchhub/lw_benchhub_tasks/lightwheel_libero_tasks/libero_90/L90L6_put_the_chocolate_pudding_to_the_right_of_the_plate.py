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
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_relative_placement_base import RelativePlacementBase


class L90L6PutTheChocolatePuddingToTheRightOfThePlate(RelativePlacementBase):
    task_name: str = "L90L6PutTheChocolatePuddingToTheRightOfThePlate"
    relation: str = "right"
    obj_name: str = "chocolate_pudding"
    ref_name: str = "plate"
    obj_groups = "chocolate_pudding"
    ref_groups = "plate"
    obj_asset_name = None
    ref_asset_name = None

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Put the chocolate pudding to the right of the plate."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        plate_placement = dict(
            fixture=self.counter,
            pos=(0.2, 0.10),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.50, 0.50),
        )
        pudding_placement = dict(
            fixture=self.counter,
            pos=(0, -0.35),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.70, 0.70),
        )
        mug_l_placement = dict(
            fixture=self.counter,
            pos=(0.55, -0.55),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.25, 0.25),
        )
        mug_r_placement = dict(
            fixture=self.counter,
            pos=(0.20, -1.00),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.25, 0.25),
        )

        cfgs.append(
            dict(
                name=self.ref_name,
                obj_groups=self.ref_groups,
                graspable=False,
                placement=plate_placement,
                init_robot_here=True,
                asset_name="Plate012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.obj_name,
                obj_groups=self.obj_groups,
                graspable=True,
                placement=pudding_placement,
                asset_name="ChocolatePudding001.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.porcelain_mug,
                obj_groups="cup",
                graspable=True,
                placement=mug_l_placement,
                asset_name="Cup012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.red_coffee_mug,
                obj_groups="cup",
                graspable=True,
                placement=mug_r_placement,
                asset_name="Cup030.usd",
            )
        )

        return cfgs

    def _check_success(self, env):
        return OU.check_place_obj1_side_by_obj2(env, self.obj_name, self.ref_name, {
            "gripper_far": True,   # obj1 and obj2 should be far from the gripper
            "contact": False,   # obj1 should not be in contact with obj2
            "side": 'right',    # relative position of obj1 to obj2
            "side_threshold": 0.25,    # threshold for distance between obj1 and obj2 in other directions
            "margin_threshold": [0.001, 0.1],    # threshold for distance between obj1 and obj2
            "stable_threshold": 0.5,    # threshold for stable, velocity vector length less than 0.5
        },
            gipper_th=0.35)
