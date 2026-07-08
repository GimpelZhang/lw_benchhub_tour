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
import lw_benchhub.utils.object_utils as OU
from lw_benchhub.core.tasks.base import LwTaskBase
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub_tasks.lightwheel_libero_tasks.base.libero_put_on_stove_base import PutOnStoveBase


class L90K3PutTheFryingPanOnTheStove(PutOnStoveBase):
    task_name: str = "L90K3PutTheFryingPanOnTheStove"

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Put the frying pan on the stove."
        return ep_meta

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.mokapot = self.register_fixture_ref("mokapot_1", dict(id=FixtureType.MOKA_POT))
        self.stove = self.register_fixture_ref("stovetop", dict(id=FixtureType.STOVE))
        self.init_robot_base_ref = self.counter
        self.frying_pan = "chefmate_8_frypan"

    def _get_obj_cfgs(self):
        cfgs = []

        pan_pl = dict(
            fixture=self.counter,
            size=(0.8, 0.8),
            pos=(1.0, -0.75),
            rotation=-np.pi / 2,
            margin=0.02,
            ensure_valid_placement=False,
        )

        cfgs.append(
            dict(
                name=self.frying_pan,
                obj_groups="pot",
                graspable=True,
                placement=pan_pl,
                asset_name="Pot086.usd",
            )
        )

        return cfgs

    def _check_success(self, env):
        pan_on_stove = OU.check_obj_fixture_contact(env, self.frying_pan, self.stove)
        gripper_far = OU.gripper_obj_far(env, self.frying_pan, th=0.4)
        return pan_on_stove & gripper_far
