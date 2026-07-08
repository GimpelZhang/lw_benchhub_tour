"""Convert per-episode HDF5 trajectories into a lerobot-standard dataset.

Reads stage4_flywheel/datasets/raw/{easy,medium,hard}/episode_*.h5 and writes a
LeRobotDataset (use_videos=False, PNG frames) to
stage4_flywheel/datasets/doublepiper_pnp_curriculum/.

The schema EXACTLY matches the original SmolVLA training dataset
(LightwheelAI/Lightwheel-Tasks-Double-Piper) + model config:
  - observation.state  : float32 (16,)  [16 sim joint names, sim order]
  - action             : float32 (12,)  [left_arm(5)|right_arm(5)|left_grip|right_grip]
  - observation.images.{left_hand,right_hand,first_person} : image (480,640,3)
  - robot_type = "double_piper", fps = 50
  - task = "put the black bowl on the plate."

This makes the dataset directly fine-tuneable on LightwheelAI/smolvla-double-piper-pnp.
"""

import json
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np
from PIL import Image

from lerobot.datasets.lerobot_dataset import LeRobotDataset

RAW_ROOT = Path("/mnt/robot/stage4_flywheel/datasets/raw")
OUT_ROOT = Path("/mnt/robot/stage4_flywheel/datasets/doublepiper_pnp_curriculum")
TASK_DESC = "put the black bowl on the plate."
FPS = 50
DIFFICULTY_ORDER = ["easy", "medium", "hard"]

# Exact joint-name lists from the original SmolVLA training dataset meta/info.json.
STATE_NAMES = [
    "joint1_r", "joint1_l", "joint2_r", "joint2_l", "joint3_r", "joint3_l",
    "joint4_r", "joint4_l", "joint5_r", "joint5_l", "joint6_r", "joint6_l",
    "finger_joint_left_r", "finger_joint_right_r", "finger_joint_left_l", "finger_joint_right_l",
]
ACTION_NAMES = [
    "joint1_l", "joint2_l", "joint3_l", "joint5_l", "joint6_l",
    "joint1_r", "joint2_r", "joint3_r", "joint5_r", "joint6_r",
    "left_gripper", "right_gripper",
]
IMAGE_NAMES = ["height", "width", "channel"]


def collect_episodes() -> list[tuple[str, int, Path]]:
    episodes = []
    for diff in DIFFICULTY_ORDER:
        diff_dir = RAW_ROOT / diff
        if not diff_dir.exists():
            continue
        for h5 in sorted(diff_dir.glob("episode_*.h5")):
            eid = int(h5.stem.split("_")[1])
            # Only include episodes whose summary marks success + n_frames>0.
            sumf = h5.parent / f"episode_{eid}_summary.json"
            if sumf.exists():
                try:
                    import json as _json
                    s = _json.loads(sumf.read_text())
                    if not (s.get("success") and s.get("n_frames", 0) > 0):
                        continue
                except Exception:
                    continue
            else:
                continue
            episodes.append((diff, eid, h5))
    return episodes


def load_episode(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as f:
        ep = {
            "states": f["observations/qpos"][:].astype(np.float32),
            "actions": f["actions"][:].astype(np.float32),
            "left": f["observations/left_hand_camera_rgb"][:] if "observations/left_hand_camera_rgb" in f else None,
            "right": f["observations/right_hand_camera_rgb"][:] if "observations/right_hand_camera_rgb" in f else None,
            "first": f["observations/first_person_camera_rgb"][:] if "observations/first_person_camera_rgb" in f else None,
            "seed": int(f["meta"].attrs["seed"]),
            "difficulty": str(f["meta"].attrs["difficulty"]),
            "success": int(f["meta"].attrs["success"]),
            "n_frames": int(f["meta"].attrs["n_frames"]),
        }
    return ep


def main():
    episodes = collect_episodes()
    if not episodes:
        print("NO EPISODES FOUND in", RAW_ROOT)
        sys.exit(1)
    print(f"Found {len(episodes)} episodes:")
    for diff, eid, p in episodes:
        print(f"  {diff}/episode_{eid} <- {p.name}")

    first = load_episode(episodes[0][2])
    state_dim = first["states"].shape[1]
    action_dim = first["actions"].shape[1]
    img_shape = tuple(first["first"].shape[1:])  # (480, 640, 3)
    print(f"Schema: state_dim={state_dim}, action_dim={action_dim}, img_shape={img_shape}")
    assert state_dim == 16 and action_dim == 12, f"expected 16/12, got {state_dim}/{action_dim}"

    # Filter to successful episodes with all 3 cameras + >0 frames.
    valid = []
    for diff, eid, p in episodes:
        ep = load_episode(p)
        ok = ep["n_frames"] > 0 and ep["success"] == 1 and ep["left"] is not None and ep["right"] is not None and ep["first"] is not None
        if not ok:
            print(f"  SKIP {diff}/episode_{eid}: n_frames={ep['n_frames']} success={ep['success']} left={ep['left'] is not None} right={ep['right'] is not None} first={ep['first'] is not None}")
            continue
        valid.append((diff, eid, p, ep))
    print(f"{len(valid)} valid successful episodes with full 3-camera coverage.")

    if not valid:
        print("NO VALID EPISODES.")
        sys.exit(1)

    features = {
        "observation.state": {"dtype": "float32", "shape": (state_dim,), "names": STATE_NAMES},
        "action": {"dtype": "float32", "shape": (action_dim,), "names": ACTION_NAMES},
        "observation.images.left_hand": {"dtype": "image", "shape": img_shape, "names": IMAGE_NAMES},
        "observation.images.right_hand": {"dtype": "image", "shape": img_shape, "names": IMAGE_NAMES},
        "observation.images.first_person": {"dtype": "image", "shape": img_shape, "names": IMAGE_NAMES},
    }

    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.parent.mkdir(parents=True, exist_ok=True)

    ds = LeRobotDataset.create(
        repo_id="doublepiper_pnp_curriculum",
        fps=FPS,
        features=features,
        root=OUT_ROOT,
        robot_type="double_piper",
        use_videos=False,
    )
    print(f"Created LeRobotDataset at {OUT_ROOT}")

    ep_records = []
    for ep_idx, (diff, eid, p, ep) in enumerate(valid):
        n = ep["n_frames"]
        for t in range(n):
            frame = {
                "task": TASK_DESC,
                "observation.state": ep["states"][t],
                "action": ep["actions"][t],
                "observation.images.left_hand": Image.fromarray(ep["left"][t]),
                "observation.images.right_hand": Image.fromarray(ep["right"][t]),
                "observation.images.first_person": Image.fromarray(ep["first"][t]),
            }
            ds.add_frame(frame)
        ds.save_episode()
        rec = {"episode_index": ep_idx, "difficulty": diff, "seed": ep["seed"], "episode_id": eid, "n_frames": n, "success": ep["success"]}
        ep_records.append(rec)
        print(f"  saved ep{ep_idx}: {diff} seed={ep['seed']} n_frames={n}")

    ds.finalize()
    print("Dataset finalized.")

    manifest = {
        "dataset_root": str(OUT_ROOT),
        "task": TASK_DESC,
        "fps": FPS,
        "robot_type": "double_piper",
        "state_dim": state_dim,
        "action_dim": action_dim,
        "image_shape": list(img_shape),
        "image_keys": ["observation.images.left_hand", "observation.images.right_hand", "observation.images.first_person"],
        "n_episodes": len(valid),
        "n_frames_total": sum(r["n_frames"] for r in ep_records),
        "distribution": {d: sum(1 for r in ep_records if r["difficulty"] == d) for d in DIFFICULTY_ORDER},
        "episodes": ep_records,
        "schema_source": "matches LightwheelAI/Lightwheel-Tasks-Double-Piper meta/info.json + smolvla-double-piper-pnp config.json",
        "fine_tune_target": "LightwheelAI/smolvla-double-piper-pnp",
        "storage": "image (PNG), use_videos=False",
    }
    manifest_path = OUT_ROOT.parent / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {manifest_path}")
    print("Distribution:", json.dumps(manifest["distribution"]))


if __name__ == "__main__":
    main()
