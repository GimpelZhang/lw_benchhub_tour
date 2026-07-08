# Copyright 2025 Lightwheel Team

from .LG_open_the_middle_drawer_of_the_cabinet import LGOpenTheMiddleDrawerOfTheCabinet
from .LG_open_the_top_drawer_and_put_the_bowl_inside import LGOpenTheTopDrawerAndPutTheBowlInside
from .LG_open_top_drawer_of_cabinet import LGOpenTopDrawerOfCabinet
from .LG_push_the_plate_to_the_front_of_the_stove import LGPushThePlateToTheFrontOfTheStove
from .LG_put_the_bowl_on_the_plate import LGPutTheBowlOnThePlate
from .LG_put_the_bowl_on_the_stove import LGPutTheBowlOnTheStove
from .LG_put_the_bowl_on_top_of_the_cabinet import LGPutTheBowlOnTopOfTheCabinet
from .LG_put_the_cream_cheese_in_the_bowl import LGPutTheCreamCheeseInTheBowl
from .LG_put_the_wine_bottle_on_the_rack import LGPutTheWineBottleOnTheRack
from .LG_put_the_wine_bottle_on_top_of_the_cabinet import LGPutTheWineBottleOnTopOfTheCabinet
from .LG_turn_on_the_stove import LGTurnOnTheStove

__all__ = [
    "LGOpenTheMiddleDrawerOfTheCabinet",
    "LGOpenTheTopDrawerAndPutTheBowlInside",
    "LGOpenTopDrawerOfCabinet",
    "LGPushThePlateToTheFrontOfTheStove",
    "LGPutTheBowlOnThePlate",
    "LGPutTheBowlOnTheStove",
    "LGPutTheBowlOnTopOfTheCabinet",
    "LGPutTheCreamCheeseInTheBowl",
    "LGPutTheWineBottleOnTheRack",
    "LGPutTheWineBottleOnTopOfTheCabinet",
    "LGTurnOnTheStove",
]

import gymnasium as gym


gym.register(
    id="Robocasa-Task-LGOpenTheMiddleDrawerOfTheCabinet",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGOpenTheMiddleDrawerOfTheCabinet",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGOpenTheTopDrawerAndPutTheBowlInside",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGOpenTheTopDrawerAndPutTheBowlInside",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGOpenTopDrawerOfCabinet",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGOpenTopDrawerOfCabinet",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPushThePlateToTheFrontOfTheStove",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPushThePlateToTheFrontOfTheStove",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheBowlOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheBowlOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheBowlOnTheStove",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheBowlOnTheStove",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheBowlOnTopOfTheCabinet",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheBowlOnTopOfTheCabinet",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheCreamCheeseInTheBowl",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheCreamCheeseInTheBowl",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheWineBottleOnTheRack",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheWineBottleOnTheRack",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGPutTheWineBottleOnTopOfTheCabinet",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGPutTheWineBottleOnTopOfTheCabinet",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LGTurnOnTheStove",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LGTurnOnTheStove",
    },
    disable_env_checker=True,
)
