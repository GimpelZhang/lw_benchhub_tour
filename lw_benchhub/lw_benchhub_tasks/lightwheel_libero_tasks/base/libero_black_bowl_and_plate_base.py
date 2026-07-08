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


class LiberoBlackBowlAndPlateBase(LwTaskBase):
    """
    LiberoBlackBowlAndPlateBase: base class for all libero black bowl and plate tasks
    """

    task_name: str = "LiberoBlackBowlAndPlateBase"
    enable_fixtures = ['storage_furniture']
    fix_object_pose_cfg: dict = None

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.drawer = self.register_fixture_ref("storage_furniture", dict(id=FixtureType.STORAGE_FURNITURE))
        self.init_robot_base_ref = self.counter
        self.akita_black_bowl_front = "akita_black_bowl_front"
        self.akita_black_bowl_middle = "akita_black_bowl_middle"
        self.akita_black_bowl_back = "akita_black_bowl_back"
        self.plate = "plate"

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        self.top_joint_name = list(self.drawer._joint_infos.keys())[0]

    def _get_obj_cfgs(self):
        cfgs = []

        base_x = self.rng.uniform(-0.3, -0.15)
        middle_y = self.rng.uniform(-0.6, -0.4)
        spacing = self.rng.uniform(0.6, 1.0)

        front_pos = (base_x, middle_y + spacing)
        middle_pos = (base_x, middle_y)
        back_pos = (base_x, middle_y - spacing)

        plate_placement = dict(
            fixture=self.counter,
            size=(0.28, 0.28),
            pos=(0.15, -0.2),
            margin=0.02,
            ensure_valid_placement=True,
        )
        black_bowl_front_placement = dict(
            fixture=self.counter,
            size=(0.22, 0.22),
            pos=front_pos,
            margin=0.02,
            ensure_valid_placement=True,
        )
        black_bowl_middle_placement = dict(
            fixture=self.counter,
            size=(0.22, 0.22),
            pos=middle_pos,
            margin=0.02,
            ensure_valid_placement=True,
        )
        black_bowl_back_placement = dict(
            fixture=self.counter,
            size=(0.22, 0.22),
            pos=back_pos,
            margin=0.02,
            ensure_valid_placement=True,
        )

        cfgs.append(
            dict(
                name=self.akita_black_bowl_back,
                obj_groups='akita_black_bowl',
                graspable=True,
                placement=black_bowl_back_placement,
                asset_name='Bowl008.usd',
                object_scale=0.8,
            )
        )
        cfgs.append(
            dict(
                name=self.plate,
                obj_groups=self.plate,
                graspable=True,
                placement=plate_placement,
                asset_name='Plate012.usd',
            )
        )
        cfgs.append(
            dict(
                name=self.akita_black_bowl_middle,
                obj_groups='akita_black_bowl',
                graspable=True,
                placement=black_bowl_middle_placement,
                asset_name='Bowl008.usd',
                object_scale=0.8,
            )
        )
        cfgs.append(
            dict(
                name=self.akita_black_bowl_front,
                obj_groups='akita_black_bowl',
                graspable=True,
                placement=black_bowl_front_placement,
                asset_name='Bowl008.usd',
                object_scale=0.8,
            )
        )
        return cfgs
