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


class RelativePlacementBase(LwTaskBase):
    task_name: str = "RelativePlacementBase"

    obj_name: str = "obj"
    ref_name: str = "ref"
    obj_groups: list | tuple | None = None
    ref_groups: list | tuple | None = None
    obj_asset_name: str | None = None
    ref_asset_name: str | None = None
    relation: str = "left"  # left / right / front / behind
    dist_range: tuple[float, float] = (0.10, 0.35)
    lateral_tol: float = 0.20
    stable_vel_th: float = 0.5

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.counter = self.register_fixture_ref("table", dict(id=FixtureType.TABLE))
        self.init_robot_base_ref = self.counter
        # additional object names for consistency with other tasks
        self.porcelain_mug = "porcelain_mug"
        self.red_coffee_mug = "red_coffee_mug"

    def _get_obj_cfgs(self):
        cfgs = []
        return cfgs

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = f"Place the {self.obj_name.replace('_', ' ')} {self.relation} of the {self.ref_name.replace('_', ' ')}."
        return ep_meta

    def _check_success(self, env):
        # use check_place_obj1_side_by_obj2 for side-by-side placement check (no angle requirement)
        return OU.check_place_obj1_side_by_obj2(env, self.obj_name, self.ref_name, {
            "gripper_far": True,   # obj1 and obj2 should be far from the gripper
            "contact": False,   # obj1 should not be in contact with obj2
            "side": self.relation,    # relative position of obj1 to obj2
            "side_threshold": 0.25,    # threshold for distance between obj1 and obj2 in other directions
            "margin_threshold": [0.001, 0.1],    # threshold for distance between obj1 and obj2
            "stable_threshold": 0.5,    # threshold for stable, velocity vector length less than 0.5
        })
