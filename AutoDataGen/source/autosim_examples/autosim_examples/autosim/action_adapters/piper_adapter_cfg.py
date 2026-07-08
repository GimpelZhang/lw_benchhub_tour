from isaaclab.utils import configclass

from autosim import ActionAdapterCfg

from .piper_adapter import PiperAbsAdapter


@configclass
class PiperAbsAdapterCfg(ActionAdapterCfg):
    """Configuration for the DoublePiper absolute joint-position action adapter."""

    class_type: type = PiperAbsAdapter

    skip_apply_skills: list[str] = ["moveto"]
