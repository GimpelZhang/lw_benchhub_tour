# Copyright 2025 Lightwheel Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simplified local replay entry: supports replay modes `action` and `state` only."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import gymnasium as gym
import h5py
import numpy as np
import torch
from isaaclab.app import AppLauncher

from lw_benchhub.utils.env import ExecuteMode, parse_env_cfg
from lw_benchhub.utils.teleop_utils import get_state_by_frame


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay local task episodes (action/state only).")
    parser.add_argument("--dataset_file", type=str, required=True, help="Input dataset .hdf5 file path.")
    parser.add_argument("--replay_mode", type=str, default="action", choices=["action", "state"], help="Replay mode.")
    parser.add_argument("--layout", type=str, default="/path/to/scene.usd", help="Override scene layout path/name.")
    parser.add_argument("--first_person_view", action="store_true", default=False, help="Use first-person view.")
    parser.add_argument("--record", action="store_true", default=False, help="Record replay rollout to dataset.")
    AppLauncher.add_app_launcher_args(parser)
    return parser


def _to_env_action(action, env):
    if not isinstance(action, torch.Tensor):
        action = torch.as_tensor(action, dtype=torch.float32, device=env.device)
    else:
        action = action.to(device=env.device, dtype=torch.float32)
    if action.ndim == 1:
        action = action.unsqueeze(0)
    elif action.ndim > 2:
        action = action.reshape(action.shape[0], -1)
    if action.shape[0] != 1:
        raise ValueError(f"Invalid action batch shape {tuple(action.shape)} for num_envs=1.")
    return action


def _record_video_frame(env, video_recorder, frame_store: dict[str, list] | None = None):
    if video_recorder is None:
        return
    obs = env.observation_manager.compute()
    policy_obs = obs.get("policy", {}) if isinstance(obs, dict) else {}
    camera_names = list(getattr(env.cfg.isaaclab_arena_env.embodiment, "active_observation_camera_names", []))

    images, used_names = [], []
    for camera_name in camera_names:
        image = policy_obs.get(camera_name)
        if isinstance(image, torch.Tensor) and image.ndim in (3, 4):
            image = image[0] if image.ndim == 4 else image
            images.append(image)
            used_names.append(camera_name)
            if frame_store is not None:
                frame_store.setdefault(camera_name, []).append(image.detach().clone().cpu())

    if not images:
        return

    if len(images) == 1:
        combined, combined_name = images[0], used_names[0]
    else:
        max_height = max(img.shape[0] for img in images)
        padded = [img if img.shape[0] == max_height else torch.cat([
            img,
            torch.full((max_height - img.shape[0], img.shape[1], img.shape[2]), 255 if img.dtype == torch.uint8 else 1.0, dtype=img.dtype, device=img.device)
        ], dim=0) for img in images]
        combined = torch.cat(padded, dim=1)
        combined_name = "__".join(used_names)

    if video_recorder.video_writer is None:
        video_recorder.start_recording(combined_name, (int(combined.shape[0]), int(combined.shape[1])))
    video_recorder.add_frame(combined)


def _keep_latest_video_only(video_dir):
    if not video_dir:
        return
    video_dir = Path(video_dir)
    videos = sorted(video_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime) if video_dir.exists() else []
    for old_video in videos[:-1]:
        old_video.unlink(missing_ok=True)


def _build_local_env(args, app_launcher, env_args: dict, task_name: str, robot_name: str, scene_name: str, episode_name: str):

    execute_mode = ExecuteMode.REPLAY_ACTION if args.replay_mode == "action" else ExecuteMode.REPLAY_STATE
    add_camera_to_observation = bool(app_launcher._enable_cameras and args.record)

    env_cfg = parse_env_cfg(
        scene_backend="local",
        task_backend="local",
        task_name=task_name,
        robot_name=robot_name,
        scene_name=scene_name,
        robot_scale=1.0,
        device=args.device,
        num_envs=1,
        use_fabric=True,
        replay_cfgs={
            "hdf5_path": args.dataset_file,
            "ep_meta": env_args,
            "ep_name": episode_name,
            "add_camera_to_observation": add_camera_to_observation,
        },
        first_person_view=args.first_person_view,
        enable_cameras=app_launcher._enable_cameras,
        execute_mode=execute_mode,
        usd_simplify=False,
        seed=env_args.get("seed", None),
        sources=env_args.get("sources", env_args.get("source", None)),
        object_projects=env_args.get("object_projects", None),
        headless_mode=args.headless,
    )

    env_name = f"LocalReplay-{task_name}-{robot_name}-v0"
    env_cfg.env_name = env_name
    env_cfg.terminations.time_out = None

    if env_name in gym.envs.registry:
        gym.envs.registry.pop(env_name)
    gym.register(
        id=env_name,
        entry_point="isaaclab.envs:ManagerBasedRLEnv",
        kwargs={},
        disable_env_checker=True,
    )
    env = gym.make(env_name, cfg=env_cfg).unwrapped
    return env


def _replay_action_episode(env, episode_data, simulation_app, video_recorder=None, camera_frames: dict[str, list] | None = None):
    initial_state = episode_data.get_initial_state()
    if initial_state is None:
        return
    env.reset_to(initial_state, torch.tensor([0], device=env.device), seed=env.cfg.seed, is_relative=False)
    _record_video_frame(env, video_recorder, frame_store=camera_frames)
    while simulation_app.is_running() and (action := episode_data.get_next_action()) is not None:
        env.step(_to_env_action(action, env))
        _record_video_frame(env, video_recorder, frame_store=camera_frames)


def _replay_state_episode(env, args, episode_data, simulation_app, is_relative: bool, video_recorder=None, camera_frames: dict[str, list] | None = None):
    initial_state = episode_data.get_initial_state()
    if initial_state is None:
        return
    env_ids = torch.tensor([0], device=env.device)
    env.reset_to(initial_state, env_ids, seed=env.cfg.seed, is_relative=False)
    _record_video_frame(env, video_recorder, frame_store=camera_frames)

    frame_index = 0
    while simulation_app.is_running() and (state := get_state_by_frame(episode_data, frame_index)) is not None:
        env.reset_to(state, env_ids, seed=env.cfg.seed, is_relative=is_relative)
        if not args.headless:
            env.sim.render()
        _record_video_frame(env, video_recorder, frame_store=camera_frames)
        frame_index += 1


def main():
    from isaaclab.utils.datasets import HDF5DatasetFileHandler

    parser = _build_parser()
    args = parser.parse_args()

    dataset_path = os.path.abspath(args.dataset_file)
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file does not exist: {dataset_path}")

    dataset_handler = HDF5DatasetFileHandler()
    dataset_handler.open(dataset_path)
    if dataset_handler.get_num_episodes() == 0:
        print("No episodes found in dataset.")
        return

    episode_names = sorted(dataset_handler.get_episode_names(), key=lambda v: int(v.split("_")[-1]))
    episode_name = episode_names[-1]

    env_args = json.loads(dataset_handler._hdf5_data_group.attrs["env_args"])
    task_name, robot_name, scene_name = env_args["task_name"], env_args["robot_name"], args.layout

    app_launcher = AppLauncher(args)
    simulation_app = app_launcher.app

    from lw_benchhub.utils.place_utils.env_utils import reset_physx
    env = _build_local_env(args, app_launcher, env_args, task_name, robot_name, scene_name, episode_name)
    reset_physx(env)
    env.reset(seed=env.cfg.seed)

    video_recorder = None
    if args.record and app_launcher._enable_cameras:
        from lw_benchhub.utils.video_recorder import VideoRecorder
        video_save_dir = os.path.dirname(args.dataset_file)
        video_recorder = VideoRecorder(save_dir=video_save_dir, fps=30, task=task_name, robot=robot_name, layout=scene_name)
        print(f"[replay_local] video save dir: {video_recorder.save_dir}")

    episode_data = dataset_handler.load_episode(episode_name, env.device)
    if args.replay_mode == "action":
        camera_frames = {}
        _replay_action_episode(env, episode_data, simulation_app, video_recorder, camera_frames)
    else:
        camera_frames = {}
        is_relative = str(robot_name).lower().endswith("rel")
        _replay_state_episode(env, args, episode_data, simulation_app, is_relative, video_recorder, camera_frames)

        if args.record:
            dataset_handler.close()
            new_dataset_path = os.path.join(os.path.dirname(dataset_path), "dataset_with_video.hdf5")

            with h5py.File(dataset_path, "r") as f_in, h5py.File(new_dataset_path, "w") as f_out:
                f_in.copy("data", f_out, "data")
                for attr_name in f_in["data"].attrs.keys():
                    f_out["data"].attrs[attr_name] = f_in["data"].attrs[attr_name]

                ep_group = f_out["data"][episode_name]
                obs_group = ep_group.require_group("obs")
                for cam_name, frame_list in camera_frames.items():
                    frames = torch.stack([f if isinstance(f, torch.Tensor) else torch.tensor(f) for f in frame_list], dim=0)
                    frames = frames.detach().cpu().numpy()
                    if isinstance(frames, np.ndarray) and frames.dtype.kind != 'O':
                        if cam_name in obs_group:
                            del obs_group[cam_name]
                        obs_group.create_dataset(cam_name, data=frames)

            print(f"Dataset with video saved to: {new_dataset_path}")

    if video_recorder is not None:
        video_recorder.stop_recording()
        _keep_latest_video_only(video_recorder.save_dir)

    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
