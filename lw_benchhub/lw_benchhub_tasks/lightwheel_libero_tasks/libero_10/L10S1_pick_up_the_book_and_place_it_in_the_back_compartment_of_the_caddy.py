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
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90S3_pick_up_the_book_and_place_it_in_the_right_compartment_of_the_caddy import L90S3PickUpTheBookAndPlaceItInTheRightCompartmentOfTheCaddy


class L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy(L90S3PickUpTheBookAndPlaceItInTheRightCompartmentOfTheCaddy):

    task_name: str = "L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy"

    def _get_obj_cfgs(self):
        cfgs = []
        cfgs.append(
            dict(
                name="black_book",
                obj_groups="book",
                object_scale=0.4,
                graspable=True,
                asset_name="Book042.usd",
                placement=dict(
                    fixture=self.counter,
                    size=(0.5, 0.3),
                    margin=0.02,
                    pos=(-0.3, -0.5)
                ),
            )
        )
        cfgs.append(
            dict(
                name="desk_caddy",
                obj_groups="desk_caddy",
                graspable=True,
                object_scale=2.0,
                init_robot_here=True,
                asset_name="DeskCaddy001.usd",
                placement=dict(
                    fixture=self.counter,
                    size=(0.8, 0.45),
                    margin=0.02,
                    pos=(0.3, -0.5)
                ),
            )
        )
        cfgs.append(
            dict(
                name="white_yellow_mug",
                obj_groups="cup",
                graspable=True,
                asset_name="Cup014.usd",
                placement=dict(
                    fixture=self.counter,
                    size=(0.5, 0.3),
                    margin=0.02,
                    pos=(-0.1, -0.5)
                ),
            )
        )
        return cfgs
