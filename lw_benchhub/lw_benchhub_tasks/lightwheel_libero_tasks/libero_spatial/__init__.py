# Copyright 2025 Lightwheel Team

from .LS_pick_up_black_bowl_between_plate_and_ramekin_and_place_it_on_plate import LSPickUpBlackBowlBetweenPlateAndRamekinAndPlaceItOnPlate
from .LS_pick_up_black_bowl_in_top_drawer_of_wooden_cabinet_and_place_it_on_plate import LSPickUpBlackBowlInTopDrawerOfWoodenCabinetAndPlaceItOnPlate
from .LS_pick_up_the_black_bowl_from_table_center_and_place_it_on_the_plate import LSPickUpTheBlackBowlFromTableCenterAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_next_to_the_cookie_box_and_place_it_on_the_plate import LSPickUpTheBlackBowlNextToTheCookieBoxAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_next_to_the_plate_and_place_it_on_the_plate import LSPickUpTheBlackBowlNextToThePlateAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_next_to_the_ramekin_and_place_it_on_the_plate import LSPickUpTheBlackBowlNextToTheRamekinAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate import LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate import LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_on_the_stove_and_place_it_on_the_plate import LSPickUpTheBlackBowlOnTheStoveAndPlaceItOnThePlate
from .LS_pick_up_the_black_bowl_on_the_wooden_cabinet_and_place_it_on_the_plate import LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate

__all__ = [
    "LSPickUpBlackBowlBetweenPlateAndRamekinAndPlaceItOnPlate",
    "LSPickUpBlackBowlInTopDrawerOfWoodenCabinetAndPlaceItOnPlate",
    "LSPickUpTheBlackBowlFromTableCenterAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlNextToTheCookieBoxAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlNextToThePlateAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlNextToTheRamekinAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlOnTheStoveAndPlaceItOnThePlate",
    "LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate",
]

import gymnasium as gym


gym.register(
    id="Robocasa-Task-LSPickUpBlackBowlBetweenPlateAndRamekinAndPlaceItOnPlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpBlackBowlBetweenPlateAndRamekinAndPlaceItOnPlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpBlackBowlInTopDrawerOfWoodenCabinetAndPlaceItOnPlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpBlackBowlInTopDrawerOfWoodenCabinetAndPlaceItOnPlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlFromTableCenterAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlFromTableCenterAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlNextToTheCookieBoxAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlNextToTheCookieBoxAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlNextToThePlateAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlNextToThePlateAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlNextToTheRamekinAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlNextToTheRamekinAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlOnTheCookieBoxAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlOnTheRamekinAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlOnTheStoveAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlOnTheStoveAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LSPickUpTheBlackBowlOnTheWoodenCabinetAndPlaceItOnThePlate",
    },
    disable_env_checker=True,
)
