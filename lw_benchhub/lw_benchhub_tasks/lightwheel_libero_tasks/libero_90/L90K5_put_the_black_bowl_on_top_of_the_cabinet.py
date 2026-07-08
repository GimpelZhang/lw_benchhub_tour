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
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K5_put_the_black_bowl_on_the_plate import L90K5PutTheBlackBowlOnThePlate


class L90K5PutTheBlackBowlOnTopOfTheCabinet(L90K5PutTheBlackBowlOnThePlate):
    task_name: str = "L90K5PutTheBlackBowlOnTopOfTheCabinet"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the black bowl on top of the cabinet."
        return ep_meta

    def _check_success(self, env):
        bowl_poses = OU.get_object_pos(env, self.akita_black_bowl)
        bowl_success_tensor = torch.tensor([False] * env.num_envs, device=env.device)
        for i, bowl_pos in enumerate(bowl_poses):
            bowl_success = OU.point_in_fixture(bowl_pos, self.drawer, only_2d=True)
            bowl_success_tensor[i] = torch.as_tensor(bowl_success, dtype=torch.bool, device=env.device)

        result = bowl_success_tensor & OU.gripper_obj_far(env, self.akita_black_bowl)
        return result
