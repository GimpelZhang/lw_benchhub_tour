# Copyright 2025 Lightwheel Team

from .LO_pick_up_the_alphabet_soup_and_place_it_in_the_basket import LOPickUpTheAlphabetSoupAndPlaceItInTheBasket
from .LO_pick_up_the_bbq_sauce_and_place_it_in_the_basket import LOPickUpTheBbqSauceAndPlaceItInTheBasket
from .LO_pick_up_the_butter_and_place_it_in_the_basket import LOPickUpTheButterAndPlaceItInTheBasket
from .LO_pick_up_the_chocolate_pudding_and_place_it_in_the_basket import LOPickUpTheChocolatePuddingAndPlaceItInTheBasket
from .LO_pick_up_the_ketchup_and_place_it_in_the_basket import LOPickUpTheKetchupAndPlaceItInTheBasket
from .LO_pick_up_the_milk_and_place_it_in_the_basket import LOPickUpTheMilkAndPlaceItInTheBasket
from .LO_pick_up_the_orange_juice_and_place_it_in_the_basket import LOPickUpTheOrangeJuiceAndPlaceItInTheBasket
from .LO_pick_up_the_salad_dressing_and_place_it_in_the_basket import LOPickUpTheSaladDressingAndPlaceItInTheBasket
from .LO_pick_up_the_tomato_sauce_and_place_it_in_the_basket import LOPickUpTheTomatoSauceAndPlaceItInTheBasket
from .LO_put_cream_cheese_in_basket import LOPutCreamCheeseInBasket

__all__ = [
    "LOPickUpTheAlphabetSoupAndPlaceItInTheBasket",
    "LOPickUpTheBbqSauceAndPlaceItInTheBasket",
    "LOPickUpTheButterAndPlaceItInTheBasket",
    "LOPickUpTheChocolatePuddingAndPlaceItInTheBasket",
    "LOPickUpTheKetchupAndPlaceItInTheBasket",
    "LOPickUpTheMilkAndPlaceItInTheBasket",
    "LOPickUpTheOrangeJuiceAndPlaceItInTheBasket",
    "LOPickUpTheSaladDressingAndPlaceItInTheBasket",
    "LOPickUpTheTomatoSauceAndPlaceItInTheBasket",
    "LOPutCreamCheeseInBasket",
]

import gymnasium as gym


gym.register(
    id="Robocasa-Task-LOPickUpTheAlphabetSoupAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheAlphabetSoupAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheBbqSauceAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheBbqSauceAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheButterAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheButterAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheChocolatePuddingAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheChocolatePuddingAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheKetchupAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheKetchupAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheMilkAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheMilkAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheOrangeJuiceAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheOrangeJuiceAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheSaladDressingAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheSaladDressingAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPickUpTheTomatoSauceAndPlaceItInTheBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPickUpTheTomatoSauceAndPlaceItInTheBasket",
    },
    disable_env_checker=True,
)

gym.register(
    id="Robocasa-Task-LOPutCreamCheeseInBasket",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}:LOPutCreamCheeseInBasket",
    },
    disable_env_checker=True,
)
