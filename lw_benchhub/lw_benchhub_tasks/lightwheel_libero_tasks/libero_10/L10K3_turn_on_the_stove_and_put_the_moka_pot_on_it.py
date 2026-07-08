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
import numpy as np

import lw_benchhub.utils.object_utils as OU
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K3_turn_on_the_stove import L90K3TurnOnTheStove


class L10K3TurnOnTheStoveAndPutTheMokaPotOnIt(L90K3TurnOnTheStove):
    task_name: str = "L10K3TurnOnTheStoveAndPutTheMokaPotOnIt"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Turn on the stove and put the moka pot on it."
        return ep_meta

    def _check_success(self, env):
        knobs_state = self.stove.get_knobs_state(env=env)
        knob_success = torch.tensor([False], device=env.device).repeat(env.num_envs)
        for knob_name, knob_value in knobs_state.items():
            abs_knob = torch.abs(knob_value)
            lower, upper = 0.35, 2 * np.pi - 0.35
            knob_on = (abs_knob >= lower) & (abs_knob <= upper)
            knob_success = knob_success | knob_on
        mokapot_pos = env.scene.articulations[self.mokapot.name].data.root_pos_w[0, :].cpu().numpy()
        moka_success = OU.point_in_fixture(mokapot_pos, self.stove, only_2d=True)
        moka_success = torch.tensor([moka_success], device=env.device).repeat(env.num_envs)
        return knob_success & moka_success & OU.gripper_obj_far(env, "mokapot_1_front_group_1", 0.35)
