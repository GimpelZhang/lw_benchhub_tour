# Copyright 2025 Lightwheel Team

from .L10K3_turn_on_the_stove_and_put_the_moka_pot_on_it import L10K3TurnOnTheStoveAndPutTheMokaPotOnIt
from .L10K4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it import L10K4PutTheBlackBowlInTheBottomDrawerOfTheCabinetAndCloseIt
from .L10K6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate import L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt
from .L10K8_put_both_moka_pots_on_the_stove import L10K8PutBothMokaPotsOnTheStove
from .L10L2_put_objects_in_basket import L10L1PutBothTheAlphabetSoupAndTheCreamCheeseBoxInTheBasket
from .L10L2_put_objects_in_basket import L10L2PutBothTheAlphabetSoupAndTheTomatoSauceInTheBasket
from .L10L2_put_objects_in_basket import L10L2PutBothTheCreamCheeseBoxAndTheButterInTheBasket
from .L10L5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate import L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate
from .L10L6_MugOnAndChocolateRightPlate import L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate
from .L10S1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy import L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy

__all__ = [
    "L10K3TurnOnTheStoveAndPutTheMokaPotOnIt",
    "L10K4PutTheBlackBowlInTheBottomDrawerOfTheCabinetAndCloseIt",
    "L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt",
    "L10K8PutBothMokaPotsOnTheStove",
    "L10L1PutBothTheAlphabetSoupAndTheCreamCheeseBoxInTheBasket",
    "L10L2PutBothTheAlphabetSoupAndTheTomatoSauceInTheBasket",
    "L10L2PutBothTheCreamCheeseBoxAndTheButterInTheBasket",
    "L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate",
    "L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate",
    "L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy",
]

import gymnasium as gym

gym.register(
    id="Robocasa-Task-L10K3TurnOnTheStoveAndPutTheMokaPotOnIt",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10K3TurnOnTheStoveAndPutTheMokaPotOnIt",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10K4PutTheBlackBowlInTheBottomDrawerOfTheCabinetAndCloseIt",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10K4PutTheBlackBowlInTheBottomDrawerOfTheCabinetAndCloseIt",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10K6PutTheYellowAndWhiteMugInTheMicrowaveAndCloseIt",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10K8PutBothMokaPotsOnTheStove",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10K8PutBothMokaPotsOnTheStove",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10L1PutBothTheAlphabetSoupAndTheCreamCheeseBoxInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10L1PutBothTheAlphabetSoupAndTheCreamCheeseBoxInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10L2PutBothTheAlphabetSoupAndTheTomatoSauceInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10L2PutBothTheAlphabetSoupAndTheTomatoSauceInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10L2PutBothTheCreamCheeseBoxAndTheButterInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10L2PutBothTheCreamCheeseBoxAndTheButterInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10L5PutWhiteMugOnLeftPlateAndPutYellowAndWhiteMugOnRightPlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10L6PutWhiteMugOnPlateAndPutChocolatePuddingToRightPlate",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy",
    },
    disable_env_checker=True,
)
