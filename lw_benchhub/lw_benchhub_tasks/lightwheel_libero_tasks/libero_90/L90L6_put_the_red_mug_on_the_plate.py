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

from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass
import lw_benchhub.core.mdp as mdp
import lw_benchhub.utils.object_utils as OU
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_10.L10L6_MugOnAndChocolateRightPlate import L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate


class L90L6PutTheRedMugOnThePlate(L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate):
    """
    L90L6PutTheRedMugOnThePlate: put the red mug on the right plate
    """

    task_name: str = "L90L6PutTheRedMugOnThePlate"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick up the red mug and put it on the plate"
        return ep_meta

    def _check_success(self, env):
        return OU.check_place_obj1_on_obj2(
            env,
            self.red_coffee_mug,
            self.plate,
            th_z_axis_cos=0.95,  # verticality
            th_xy_dist=0.4,    # within 0.4 diameter
            th_xyz_vel=0.5     # velocity vector length less than 0.5
        )
