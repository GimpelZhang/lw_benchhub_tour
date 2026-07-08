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
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90S1_pick_up_the_book_and_place_it_in_the_front_compartment_of_the_caddy import L90S1PickUpTheBookAndPlaceItInTheFrontCompartmentOfTheCaddy


class L90S3PickUpTheBookAndPlaceItInTheFrontCompartmentOfTheCaddy(L90S1PickUpTheBookAndPlaceItInTheFrontCompartmentOfTheCaddy):

    task_name: str = 'L90S3PickUpTheBookAndPlaceItInTheFrontCompartmentOfTheCaddy'

    def _get_obj_cfgs(self):
        cfgs = []

        cfgs.append(
            dict(
                name=self.desk_caddy,
                obj_groups=self.desk_caddy,
                graspable=True,
                object_scale=2.0,
                placement=dict(
                    fixture=self.dining_table,
                    size=(0.6, 0.6),
                    pos=(-0.5, -0.3),
                    rotation=np.pi / 8.0,
                ),
                asset_name="DeskCaddy001.usd",
            )
        )

        cfgs.append(
            dict(
                name=self.book,
                obj_groups="book",
                graspable=True,
                object_scale=0.4,
                placement=dict(
                    fixture=self.dining_table,
                    size=(0.25, 0.25),
                    pos=(-0.3, -0.7),
                    ensure_valid_placement=True,
                ),
                asset_name="Book042.usd",
            )
        )

        cfgs.append(
            dict(
                name=self.mug,
                obj_groups="mug",
                graspable=True,
                placement=dict(
                    fixture=self.dining_table,
                    size=(0.25, 0.25),
                    pos=(0.0, -0.6),
                    ensure_valid_placement=True,
                ),
                asset_name="Cup012.usd",
            )
        )

        return cfgs
