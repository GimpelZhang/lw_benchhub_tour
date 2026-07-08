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
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_goal_tasks_base import LiberoGoalTasksBase


class LGTurnOnTheStove(LiberoGoalTasksBase):
    """
    LGTurnOnTheStove: turn on the stove

    Steps:
        turn on the stove

    """
    task_name: str = "LGTurnOnTheStove"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Turn on the stove."
        return ep_meta

    def _get_obj_cfgs(self):
        cfgs = []

        # According to task.csv, need: akita_black_bowl, cream_cheese, plate, wine_bottle
        wine_bottle_placement = dict(
            fixture=self.table,
            pos=(0.0, -0.30),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.5),
        )
        cream_cheese_placement = dict(
            fixture=self.table,
            pos=(0.2, -0.70),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.7, 0.7),
        )
        plate_placement = dict(
            fixture=self.table,
            pos=(0.4, -1.30),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.7, 0.7),
        )
        bowl_placement = dict(
            fixture=self.table,
            pos=(0.6, 0.00),
            margin=0.02,
            ensure_valid_placement=True,
            size=(0.5, 0.7),
        )

        cfgs.append(
            dict(
                name=self.plate,
                obj_groups="plate",
                graspable=False,
                placement=plate_placement,
                asset_name="Plate012.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.akita_black_bowl,
                obj_groups="bowl",
                graspable=True,
                placement=bowl_placement,
                asset_name="Bowl008.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.wine_bottle,
                obj_groups="bottle",
                graspable=True,
                placement=wine_bottle_placement,
                object_scale=0.8,
                asset_name="Bottle054.usd",
            )
        )
        cfgs.append(
            dict(
                name=self.cream_cheese,
                obj_groups="cream_cheese",
                graspable=True,
                placement=cream_cheese_placement,
                asset_name="CreamCheeseStick013.usd",
            )
        )

        return cfgs

    def _check_success(self, env):
        # Check if the stove is turned on
        # Get the stove fixture and check if any knob is turned on
        knobs_state = self.stove.get_knobs_state(env)

        knob_success = torch.tensor([False], device=env.device).repeat(env.num_envs)
        for knob_name, knob_value in knobs_state.items():
            abs_knob = torch.abs(knob_value)
            lower, upper = 0.35, 2 * np.pi - 0.35
            knob_on = (abs_knob >= lower) & (abs_knob <= upper)
            knob_success = knob_success | knob_on
        # Check if gripper is far from the stove (not interacting with it)
        # Use the utility function to check gripper distance from stove
        gripper_far_from_stove = OU.gripper_obj_far(env, self.stove.name, th=0.3)

        return knob_success & gripper_far_from_stove
