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
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_90.L90K3_turn_on_the_stove import L90K3TurnOnTheStove


class L90K3TurnOnTheStoveAndPutTheFryingPanOnIt(L90K3TurnOnTheStove):
    task_name: str = "L90K3TurnOnTheStoveAndPutTheFryingPanOnIt"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Turn on the stove and put the frying pan on it."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []
        placement = dict(
            fixture=self.counter,
            size=(0.6, 0.5),
            pos=(-0.5, 0.0),
            ensure_object_boundary_in_range=False,
        )
        cfgs.append(
            dict(
                name="chefmate_8_frypan",
                obj_groups="pot",
                graspable=True,
                asset_name="Pot086.usd",
                placement=placement,
            )
        )
        return cfgs

    def _check_success(self, env):
        knobs_state = self.stove.get_knobs_state(env=env)
        knob_success = torch.tensor([False], device=env.device).repeat(env.num_envs)
        for knob_name, knob_value in knobs_state.items():
            abs_knob = torch.abs(knob_value)
            lower, upper = 0.35, 2 * np.pi - 0.35
            knob_on = (abs_knob >= lower) & (abs_knob <= upper)
            knob_success = knob_success | knob_on
        pot_success = torch.tensor([False] * env.num_envs, device=env.device)
        for i in range(env.num_envs):
            pot_success[i] = torch.as_tensor(
                OU.point_in_fixture(OU.get_object_pos(env, "chefmate_8_frypan")[i], self.stove, only_2d=True),
                dtype=torch.bool,
                device=env.device,
            )
        return knob_success & pot_success & OU.gripper_obj_far(env, "chefmate_8_frypan", 0.35)
