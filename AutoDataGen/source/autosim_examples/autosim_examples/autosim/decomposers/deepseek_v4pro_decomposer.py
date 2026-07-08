from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from isaaclab.utils import configclass

from autosim import SkillRegistry
from autosim.core.decomposer import Decomposer
from autosim.core.types import EnvExtraInfo
from autosim.decomposers.llm_decomposer.llm_decomposer import LLMDecomposer
from autosim.decomposers.llm_decomposer.llm_decomposer_cfg import LLMDecomposerCfg


class DeepSeekV4ProBackend:
    """DeepSeek-v4-pro backend using the Anthropic Messages protocol.

    Uses only the Python standard library (urllib) and enforces strict equality
    on the response ``model`` field to prevent silent degradation to other models.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/anthropic", model: str = "deepseek-v4-pro"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        headers = {
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} {e.reason}\n{e.read().decode('utf-8', errors='replace')}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}") from None

        if data.get("type") == "error":
            raise RuntimeError(data.get("error"))

        actual = data.get("model", "")
        print(f"[请求模型: deepseek-v4-pro | 实际响应模型: {actual}]", file=sys.stderr)
        # Strict equality anti-degrade guard (stronger than substring match).
        if actual != "deepseek-v4-pro":
            print(f"⚠️ 警告: 实际响应模型 {actual} 不一致！", file=sys.stderr)
            raise RuntimeError("model degrade")

        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


class DeepSeekV4ProLLMDecomposer(LLMDecomposer):
    """LLM decomposer backed by DeepSeek-v4-pro.

    Skips the OpenAI-based :class:`LLMDecomposer` initializer and wires in
    :class:`DeepSeekV4ProBackend` directly. The prompt template is reused from
    the core LLM decomposer via the ``prompts`` symlink.
    """

    def __init__(self, cfg: DeepSeekV4ProLLMDecomposerCfg) -> None:
        # Bypass LLMDecomposer.__init__ (it instantiates an OpenAI client).
        Decomposer.__init__(self, cfg)

        self._llm_backend = DeepSeekV4ProBackend(cfg.api_key, cfg.base_url, cfg.model)
        self._atomic_skills = [skill_cfg.name for skill_cfg in SkillRegistry.list_skills()]

        from jinja2 import Environment, FileSystemLoader

        self._prompt_template = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent / "prompts")),
            autoescape=False,
        ).get_template("task_decompose.jinja")

    def _load_task_code(self, task_name: str) -> str:
        """Return a placeholder instead of loading lw_benchhub envhub task code.

        lw_benchhub envhub tasks are registered with empty ``kwargs``, so the
        base registry lookup always fails. The actual task description is carried
        by ``EnvExtraInfo.additional_prompt_contents``.
        """
        return (
            f"# Source for {task_name} not loaded (lw_benchhub envhub tasks have empty kwargs). "
            "See additional_prompt_contents."
        )


@configclass
class DeepSeekV4ProLLMDecomposerCfg(LLMDecomposerCfg):
    """Configuration for the DeepSeek-v4-pro LLM decomposer."""

    class_type: type = DeepSeekV4ProLLMDecomposer
    """The class type of the decomposer."""

    base_url: str = "https://api.deepseek.com/anthropic"
    """Anthropic-compatible endpoint for DeepSeek."""

    model: str = "deepseek-v4-pro"
    """Model name; only deepseek-v4-pro is allowed."""

    temperature: float = 0.3
    """Sampling temperature."""

    max_tokens: int = 32768
    """Maximum tokens to generate (DeepSeek-v4-pro supports up to 384K)."""

    max_decompose_retries: int = 3
    """Maximum retries for JSON parse/validation failures."""

    def __post_init__(self) -> None:
        # Do NOT call LLMDecomposerCfg.__post_init__; it requires AUTOSIM_LLM_API_KEY.
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if api_key is None:
            raise ValueError("DEEPSEEK_API_KEY not set; source deepseek_v4pro_env.sh")
        self.api_key = api_key
        if "deepseek-v4-pro" not in self.model:
            raise ValueError(f"only deepseek-v4-pro allowed, got {self.model}")
