from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_AUTOSIM_ROOT = Path(__file__).parent
_PROMPT_ENV = Environment(
    loader=FileSystemLoader(str(_AUTOSIM_ROOT)),
    autoescape=False,
)
_PROMPT_TEMPLATE = _PROMPT_ENV.get_template("additional_prompt.jinja")


def render_additional_prompt() -> str:
    """Render the shared autosim prompt template used by task pipelines."""

    return _PROMPT_TEMPLATE.render()
