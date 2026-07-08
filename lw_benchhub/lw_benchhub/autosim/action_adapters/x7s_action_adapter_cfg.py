from isaaclab.utils import configclass
from autosim import ActionAdapterCfg

from .x7s_action_adapter import X7SActionAdapter


@configclass
class X7SActionAdapterCfg(ActionAdapterCfg):
    """Configuration for the X7S action adapter."""

    class_type: type = X7SActionAdapter
    """The class type of the action adapter."""

    base_x_joint_name: str = "base_x_joint"
    """The name of the base x joint."""
    base_y_joint_name: str = "base_y_joint"
    """The name of the base y joint."""
    base_yaw_joint_name: str = "base_yaw_link"
    """The name of the base yaw joint."""
    robot_base_link_name: str = "base_link"
    """The name of the robot base link."""
    use_left_gripper_action: bool = True
    """Whether to use the left gripper action."""
