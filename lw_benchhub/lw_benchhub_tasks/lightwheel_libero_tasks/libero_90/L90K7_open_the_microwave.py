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

from copy import deepcopy
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K7_put_the_white_bowl_to_the_right_of_the_plate import L90K7PutTheWhiteBowlToTheRightOfThePlate


class L90K7OpenTheMicrowave(L90K7PutTheWhiteBowlToTheRightOfThePlate):
    task_name: str = "L90K7OpenTheMicrowave"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Open the microwave."
        return ep_meta

    def _check_success(self, env):
        return self.microwave.is_open(env, th=0.6) & OU.gripper_obj_far(env, self.microwave.name)
