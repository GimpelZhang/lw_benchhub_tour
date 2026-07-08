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
import copy
import lw_benchhub.utils.object_utils as OU
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_spatial.libero_put_black_bowl_on_plate import PutBlackBowlOnPlate
from lw_benchhub_tasks.lightwheel_libero_tasks.libero_spatial.LS_pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate import LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate


class LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate(LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate):
    task_name: str = 'LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate'
    EXCLUDE_LAYOUTS: list = [63, 64]

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick the akita black bowl on the wooden cabinet and place it on the plate."
        return ep_meta

    def _load_model(self):

        if self.fix_object_pose_cfg is None:
            self.fix_object_pose_cfg = {}

        PutBlackBowlOnPlate._load_model(self)

        cabinet_pos = self.storage_furniture.pos
        bowl_obj = self.object_placements[self.bowl_target]
        bowl_height = bowl_obj[2].size[2]

        bowl_target_pos = (
            cabinet_pos[0],
            cabinet_pos[1],
            cabinet_pos[2] + self.storage_furniture.size[2] / 2 + bowl_height / 2.0 + 0.01
        )

        self.fix_object_pose_cfg[self.bowl_target] = {"pos": bowl_target_pos}

        bowl_obj_list = list(bowl_obj)
        bowl_obj_list[0] = bowl_target_pos
        self.object_placements[self.bowl_target] = tuple(bowl_obj_list)

    def _get_obj_cfgs(self):
        cfgs = PutBlackBowlOnPlate._get_obj_cfgs(self)

        cfgs.append(
            dict(
                name=self.bowl,
                obj_groups="bowl",
                asset_name=self.bowl_asset_name,
                graspable=True,
                object_scale=0.6,
                placement=dict(
                    fixture=self.dining_table,
                    size=(0.25, 0.25),
                    pos=(-0.2, -0.6),
                    ensure_valid_placement=True,
                ),
            )
        )

        cfgs.append(
            dict(
                name=self.bowl_target,
                obj_groups="bowl",
                asset_name=self.bowl_asset_name,
                graspable=True,
                object_scale=0.6,
                placement=dict(
                    fixture=self.dining_table,
                    size=(0.4, 0.4),
                    pos=(-0.4, -0.4),
                    ensure_valid_placement=True,
                ),
            )
        )

        return cfgs
