#!/usr/bin/env python3
"""Boot Isaac Sim once for one seed yml, read akita_black_bowl + robot world pose, write JSON.
Mirrors validate_scene_objects_reach_v5._boot_env import order (no monkey_patch; AppLauncher-first)."""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

# env vars MUST be set before isaaclab import (v6 validator pattern)
os.environ.setdefault("ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT", "1")
os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "Y")
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()

    # AppLauncher import BEFORE lw_benchhub envhub_utils (ordering); both deferred-safe at top level
    from isaaclab.app import AppLauncher  # noqa: F401
    from lw_benchhub.utils.envhub_utils import export_env_for_envhub

    last_exc = None
    for attempt in range(3):
        try:
            raw_env, environment, task, render_mode, episode_length, app_launcher = export_env_for_envhub(
                config_path=args.config
            )
            raw_env.reset()
            break
        except Exception as e:
            msg = str(e)
            transient = any(s in msg for s in (
                "SSLError", "SSLEOFError", "EOF occurred", "Max retries exceeded",
                "Connection aborted", "TimeoutError", "Read timed out",
            ))
            if not transient or attempt == 2:
                raise
            last_exc = e
            print(f"[probe] transient boot error attempt {attempt+1}, retry 5s: {msg[:160]}", flush=True)
            time.sleep(5)
    else:
        raise last_exc

    env = raw_env
    scene = env.scene
    rigid_dict = getattr(scene, "rigid_objects", None) or getattr(scene, "_rigid_objects", {})
    bowl = rigid_dict["akita_black_bowl"].data.root_pos_w[0].detach().cpu().numpy()
    rpos = None
    art_dict = getattr(scene, "articulations", None) or getattr(scene, "_articulations", {})
    for name, art in art_dict.items():
        if "piper" in name.lower() or "robot" in name.lower():
            rpos = art.data.root_state_w[0, :3].detach().cpu().numpy(); break
    if rpos is None:
        for name, art in art_dict.items():
            rpos = art.data.root_state_w[0, :3].detach().cpu().numpy(); break
    dist = float(((bowl - rpos) ** 2).sum() ** 0.5)
    result = {"seed": args.seed, "bowl_world": bowl.tolist(),
              "robot_world": rpos.tolist(), "dist_to_robot": dist}
    Path(args.out).write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps(result), flush=True)
    try:
        app_launcher.close()
    except Exception:
        pass

main()
