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


class L90L1PickUpTheKetchupAndPutItInTheBasket(Libero10PutInBasket):
    """
    L90L1PickUpTheKetchupAndPutItInTheBasket: pick up the ketchup and put it in the basket

    Steps:
        pick up the ketchup
        put the ketchup in the basket

    """

    task_name: str = "L90L1PickUpTheKetchupAndPutItInTheBasket"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick up the ketchup, and put it in the basket."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = super()._get_obj_cfgs()
        pop_objs = [self.milk, self.orange_juice, self.butter]
        cfg_index = 0
        while cfg_index < len(cfgs):
            if cfgs[cfg_index]['name'] in pop_objs:
                cfgs.pop(cfg_index)
            else:
                cfg_index += 1
        return cfgs

    def _check_success(self, env):
        return OU.check_place_obj1_on_obj2(
            env,
            self.ketchup,
            self.basket,
            th_z_axis_cos=0,  # verticality
            th_xy_dist=0.4,    # within 0.4 diameter
            th_xyz_vel=0.5     # velocity vector length less than 0.5
        )
