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


class LiberoGoalTasksBase(LwTaskBase):
    """
    LiberoGoalTasksBase: base class for all libero goal tasks
    """

    task_name: str = "LiberoGoalTasksBase"
    enable_fixtures = ["storage_furniture", "stovetop", "winerack"]
    # movable_fixtures = ["winerack"]

    def _setup_kitchen_references(self, scene):
        super()._setup_kitchen_references(scene)
        self.table = self.register_fixture_ref(
            "table", dict(id=FixtureType.TABLE)
        )

        self.init_robot_base_ref = self.table
        self.drawer = self.register_fixture_ref("storage_furniture", dict(id=FixtureType.STORAGE_FURNITURE))
        self.stove = self.register_fixture_ref("stovetop", dict(id=FixtureType.STOVE))
        self.winerack = self.register_fixture_ref("winerack", dict(id=FixtureType.WINE_RACK))

        # Define object names for drawer tasks
        self.akita_black_bowl = "akita_black_bowl"
        self.cream_cheese = "cream_cheese"
        self.plate = "plate"
        self.wine_bottle = "wine_bottle"

    def _setup_scene(self, env, env_ids=None):
        """
        Resets simulation internal configurations.
        """
        super()._setup_scene(env, env_ids)
        # Get the top drawer joint name (first joint)
        if hasattr(self.drawer, '_joint_infos') and self.drawer._joint_infos:
            self.top_drawer_joint_name = list(self.drawer._joint_infos.keys())[0]
        else:
            # Use default joint name if joint info is not available
            self.top_drawer_joint_name = "drawer_joint_1"

    def _get_obj_cfgs(self):
        cfgs = []
        return cfgs

    def _check_success(self, env):
        return torch.tensor([False], device=env.device)
