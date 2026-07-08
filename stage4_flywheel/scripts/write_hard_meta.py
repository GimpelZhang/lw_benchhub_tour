#!/usr/bin/env python3
"""§5.7: record hard-scene metadata for Phase 3 (curriculum generation consumes this)."""
import json, pathlib
probe = json.loads(pathlib.Path("/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json").read_text())
meta = {
  "task": "L90K1PutTheBlackBowlOnThePlate", "robot": "DoublePiper-Abs", "layout": "libero-1-1",
  "hard_scene_yml": "/mnt/robot/stage4_flywheel/configs/hard_scene.yml",
  "hard_seed": probe["best_seed"],
  "akita_black_bowl_world": probe["best"]["bowl_world"],
  "robot_base_world": probe["best"]["robot_world"],
  "dist_to_robot_m": probe["best"]["dist_to_robot"],
  "baseline_metrics": "/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_metrics.json",
  "head_video": "/mnt/robot/stage4_flywheel/videos/hard_scene_head_view.mp4",
  "head_frame0": "/mnt/robot/stage4_flywheel/videos/hard_scene_frame0.png",
}
pathlib.Path("/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_meta.json").write_text(
    json.dumps(meta, indent=2), encoding="utf-8")
print(json.dumps(meta, indent=2))
