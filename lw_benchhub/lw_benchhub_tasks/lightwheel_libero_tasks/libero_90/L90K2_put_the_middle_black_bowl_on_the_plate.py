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


class L90K2PutTheMiddleBlackBowlOnThePlate(LiberoBlackBowlAndPlateBase):
    """
    L90K2PutTheMiddleBlackBowlOnThePlate: put the black bowl in the middle on the plate

    Steps:
        pick up the black bowl
        put the black bowl in the middle on the plate

    """

    task_name: str = "L90K2PutTheMiddleBlackBowlOnThePlate"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Put the black bowl in the middle on the plate."
        return ep_meta

    def _check_success(self, env):
        success = OU.check_place_obj1_on_obj2(
            env,
            self.akita_black_bowl_middle,
            self.plate,
            th_z_axis_cos=0.95,  # verticality
            th_xy_dist=0.7,    # within 0.4 diameter
            th_xyz_vel=0.5     # velocity vector length less than 0.5
        )
        return success
