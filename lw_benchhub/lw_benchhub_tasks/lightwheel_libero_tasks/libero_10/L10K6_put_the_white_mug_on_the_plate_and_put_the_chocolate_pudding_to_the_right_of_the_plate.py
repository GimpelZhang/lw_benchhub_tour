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

import torch

import lw_benchhub.utils.object_utils as OU
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K6_put_the_yellow_and_white_mug_to_the_front_of_the_white_mug import L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug


class L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt(L90K6PutTheYellowAndWhiteMugToTheFrontOfTheWhiteMug):
    task_name: str = "L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the yellow and white mug in the microwave and close it."
        return ep_meta

    def _check_success(self, env):
        mug_poses = OU.get_object_pos(env, self.white_yellow_mug)
        mug_success_tensor = torch.tensor([False] * env.num_envs, device=env.device)
        for i, mug_pos in enumerate(mug_poses):
            mug_success = OU.point_in_fixture(mug_pos, self.microwave)
            mug_success_tensor[i] = torch.as_tensor(mug_success, dtype=torch.bool, device=env.device)
        return mug_success_tensor & self.microwave.is_closed(env) & OU.gripper_obj_far(env, self.microwave.name, th=0.4)
