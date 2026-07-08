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
import torch
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K6_put_the_yellow_and_white_mug_to_the_front_of_the_white_mug import L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug


class L90K6CloseTheMicrowave(L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug):
    task_name: str = "L90K6CloseTheMicrowave"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Close the microwave."
        return ep_meta

    def _check_success(self, env):
        return self.microwave.is_closed(env) & OU.gripper_obj_far(env, self.microwave.name, th=0.4)
