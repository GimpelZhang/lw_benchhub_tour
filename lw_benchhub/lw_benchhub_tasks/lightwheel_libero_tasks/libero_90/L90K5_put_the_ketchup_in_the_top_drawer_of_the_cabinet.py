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
import torch
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K5_put_the_black_bowl_on_the_plate import L90K5PutTheBlackBowlOnThePlate


class L90K5PutTheKetchupInTheTopDrawerOfTheCabinet(L90K5PutTheBlackBowlOnThePlate):
    task_name: str = "L90K5PutTheKetchupInTheTopDrawerOfTheCabinet"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the ketchup in the top drawer of the cabinet."
        return ep_meta

    def _check_success(self, env):
        ketchup_success = OU.obj_inside_of(env, self.ketchup, self.drawer)
        return ketchup_success & OU.gripper_obj_far(env, self.ketchup)
