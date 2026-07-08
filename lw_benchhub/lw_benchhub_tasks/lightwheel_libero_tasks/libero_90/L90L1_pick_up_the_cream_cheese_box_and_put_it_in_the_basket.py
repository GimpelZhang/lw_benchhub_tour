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
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_10.L10L2_put_objects_in_basket import Libero10PutInBasket
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90L1_pick_up_the_ketchup_and_put_it_in_the_basket import L90L1PickUpTheKetchupAndPutItInTheBasket


class L90L1PickUpTheCreamCheeseBoxAndPutItInTheBasket(L90L1PickUpTheKetchupAndPutItInTheBasket):
    """
    L90L1PickUpTheCreamCheeseBoxAndPutItInTheBasket: pick up the cream cheese box and put it in the basket

    Steps:
        pick up the cream cheese box
        put the cream cheese box in the basket

    """

    task_name: str = "L90L1PickUpTheCreamCheeseBoxAndPutItInTheBasket"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick up the cream cheese box, and put it in the basket."
        return ep_meta

    def _check_success(self, env):
        return OU.check_place_obj1_on_obj2(
            env,
            self.cream_cheese,
            self.basket,
            th_z_axis_cos=0.0,  # verticality
            th_xy_dist=0.4,    # within 0.4 diameter
            th_xyz_vel=0.5     # velocity vector length less than 0.5
        )
