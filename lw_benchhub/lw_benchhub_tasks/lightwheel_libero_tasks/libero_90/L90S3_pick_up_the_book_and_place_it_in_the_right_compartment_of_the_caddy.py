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
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase


class L90S3PickUpTheBookAndPlaceItInTheRightCompartmentOfTheCaddy(LwTaskBase):
    task_name: str = "L90S3PickUpTheBookAndPlaceItInTheRightCompartmentOfTheCaddy"

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.init_robot_base_ref = self.counter

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick up the book and place it in the right compartment of the caddy."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        placement = dict(
            fixture=self.counter,
            size=(0.8, 0.4),
            pos=(0.0, -0.6),
            offset=(-0.05, 0),
            ensure_valid_placement=True,
        )
        cfgs.append(
            dict(
                name="desk_caddy",
                obj_groups="desk_caddy",
                graspable=True,
                object_scale=2.0,
                init_robot_here=True,
                asset_name="DeskCaddy001.usd",
                placement=placement,
            )
        )
        cfgs.append(
            dict(
                name="black_book",
                object_scale=0.4,
                obj_groups="book",
                graspable=True,
                asset_name="Book042.usd",
                placement=dict(
                    fixture=self.counter,
                    size=(0.4, 0.3),
                    pos=(0.2, -0.9),
                    offset=(-0.05, 0),
                    ensure_valid_placement=True,
                ),
            )
        )
        cfgs.append(
            dict(
                name="porcelain_mug",
                obj_groups="cup",
                graspable=True,
                asset_name="Cup012.usd",
                placement=placement,
            )
        )
        cfgs.append(
            dict(
                name="red_coffee_mug",
                obj_groups="cup",
                graspable=True,
                asset_name="Cup030.usd",
                placement=placement,
            )
        )
        return cfgs

    def _check_success(self, env):
        book_success = OU.check_obj_in_receptacle(env, "black_book", "desk_caddy")
        gipper_far_success = OU.gripper_obj_far(env, "black_book", 0.35)
        return book_success & gipper_far_success
