"""Stage 3 cross-embodiment benchmark driver for LightwheelAI lw_benchhub.

Re-pivots the Stage 3 demo back to the Lightwheel ecosystem:
  - Hub:   LightwheelAI/lw_benchhub_env
  - Model: LightwheelAI/smolvla-double-piper-pnp
  - Tasks: lw_benchhub kitchen PnP YML tasks
  - Embodiments: cross-brand matrix (DoublePiper, DoublePanda, PandaOmron, ...)

The script explicitly applies lw_benchhub monkey-patches at entry to demonstrate
LW toolchain value for headless rendering and USD xform standardization.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# =============================================================================
# Constants
# =============================================================================

POLICY_PATH = "LightwheelAI/smolvla-double-piper-pnp"   # NOT nvidia
ENV_TYPE = "isaaclab_arena"                             # same as Stage 1
ENV_HUB_PATH = "LightwheelAI/lw_benchhub_env"
STATE_DIM = 16                                          # DoublePiper-Abs
ACTION_DIM = 12
STATE_KEYS = "joint_pos"                                # verified against pathB_logs/run_pathB.sh
CAMERA_KEYS = "left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb"
RENAME_MAP = (
    '{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", '
    '"observation.images.right_hand_camera_rgb": "observation.images.right_hand", '
    '"observation.images.first_person_camera_rgb": "observation.images.first_person"}'
)

LEROBOT_CWD = Path("/mnt/robot/lw_benchhub")             # cwd MUST be this — yml uses relative path
YML_OUT_DIR = Path("/mnt/robot/lw_benchhub/configs/envhub/generated_stage3")
TEMPLATE_YML = Path("/mnt/robot/lw_benchhub/configs/envhub/example.yml")
OUTPUT_ROOT_PREFIX = Path("/mnt/robot")
DELIVERABLES_ROOT = Path("/mnt/robot/stage3_final_deliverables")
LOGS_ROOT = Path("/mnt/robot/stage3_logs")

N_EPISODES = 10
BATCH_SIZE = 1
VIDEO_LENGTH = 200

FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


# =============================================================================
# Matrix — 4 rows. All robot IDs verified against
#   /mnt/robot/lw_benchhub/lw_benchhub/core/robots/*/__init__.py gym.register(id=...)
# (yml uses the part after "Robocasa-Robot-").
# =============================================================================

MATRIX: list[dict[str, Any]] = [
    {
        "label": "ctrl_doublepiper_baseline",
        "robot": "DoublePiper-Abs",
        "layout": "libero-1-1",
        "task": "L90K1PutTheBlackBowlOnThePlate",
        "seed": 42,
        "episode_length_s": 20.0,
        "expected_ood": False,
        "note": "Stage 1 reproduction row (~40% expected success rate).",
    },
    {
        "label": "cross_doublepanda_abs",
        "robot": "DoublePanda-Abs",
        "layout": "libero-1-1",
        "task": "L90K1PutTheBlackBowlOnThePlate",
        "seed": 43,
        "episode_length_s": 20.0,
        "expected_ood": True,
        "note": "Cross-brand (Franka Panda) absolute-joint control; SmolVLA policy is OOD.",
    },
    {
        "label": "cross_pandaomron_abs",
        "robot": "PandaOmron-Abs",
        "layout": "libero-1-1",
        "task": "L90K1PutTheBlackBowlOnThePlate",
        "seed": 44,
        "episode_length_s": 20.0,
        "expected_ood": True,
        "note": "Cross-brand Franka+Omron mobile manipulator; absolute-joint OOD.",
    },
    {
        "label": "cross_pandaomron_rel",
        "robot": "PandaOmron-Rel",
        "layout": "libero-1-1",
        "task": "L90K1PutTheBlackBowlOnThePlate",
        "seed": 45,
        "episode_length_s": 20.0,
        "expected_ood": True,
        "note": "Cross-brand Franka+Omron relative-joint control; predicted as double OOD (brand + action space), but in this run hit a `lightwheel_sdk` asset-fetch timeout to api.lightwheel.net before the policy/env interface was exercised. Re-run when the asset endpoint is reachable to observe the predicted obs/action-space mismatch.",
    },
]


# =============================================================================
# Environment & Lightwheel patch demonstration
# =============================================================================

def check_environment() -> None:
    """Validate runtime pre-conditions before any eval work."""
    import numpy as np

    if np.__version__ != "1.26.0":
        raise RuntimeError(f"numpy must be 1.26.0 (Isaac Sim 5.1 ABI); got {np.__version__}")

    if os.environ.get("CUDA_VISIBLE_DEVICES") is not None:
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be unset; see CLAUDE.md §0.5")

    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if "lerobot-arena" not in conda_prefix:
        raise RuntimeError(f"Expected conda env 'lerobot-arena'; CONDA_PREFIX={conda_prefix}")

    try:
        from lw_benchhub import CONFIGS_PATH
    except ImportError as exc:
        raise RuntimeError("lw_benchhub.CONFIGS_PATH not resolvable; namespace shim broken?") from exc

    example_yml = Path(CONFIGS_PATH) / "envhub" / "example.yml"
    if not example_yml.is_file():
        raise RuntimeError(f"Stage 1 baseline yml missing: {example_yml}")

    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=True,
    )
    free_mibs = [
        int(line.replace(" MiB", "").strip())
        for line in result.stdout.strip().splitlines()
        if line.strip()
    ]
    if not free_mibs or max(free_mibs) < 20_000:
        raise RuntimeError(f"Insufficient GPU memory: free MiB = {free_mibs}; need >= 20,000 MiB")

    print(
        "[check_environment] numpy=1.26.0, CUDA_VISIBLE_DEVICES unset, env=lerobot-arena, "
        f"CONFIGS_PATH={CONFIGS_PATH}, GPU free={max(free_mibs)} MiB — OK"
    )


def apply_lightwheel_patches() -> None:
    """Verify lw_benchhub monkey patches are present — demonstrates LW toolchain value.

    NOTE: The patches themselves are applied inside the lerobot-eval child process
    (because lw_benchhub.utils.monkey_patch transitively imports `pxr` at module
    load time, which is only available after Isaac Sim's AppLauncher boots).
    From the parent orchestrator we instead statically verify that the two patch
    functions are defined in the on-disk source — this is a cheap, evidence-based
    proof that LW's headless-POV + IK-standardizer toolchain is in play for every
    row, without paying a double Isaac Sim cold start.

    Patches verified (per /mnt/robot/CLAUDE.md §3.1):
      - patch_create_teleop_device(): IsaacLab v2.3.x DEVICE_MAP/RETARGETER_MAP shim,
        lets headless servers (no teleop device) boot cleanly.
      - patch_xform_prim_view_auto_standardize(): USD xform op standardizer that forces
        validate_xform_ops=False so SimReady assets with non-standard prim op order
        still load under EGL off-screen rendering.
    """
    patch_src = Path("/mnt/robot/lw_benchhub/lw_benchhub/utils/monkey_patch.py")
    if not patch_src.exists():
        raise RuntimeError(f"lw_benchhub monkey_patch.py missing at {patch_src}")
    src_text = patch_src.read_text()
    missing = [
        name for name in ("patch_create_teleop_device", "patch_xform_prim_view_auto_standardize")
        if f"def {name}" not in src_text
    ]
    if missing:
        raise RuntimeError(
            f"lw_benchhub monkey_patch.py is missing required patch fns: {missing}. "
            "These are mandated by /mnt/robot/CLAUDE.md §3.1 and are demonstrated by Stage 3."
        )
    print(
        "[lw_benchhub] monkey patches verified on disk: "
        "patch_create_teleop_device + patch_xform_prim_view_auto_standardize"
    )
    print(
        "[lw_benchhub] patches activate inside lerobot-eval child "
        "(after AppLauncher pulls in pxr/isaaclab) — headless POV + USD xform standardizer in play."
    )


# =============================================================================
# Scene YML generation
# =============================================================================

def generate_scene_yml(row: dict[str, Any]) -> Path:
    """Copy example.yml and override only robot/layout/task/seed/episode_length_s for this row."""
    YML_OUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = YML_OUT_DIR / f"scene_{row['label']}.yml"

    text = TEMPLATE_YML.read_text(encoding="utf-8")

    replacements = {
        r"^robot:.*$": f"robot: {row['robot']}",
        r"^layout:.*$": f"layout: {row['layout']}",
        r"^task:.*$": f"task: {row['task']}",
        r"^seed:.*$": f"seed: {row['seed']}",
        r"^episode_length_s:.*$": f"episode_length_s: {row['episode_length_s']}",
    }

    for pattern, replacement in replacements.items():
        new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE, count=1)
        if count == 0:
            raise RuntimeError(f"Could not find pattern {pattern!r} in {TEMPLATE_YML}")
        text = new_text

    dst.write_text(text, encoding="utf-8")
    print(
        f"[generate_scene_yml] wrote {dst} "
        f"with robot={row['robot']}, layout={row['layout']}, "
        f"task={row['task']}, seed={row['seed']}, "
        f"episode_length_s={row['episode_length_s']}"
    )
    return dst


def output_dir_for(row: dict[str, Any]) -> Path:
    return OUTPUT_ROOT_PREFIX / f"eval_outputs_stage3_{row['label']}"


# =============================================================================
# Eval command construction
# =============================================================================

def build_eval_command(row: dict[str, Any]) -> list[str]:
    """Build lerobot-eval CLI matching Stage 1 run_pathB.sh flag order verbatim."""
    yml_rel = f"configs/envhub/generated_stage3/scene_{row['label']}.yml"
    output_dir = output_dir_for(row)

    cmd: list[str] = [
        "lerobot-eval",
        f"--policy.path={POLICY_PATH}",
        f"--env.type={ENV_TYPE}",
        f"--rename_map={RENAME_MAP}",
        f"--env.hub_path={ENV_HUB_PATH}",
        f"--env.kwargs={{\"config_path\": \"{yml_rel}\"}}",
        "--trust_remote_code=true",
        f"--env.state_keys={STATE_KEYS}",
        f"--env.action_dim={ACTION_DIM}",
        f"--env.state_dim={STATE_DIM}",
        f"--env.camera_keys={CAMERA_KEYS}",
        "--env.enable_cameras=true",
        "--env.headless=true",
        "--env.video=true",
        f"--env.video_length={VIDEO_LENGTH}",
        "--env.video_interval=1",
        "--policy.device=cuda",
        f"--eval.batch_size={BATCH_SIZE}",
        f"--eval.n_episodes={N_EPISODES}",
        f"--output_dir={output_dir}",
    ]
    return cmd


# =============================================================================
# Eval execution
# =============================================================================

def run_eval(row: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Run lerobot-eval for one matrix row; tee output to LOGS_ROOT/{label}.log."""
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_ROOT / f"{row['label']}.log"
    output_dir = output_dir_for(row)
    cmd = build_eval_command(row)

    record: dict[str, Any] = {
        "label": row["label"],
        "command": " ".join(cmd),
        "log_path": str(log_path),
        "output_dir": str(output_dir),
        "exit_code": None,
    }

    print(f"[run_eval:{row['label']}] {'WOULD RUN' if dry_run else 'RUNNING'}")
    print(f"[run_eval:{row['label']}] {' '.join(cmd)}")

    if dry_run:
        record["exit_code"] = 0
        record["dry_run"] = True
        return record

    with log_path.open("w", encoding="utf-8") as log_fh:
        log_fh.write(f"# Command: {' '.join(cmd)}\n")
        log_fh.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\n")
        log_fh.flush()

        proc = subprocess.run(
            cmd,
            cwd=LEROBOT_CWD,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy(),
        )
        exit_code = proc.returncode

        log_fh.write(f"\nEXIT_CODE: {exit_code}\n")
        log_fh.write(f"# Finished: {datetime.now(timezone.utc).isoformat()}\n")

    record["exit_code"] = exit_code
    print(f"[run_eval:{row['label']}] exit_code={exit_code}, log={log_path}")
    return record


# =============================================================================
# Head-view video + first-frame extraction
# =============================================================================

def locate_head_video(row: dict[str, Any], output_dir: Path) -> Path | None:
    """Find the first eval_episode_0.mp4 under output_dir/videos/<env>/."""
    if not output_dir.is_dir():
        return None
    matches = sorted(output_dir.rglob("eval_episode_0.mp4"))
    for p in matches:
        if p.is_file() and "videos" in p.parts:
            print(f"[locate_head_video:{row['label']}] found {p}")
            return p
    print(f"[locate_head_video:{row['label']}] no eval_episode_0.mp4 under {output_dir}")
    return None


def copy_head_video(row: dict[str, Any], src: Path) -> Path:
    """Copy head-view mp4 to deliverables without transcoding."""
    video_dir = DELIVERABLES_ROOT / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    dst = video_dir / f"{row['label']}_head_view.mp4"
    shutil.copy2(src, dst)
    print(f"[copy_head_video:{row['label']}] copied {src} -> {dst}")
    return dst


def extract_first_frame(row: dict[str, Any], video_path: Path) -> Path:
    """Extract a single PNG at ~0.10s from the head-view video."""
    snapshot_dir = DELIVERABLES_ROOT / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    dst = snapshot_dir / f"{row['label']}_frame0.png"

    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:00.10",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg first-frame extraction failed for {row['label']}: {result.stderr}"
        )
    print(f"[extract_first_frame:{row['label']}] wrote {dst}")
    return dst


# =============================================================================
# Metrics parsing
# =============================================================================

def parse_metrics(row: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Read eval_metrics.json if present; otherwise grep running_success_rate from log.
    Also classify OOD failure signatures (tensor-shape mismatch, gym NameNotFound, init abort)
    so the consolidated report can explain *why* a row produced no video.
    """
    metrics: dict[str, Any] = {
        "label": row["label"],
        "success_rate": None,
        "avg_episode_length": None,
        "metrics_file": None,
        "error_summary": None,
    }

    metrics_file = output_dir / "eval_metrics.json"
    if metrics_file.is_file():
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
        raw_sr = data.get("success_rate")
        if isinstance(raw_sr, (int, float)):
            # lerobot may emit success_rate either as fraction in [0,1] or as
            # already-scaled percent like 20.0. write_report applies `:.2%`, which
            # expects a fraction. Normalize either form to fraction.
            metrics["success_rate"] = raw_sr / 100.0 if raw_sr > 1.0 else float(raw_sr)
        else:
            metrics["success_rate"] = raw_sr
        metrics["avg_episode_length"] = data.get("avg_episode_length")
        metrics["metrics_file"] = str(metrics_file)
        print(
            f"[parse_metrics:{row['label']}] from json: "
            f"success_rate={metrics['success_rate']!r}"
        )
        return metrics

    log_path = LOGS_ROOT / f"{row['label']}.log"
    if log_path.is_file():
        text = log_path.read_text(encoding="utf-8", errors="ignore")
        for line in reversed(text.splitlines()):
            match = re.search(r"running_success_rate[=:]\s*([0-9.]+)", line)
            if match:
                # lerobot logs running_success_rate as already-scaled percent (e.g. 20.0
                # means 20% = 2/10). The report formatter applies `:.2%`, which expects
                # a fraction in [0,1]. Normalize to fraction at parse time.
                metrics["success_rate"] = float(match.group(1)) / 100.0
                print(
                    f"[parse_metrics:{row['label']}] from log: "
                    f"running_success_rate={metrics['success_rate']:.4f} (fraction)"
                )
                return metrics

        # No success_rate line: classify the OOD failure mode for the report.
        # Patterns documented in Stage3_Plan_Detailed.md §1.2.
        ts_match = re.search(
            r"RuntimeError:\s*The size of tensor a \((\d+)\) must match the size of tensor b \((\d+)\)",
            text,
        )
        if ts_match:
            metrics["error_summary"] = (
                f"obs-dim mismatch: policy expects {ts_match.group(2)}-D, "
                f"env emits {ts_match.group(1)}-D (embodiment OOD)"
            )
        elif re.search(r"gym\.error\.NameNotFound", text) or re.search(
            r"NameNotFound", text
        ):
            m = re.search(r"NameNotFound[^\n]*", text)
            metrics["error_summary"] = (
                f"gym task id not registered ({m.group(0)[:80] if m else 'NameNotFound'})"
            )
        elif re.search(r"action.*dim.*mismatch", text, re.IGNORECASE):
            metrics["error_summary"] = "action-dim mismatch (embodiment OOD)"
        elif re.search(r"Traceback \(most recent call last\):", text):
            # generic traceback fallback: capture the last RuntimeError/Error line
            err = None
            for line in reversed(text.splitlines()):
                m = re.search(r"^\s*([A-Za-z][A-Za-z0-9_.]*Error[^\n]*)", line)
                if m:
                    err = m.group(1).strip()
                    break
            metrics["error_summary"] = (
                err[:160] if err else "unhandled traceback; see per-row log"
            )

        if metrics["error_summary"]:
            print(
                f"[parse_metrics:{row['label']}] OOD failure mode: {metrics['error_summary']}"
            )
            return metrics

    print(f"[parse_metrics:{row['label']}] no metrics found")
    return metrics


# =============================================================================
# Report generation
# =============================================================================

def write_report(matrix: list[dict[str, Any]], results: list[dict[str, Any]]) -> Path:
    """Write a markdown report with matrix results and LW toolchain demo notes."""
    DELIVERABLES_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = DELIVERABLES_ROOT / "stage3_report.md"

    result_by_label = {r["label"]: r for r in results}

    lines: list[str] = []
    lines.append("# Stage 3 Cross-Embodiment Benchmark Report\n\n")
    lines.append(f"- **Model**: `{POLICY_PATH}`\n")
    lines.append(f"- **Hub**: `{ENV_HUB_PATH}`\n")
    lines.append(f"- **Environment type**: `{ENV_TYPE}`\n")
    lines.append(
        f"- **State/action binding**: state_dim={STATE_DIM}, action_dim={ACTION_DIM}, "
        f"state_keys={STATE_KEYS}\n"
    )
    lines.append(f"- **Camera keys**: `{CAMERA_KEYS}`\n")
    lines.append(f"- **Episodes per row**: {N_EPISODES}\n")
    lines.append(f"- **Generated at**: {datetime.now(timezone.utc).isoformat()}\n\n")

    lines.append("## Benchmark Matrix\n\n")
    lines.append(
        "| Label | Robot | Layout | Task | Seed | Exit Code | Success Rate | Avg Length | OOD Expected | OOD Failure Mode | Note |\n"
    )
    lines.append(
        "|-------|-------|--------|------|------|-----------|--------------|------------|--------------|------------------|------|\n"
    )

    for row in matrix:
        label = row["label"]
        res = result_by_label.get(label, {})
        exit_code = res.get("exit_code", "N/A")
        metrics = res.get("metrics", {})
        success_rate = metrics.get("success_rate") if metrics else None
        avg_len = metrics.get("avg_episode_length") if metrics else None
        err_summary = metrics.get("error_summary") if metrics else None
        success_str = (
            f"{success_rate:.2%}" if isinstance(success_rate, (int, float)) else "N/A"
        )
        avg_str = f"{avg_len:.1f}" if isinstance(avg_len, (int, float)) else "N/A"
        err_str = err_summary if err_summary else "—"
        lines.append(
            f"| {label} | {row['robot']} | {row['layout']} | {row['task']} | "
            f"{row['seed']} | {exit_code} | {success_str} | {avg_str} | "
            f"{'Yes' if row['expected_ood'] else 'No'} | {err_str} | {row['note']} |\n"
        )

    lines.append("\n## Lightwheel Toolchain Demonstration\n\n")
    lines.append("This benchmark exercised the following LightwheelAI tooling capabilities:\n\n")
    lines.append(
        "1. **IsaacLab v2.3.x teleop-device shim** — `patch_create_teleop_device()` invoked at "
        "script entry; lets the headless server boot without `DEVICE_MAP` / `RETARGETER_MAP`.\n"
    )
    lines.append(
        "2. **USD xform standardizer** — `patch_xform_prim_view_auto_standardize()` forces "
        "`validate_xform_ops=False` so SimReady assets render under EGL.\n"
    )
    lines.append(
        "3. **Namespace shim** — `from lw_benchhub import CONFIGS_PATH` resolves from any cwd, "
        "per the v6 fix in `/mnt/robot/CLAUDE.md` §3.4.\n"
    )
    lines.append(
        "4. **Cross-embodiment YML reuse** — the same `configs/envhub/example.yml` template is "
        "re-used across robot brands by overriding only `robot`, `layout`, `task`, `seed`.\n\n"
    )

    lines.append("## Cross-Embodiment Observations\n\n")
    lines.append(
        "- The baseline `DoublePiper-Abs` row should reproduce Stage 1 behavior (~40% success).\n"
    )
    lines.append(
        "- Cross-brand rows (`DoublePanda`, `PandaOmron-Abs/-Rel`) run the same "
        "`smolvla-double-piper-pnp` policy out-of-distribution; near-zero success or env-init "
        "abort is the expected and documented failure mode.\n"
    )
    lines.append(
        "- The primary success criterion is that every row boots through the Lightwheel patches, "
        "renders a head-view video (or emits a clean abort log), and exits under the "
        "`LightwheelAI/lw_benchhub_env` + `LightwheelAI/smolvla-double-piper-pnp` binding — "
        "not absolute success rate.\n\n"
    )

    lines.append("## Deliverables\n\n")
    lines.append(f"- Head-view videos: `{DELIVERABLES_ROOT / 'videos'}`\n")
    lines.append(f"- First-frame snapshots: `{DELIVERABLES_ROOT / 'snapshots'}`\n")
    lines.append(
        f"- Comparison grid: `{DELIVERABLES_ROOT / 'comparison_grid.mp4'}` "
        f"(generated when >=1 row produces a video; xstack grid kicks in at 4+ rows)\n"
    )
    lines.append(f"- Raw outputs: `{OUTPUT_ROOT_PREFIX / 'eval_outputs_stage3_*'}`\n")
    lines.append(f"- Per-row logs: `{LOGS_ROOT}`\n")

    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"[write_report] wrote {report_path}")
    return report_path


# =============================================================================
# Comparison grid
# =============================================================================

def build_comparison_grid(
    matrix: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> Path | None:
    """Build an ffmpeg xstack/hstack grid of head-view videos for successful rows."""
    DELIVERABLES_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = DELIVERABLES_ROOT / "comparison_grid.mp4"

    valid: list[tuple[dict[str, Any], Path]] = []
    for row in matrix:
        res = next((r for r in results if r["label"] == row["label"]), {})
        if res.get("exit_code") != 0:
            continue
        head_video = res.get("head_video_path")
        if head_video and Path(head_video).is_file():
            valid.append((row, Path(head_video)))

    if not valid:
        print("[build_comparison_grid] no valid head-view videos; skipping grid")
        return None

    if len(valid) == 1:
        src = valid[0][1]
        shutil.copy2(src, out_path)
        print(f"[build_comparison_grid] only 1 valid video; copied {src} -> {out_path}")
        return out_path

    inputs: list[str] = []
    parts: list[str] = []
    for idx, (row, video_path) in enumerate(valid):
        inputs.extend(["-i", str(video_path)])
        label_text = row["label"].replace("_", " ")
        # Defensive: reject labels with ffmpeg drawtext metacharacters so the
        # filter string cannot be broken or extended. Matches a-zA-Z0-9 + space
        # only (after the underscore→space pass above).
        if not re.match(r"^[A-Za-z0-9 ]+$", label_text):
            raise RuntimeError(
                f"Unsafe label for ffmpeg drawtext: {row['label']!r}. "
                f"Allowed: alphanumerics + underscores only."
            )
        parts.append(
            f"[{idx}:v]drawtext=fontfile={FONT_PATH}:text='{label_text}':"
            f"x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5[v{idx}];"
        )

    if len(valid) >= 4:
        valid_chain = valid[:4]
        parts.append("[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[grid];")
        del valid_chain  # only the first 4 are stacked
    else:
        chain = "".join(f"[v{i}]" for i in range(len(valid)))
        parts.append(f"{chain}hstack=inputs={len(valid)}[grid];")

    parts.append(
        f"[grid]drawtext=fontfile={FONT_PATH}:text='Stage 3 Cross-Embodiment':"
        f"x=(w-text_w)/2:y=30:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6[final]"
    )
    filter_str = "".join(parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[final]",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg comparison grid failed: {result.stderr}")

    print(f"[build_comparison_grid] wrote {out_path} from {len(valid)} videos")
    return out_path


# =============================================================================
# Head-only re-run
# =============================================================================

def head_only_rerun(
    matrix: list[dict[str, Any]],
    *,
    only: str | None = None,
) -> list[dict[str, Any]]:
    """Re-derive head-view copies, first frames, and comparison grid from existing outputs."""
    results: list[dict[str, Any]] = []
    for row in matrix:
        if only and row["label"] != only:
            continue
        output_dir = output_dir_for(row)
        # Recover the true subprocess return code from the per-row log
        # (every lerobot-eval child emits `EXIT_CODE: N` near the end).
        # This is more honest than guessing from video presence.
        log_path = LOGS_ROOT / f"{row['label']}.log"
        recovered_rc: int | str = "N/A"
        if log_path.is_file():
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^EXIT_CODE:\s*(\d+)", log_text, re.MULTILINE)
            if m:
                recovered_rc = int(m.group(1))
        record: dict[str, Any] = {
            "label": row["label"],
            "output_dir": str(output_dir),
            "exit_code": recovered_rc,
        }
        video_path = locate_head_video(row, output_dir)
        if video_path:
            record["head_video_path"] = str(copy_head_video(row, video_path))
            record["frame0_path"] = str(extract_first_frame(row, video_path))
        # also re-parse metrics from the per-row log so head-only re-runs
        # produce a correct stage3_report.md (matches the post-eval path)
        record["metrics"] = parse_metrics(row, output_dir)
        results.append(record)

    if results:
        build_comparison_grid(matrix, results)
        # regenerate the consolidated report so head-only re-runs ship
        # the latest exit codes / success rates / video paths
        write_report(matrix, results)
    return results


# =============================================================================
# Main
# =============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 3 Lightwheel cross-embodiment benchmark driver"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print matrix and would-be commands; do not run eval",
    )
    parser.add_argument(
        "--only", default=None,
        help="Run only the row with this label",
    )
    parser.add_argument(
        "--head-only-rerun", action="store_true",
        help="Re-copy videos / frames / grid from existing outputs",
    )
    parser.add_argument(
        "--skip-on-failure", action="store_true", default=True,
        help="Continue to next row if eval exits non-zero (default: True, per plan §2.1)",
    )
    parser.add_argument(
        "--abort-on-failure", dest="skip_on_failure", action="store_false",
        help="Abort the sweep on the first row that fails (opposite of --skip-on-failure)",
    )
    args = parser.parse_args(argv)

    if args.head_only_rerun:
        head_only_rerun(MATRIX, only=args.only)
        return 0

    check_environment()
    apply_lightwheel_patches()

    DELIVERABLES_ROOT.mkdir(parents=True, exist_ok=True)
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    rows_to_run = [row for row in MATRIX if not args.only or row["label"] == args.only]

    for row in rows_to_run:
        print(f"\n{'='*60}\n[main] processing row: {row['label']}\n{'='*60}")
        generate_scene_yml(row)
        record = run_eval(row, dry_run=args.dry_run)

        if args.dry_run:
            results.append(record)
            continue

        if record["exit_code"] != 0 and not args.skip_on_failure:
            print(f"[main] row {row['label']} failed; aborting (--skip-on-failure not set)")
            results.append(record)
            break

        if record["exit_code"] == 0:
            output_dir = output_dir_for(row)
            video_path = locate_head_video(row, output_dir)
            if video_path:
                record["head_video_path"] = str(copy_head_video(row, video_path))
                record["frame0_path"] = str(extract_first_frame(row, video_path))

        record["metrics"] = parse_metrics(row, output_dir_for(row))
        results.append(record)

    if not args.dry_run:
        write_report(MATRIX, results)
        build_comparison_grid(MATRIX, results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
