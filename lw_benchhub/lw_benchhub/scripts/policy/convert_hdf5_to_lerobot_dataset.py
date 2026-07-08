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

import argparse
import os
from pathlib import Path

import h5py
import numpy as np
import tqdm

from lerobot.datasets.lerobot_dataset import LeRobotDataset

VIDEO_INFO = {
    "video.fps": 30.0,
    "video.codec": "h264",
    "video.pix_fmt": "yuv420p",
    "video.is_depth_map": False,
    "has_audio": False,
}


def _build_features(camera_paths: list[str], state_dim: int, action_dim: int, camera_shape: tuple = None) -> dict:
    features = {
        "observation.state": {"dtype": "float32", "shape": (state_dim,), "names": None},
        "action": {"dtype": "float32", "shape": (action_dim,), "names": None},
        "episode_index": {"dtype": "int64", "shape": (1,), "names": None},
        "frame_index": {"dtype": "int64", "shape": (1,), "names": None},
        "index": {"dtype": "int64", "shape": (1,), "names": None},
        "task_index": {"dtype": "int64", "shape": (1,), "names": None},
    }

    for camera_path in camera_paths:
        camera_name = camera_path.split("/")[-1]
        features[f"observation.images.{camera_name}"] = {
            "dtype": "video",
            "shape": camera_shape,
            "names": ["height", "width", "channel"],
            "video_info": VIDEO_INFO,
        }

    return features


def convert_isaaclab_to_lerobot(args):

    repo_id = args.tgt_repo_id or f"{Path(args.root_path).stem}-lerobot"
    root = Path(args.root_path).parent / repo_id
    robot_type = args.robot_type

    clip_names = os.listdir(args.root_path)
    dataset_files = [os.path.join(args.root_path, clip_name, 'dataset_with_video.hdf5') for clip_name in clip_names]

    with h5py.File(dataset_files[0], "r") as f:
        demo_names = list(f["data"].keys())
        demo_names.sort(key=lambda x: int(x.split("_")[-1]))
        demo_name = demo_names[-1]
        demo_group = f["data"][demo_name]
        actions = np.asarray(demo_group["actions"])
        states = np.asarray(demo_group["obs/joint_pos"])
        state_dim = int(states.shape[1])
        action_dim = int(actions.shape[1])
        camera_shapes = np.asarray(demo_group[args.camera_path_in_hdf5[0]])[0].shape

    features = _build_features(args.camera_path_in_hdf5, state_dim, action_dim, camera_shapes)
    dataset = LeRobotDataset.create(
        repo_id=repo_id,
        root=str(root),
        fps=30,
        robot_type=robot_type,
        features=features,
    )

    success = 0
    failed = 0
    failed_list = []

    for i, dataset_file in enumerate(dataset_files):
        try:
            process_hdf5(dataset, dataset_file, args)
            success += 1
            print(f"Processed {i+1}/{len(dataset_files)}: {dataset_file}")
        except Exception as e:
            failed += 1
            failed_list.append(dataset_file)
        print(f"Success: {success}, Failed: {failed}")
        print(f"Failed list: {failed_list}")


def process_hdf5(dataset, hdf5_path, args):
    with h5py.File(hdf5_path, "r") as f:
        demo_names = list(f["data"].keys())
        demo_names.sort(key=lambda x: int(x.split("_")[-1]))

        if args.only_last_demo:
            demo_names = [demo_names[-1]]

        for i in tqdm.tqdm(range(0, len(demo_names)), desc="Convert demos"):
            demo_name = demo_names[i]
            demo_group = f["data"][demo_name]
            actions = np.asarray(demo_group["actions"])
            states = np.asarray(demo_group["obs/joint_pos"])
            camera_arrays = {path: np.asarray(demo_group[path]) for path in args.camera_path_in_hdf5}

            T = actions.shape[0]

            for i in tqdm.tqdm(range(5, T), desc="Processing frames"):
                frame = {
                    "observation.state": states[i],
                    "action": actions[i],
                }
                for camera_path in args.camera_path_in_hdf5:
                    camera_name = camera_path.split("/")[-1]
                    frame[f"observation.images.{camera_name}"] = camera_arrays[camera_path][i]

                dataset.add_frame(frame, task=args.task_description)
            dataset.save_episode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tgt_repo_id", type=str, default="test-dataset", help="LeRobot dataset repo_id (folder name)")
    parser.add_argument("--root_path", type=str, default=None, help="Path to the root directory of the dataset")
    parser.add_argument("--only_last_demo", type=bool, default=True, help="Path to the root directory of the dataset")
    parser.add_argument("--camera_path_in_hdf5", type=list, default=["obs/first_person_camera_rgb", "obs/left_hand_camera_rgb", "obs/right_hand_camera_rgb"], help="Camera paths in hdf5 file")
    parser.add_argument("--task_description", type=str, default="X7S teleoperation task")
    parser.add_argument("--robot_type", type=str, default="X7S-Abs")
    args = parser.parse_args()

    convert_isaaclab_to_lerobot(args)
