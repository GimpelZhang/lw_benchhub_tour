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
from lw_benchhub.core.models.fixtures import FixtureType
from lw_benchhub.core.tasks.base import LwTaskBase


class BookInCaddyBase(LwTaskBase):
    task_name: str = "BookInCaddyBase"

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.init_robot_base_ref = self.counter
        self.black_book = "black_book"
        self.desk_caddy = "desk_caddy"
        self.red_coffee_mug = "red_coffee_mug"

    def _get_obj_cfgs(self):
        cfgs = []

        caddy_pl = dict(
            fixture=self.counter,
            size=(0.6, 0.4),
            pos=(0, -0.4),
            rotation=np.pi / 8,
            margin=0.02,
            ensure_valid_placement=True,
        )
        book_pl = dict(
            fixture=self.counter,
            size=(0.35, 0.35),
            pos=(0.2, -0.5),
            rotation=0,
            margin=0.02,
            ensure_valid_placement=True,
        )
        mug_pl = dict(
            fixture=self.counter,
            size=(0.35, 0.3),
            pos=(-0.3, -0.6),
            rotation=0,
            margin=0.02,
            ensure_valid_placement=True,
        )

        cfgs.append(
            dict(
                name=self.desk_caddy,
                obj_groups="desk_caddy",
                graspable=True,
                placement=caddy_pl,
                asset_name="DeskCaddy001.usd",
                object_scale=2.0,
            )
        )
        cfgs.append(
            dict(
                name=self.black_book,
                obj_groups="book",
                graspable=True,
                placement=book_pl,
                asset_name="Book042.usd",
                object_scale=0.4,
            )
        )
        cfgs.append(
            dict(
                name=self.red_coffee_mug,
                obj_groups="cup",
                graspable=True,
                placement=mug_pl,
                asset_name="Cup030.usd",
            )
        )

        return cfgs

    def _success_common(self, env):
        in_caddy = OU.check_obj_in_receptacle(env, self.black_book, self.desk_caddy)
        gripper_far_success = OU.gripper_obj_far(env, self.black_book, 0.35)
        return in_caddy & gripper_far_success


class StudySceneBase(LwTaskBase):
    """Base class for Study Scene 4 tasks with books and shelves"""
    task_name: str = "StudySceneBase"

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.init_robot_base_ref = self.counter
        self.black_book = "black_book"
        self.yellow_book = "yellow_book"
        self.middle_book = "midlle_book"
        self.shelf = "shelf"

    def _get_obj_cfgs(self):
        cfgs = []

        left_book_pl = dict(
            fixture=self.counter,
            size=(0.35, 0.35),
            pos=(-0.35, 0.8),
            margin=0.02,
            ensure_valid_placement=True,
        )
        right_book_pl = dict(
            fixture=self.counter,
            size=(0.35, 0.35),
            pos=(0.35, -0.6),
            margin=0.02,
            ensure_valid_placement=True,
        )
        middle_book_pl = dict(
            fixture=self.counter,
            size=(0.35, 0.35),
            pos=(0, -0.6),
            margin=0.02,
            ensure_valid_placement=True,
        )
        shelf_pl = dict(
            fixture=self.counter,
            size=(0.5, 0.75),
            pos=(0.7, -0.5),
            rotation=-np.pi / 2,
            margin=0.02,
            ensure_valid_placement=True,
        )

        cfgs.append(
            dict(
                name=self.shelf,
                obj_groups="shelf",
                graspable=True,
                placement=shelf_pl,
                asset_name="Shelf073.usd",
                object_scale=1.0,
            )
        )
        cfgs.append(
            dict(
                name=self.black_book,
                obj_groups="book",
                graspable=True,
                placement=left_book_pl,
                asset_name="Book042.usd",
                object_scale=0.4,
            )
        )
        cfgs.append(
            dict(
                name=self.yellow_book,
                obj_groups="book",
                graspable=True,
                placement=right_book_pl,
                asset_name="Book043.usd",
                object_scale=0.4,
            )
        )
        cfgs.append(
            dict(
                name=self.middle_book,
                obj_groups="book",
                graspable=True,
                placement=middle_book_pl,
                asset_name="Book043.usd",
                object_scale=0.4,
            )
        )

        return cfgs
