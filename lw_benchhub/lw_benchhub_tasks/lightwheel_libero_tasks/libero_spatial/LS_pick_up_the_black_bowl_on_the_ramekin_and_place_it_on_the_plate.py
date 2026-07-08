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


class LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate(LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate):
    task_name: str = 'LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate'
    EXCLUDE_LAYOUTS: list = [63, 64]

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta[
            "lang"
        ] = f"Pick the akita black bowl on the ramekin and place it on the plate."
        return ep_meta

    def _load_model(self):
        super()._load_model()
        if self.fix_object_pose_cfg is None:
            self.fix_object_pose_cfg = {}
        ramekin_pos = list(self.object_placements[self.ramekin][0])
        bowl_obj = copy.deepcopy(self.object_placements[self.bowl_target])
        bowl_pos = list(bowl_obj[0])
        bowl_pos[0] = ramekin_pos[0]
        bowl_pos[1] = ramekin_pos[1]
        bowl_pos[2] = bowl_pos[2] + self.object_placements[self.ramekin][2].size[2] - 0.05
        bowl_obj = list(bowl_obj)
        bowl_obj[0] = bowl_pos
        self.fix_object_pose_cfg[self.bowl_target] = {"pos": bowl_pos}
        self.object_placements[self.bowl_target] = tuple(bowl_obj)
