"""Phase 1 Task 1.3 — convert SmolVLA closed-loop HDF5 demos into a lerobot dataset.

Reads stage4_flywheel/datasets/policy_demos_v3/raw/<band>/episode_*.h5 (only TASK_SUCCESS=True
episodes, already self-filtered by generate_policy_demos.py) and writes a LeRobotDataset
(use_videos=False, PNG frames) to
stage4_flywheel/datasets/policy_demos_v3/policy_demos_v3_lerobot/.

Schema EXACTLY matches build_lerobot_dataset.py / the original SmolVLA training dataset
(LightwheelAI/Lightwheel-Tasks-Double-Piper) + smolvla-double-piper-pnp config:
  - observation.state  : float32 (16,)  [16 sim joint names, sim order]
  - action             : float32 (12,)  [left_arm(5)|right_arm(5)|left_grip|right_grip]
  - observation.images.{left_hand,right_hand,first_person} : image (480,640,3)
  - robot_type = "double_piper", fps = 50, task = "put the black bowl on the plate."

Does NOT touch doublepiper_pnp_curriculum/ (T3 protected dataset).
"""
import json
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np
from PIL import Image

# Speed up PNG encoding: LeRobotDataset encodes each camera frame as PNG (default compress_level=6,
# the build bottleneck at ~2 fps). compress_level=1 is ~2-3x faster (larger files); schema unchanged.
import PIL.Image as _PIL_Image
_orig_img_save = _PIL_Image.Image.save
def _fast_png_save(self, fp, format=None, **kwargs):
    if isinstance(format, str) and format.upper() == "PNG" and "compress_level" not in kwargs:
        kwargs["compress_level"] = 1
    return _orig_img_save(self, fp, format, **kwargs)
_PIL_Image.Image.save = _fast_png_save

from lerobot.datasets.lerobot_dataset import LeRobotDataset

RAW_ROOT = Path("/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/raw")
OUT_ROOT = Path("/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/policy_demos_v3_lerobot")
TASK_DESC = "put the black bowl on the plate."
FPS = 50

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
    """Scan all band subdirs of RAW_ROOT for successful episode HDF5s."""
    episodes = []
    if not RAW_ROOT.exists():
        return episodes
    for band_dir in sorted(RAW_ROOT.iterdir()):
        if not band_dir.is_dir():
            continue
        for h5 in sorted(band_dir.glob("episode_*.h5")):
            eid = int(h5.stem.split("_")[1])
            sumf = h5.parent / f"episode_{eid}_summary.json"
            if not sumf.exists():
                continue
            try:
                s = json.loads(sumf.read_text())
                if not (s.get("success") and s.get("n_frames", 0) > 0):
                    continue
            except Exception:
                continue
            episodes.append((band_dir.name, eid, h5))
    return episodes


def load_episode(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as f:
        meta = f["meta"].attrs
        ep = {
            "states": f["observations/qpos"][:].astype(np.float32),
            "actions": f["actions"][:].astype(np.float32),
            "left": f["observations/left_hand_camera_rgb"][:] if "observations/left_hand_camera_rgb" in f else None,
            "right": f["observations/right_hand_camera_rgb"][:] if "observations/right_hand_camera_rgb" in f else None,
            "first": f["observations/first_person_camera_rgb"][:] if "observations/first_person_camera_rgb" in f else None,
            "seed": int(meta["seed"]),
            "band": str(meta["band"]) if "band" in meta else str(meta.get("difficulty", "unknown")),
            "success": int(meta["success"]),
            "n_frames": int(meta["n_frames"]),
        }
    return ep


def main():
    episodes = collect_episodes()
    if not episodes:
        print(f"NO SUCCESSFUL EPISODES FOUND in {RAW_ROOT}")
        sys.exit(1)
    print(f"Found {len(episodes)} successful episodes:")
    for band, eid, p in episodes:
        print(f"  {band}/episode_{eid} <- {p.name}")

    first = load_episode(episodes[0][2])
    state_dim = first["states"].shape[1]
    action_dim = first["actions"].shape[1]
    img_shape = tuple(first["first"].shape[1:])  # (480, 640, 3)
    print(f"Schema: state_dim={state_dim}, action_dim={action_dim}, img_shape={img_shape}")
    assert state_dim == 16 and action_dim == 12, f"expected 16/12, got {state_dim}/{action_dim}"

    valid = []
    for band, eid, p in episodes:
        ep = load_episode(p)
        ok = (ep["n_frames"] > 0 and ep["success"] == 1
              and ep["left"] is not None and ep["right"] is not None and ep["first"] is not None)
        if not ok:
            print(f"  SKIP {band}/episode_{eid}: n_frames={ep['n_frames']} success={ep['success']} "
                  f"left={ep['left'] is not None} right={ep['right'] is not None} first={ep['first'] is not None}")
            continue
        valid.append((band, eid, p, ep))
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
        repo_id="policy_demos_v3",
        fps=FPS,
        features=features,
        root=OUT_ROOT,
        robot_type="double_piper",
        use_videos=False,
    )
    print(f"Created LeRobotDataset at {OUT_ROOT}")

    ep_records = []
    for ep_idx, (band, eid, p, ep) in enumerate(valid):
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
        rec = {"episode_index": ep_idx, "band": band, "seed": ep["seed"],
               "episode_id": eid, "n_frames": n, "success": ep["success"]}
        ep_records.append(rec)
        print(f"  saved ep{ep_idx}: {band} seed={ep['seed']} n_frames={n}")

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
        "distribution": {b: sum(1 for r in ep_records if r["band"] == b) for b in sorted({r["band"] for r in ep_records})},
        "episodes": ep_records,
        "schema_source": "matches LightwheelAI/Lightwheel-Tasks-Double-Piper meta/info.json + smolvla-double-piper-pnp config.json",
        "fine_tune_target": "LightwheelAI/smolvla-double-piper-pnp",
        "demo_source": "SmolVLA closed-loop self-filtered (TASK_SUCCESS=True only)",
        "storage": "image (PNG), use_videos=False",
    }
    manifest_path = OUT_ROOT.parent / "policy_demos_v3_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {manifest_path}")
    print("Distribution:", json.dumps(manifest["distribution"]))


if __name__ == "__main__":
    main()
