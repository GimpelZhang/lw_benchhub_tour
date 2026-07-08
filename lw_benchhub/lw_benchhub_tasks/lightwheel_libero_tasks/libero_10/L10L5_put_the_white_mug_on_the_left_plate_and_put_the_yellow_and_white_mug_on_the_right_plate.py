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
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90L5_put_the_white_mug_on_the_left_plate import L90L5PutTheWhiteMugOnTheLeftPlate


class L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate(L90L5PutTheWhiteMugOnTheLeftPlate):
    task_name: str = "L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Put the white mug on the left plate and put the yellow and white mug on the right plate."
        return ep_meta

    def _check_success(self, env):
        ret = OU.check_place_obj1_on_obj2(env, "porcelain_mug", "plate_left")
        ret1 = OU.check_place_obj1_on_obj2(env, "porcelain_mug", "plate")
        porcelain_mug_success = ret | ret1

        ret_right = OU.check_place_obj1_on_obj2(env, "white_yellow_mug", "plate")
        ret_right2 = OU.check_place_obj1_on_obj2(env, "white_yellow_mug", "plate_left")
        white_yellow_mug_success = ret_right | ret_right2
        return porcelain_mug_success & white_yellow_mug_success
