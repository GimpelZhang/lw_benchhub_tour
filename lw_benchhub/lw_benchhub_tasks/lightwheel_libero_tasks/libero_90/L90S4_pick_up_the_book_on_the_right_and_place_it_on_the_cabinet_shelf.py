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
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_book_in_caddy_base import StudySceneBase


class L90S4PickUpTheBookOnTheRightAndPlaceItOnTheCabinetShelf(StudySceneBase):
    task_name: str = "L90S4PickUpTheBookOnTheRightAndPlaceItOnTheCabinetShelf"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Pick up the book on the right and place it on the cabinet shelf."
        return ep_meta

    def _check_success(self, env):
        # Check if yellow book (right book) is placed on top of the desk_caddy (cabinet shelf)
        book_on_shelf_result = OU.check_place_obj1_on_obj2(
            env,
            self.yellow_book,
            self.shelf,
            th_z_axis_cos=0.0,
            th_xy_dist=0.25,
            th_xyz_vel=0.5
        )
        return book_on_shelf_result
