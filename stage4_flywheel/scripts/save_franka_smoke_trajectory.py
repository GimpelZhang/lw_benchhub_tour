#!/usr/bin/env python3
"""Phase 4 T1: AutoDataGen+cuRobo link-proof smoke (FrankaCubeLift).
Boots Isaac Sim, runs FrankaCubeLiftPipeline, persists trajectories as .npz + manifest."""
import argparse, json, sys
from pathlib import Path
import numpy as np, torch
sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim")
sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim_examples")
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--pipeline_id", type=str, default="AutoSimPipeline-FrankaCubeLift-v0")
parser.add_argument("--num_runs", type=int, default=3)
parser.add_argument("--out_dir", type=str, default="/mnt/robot/stage4_flywheel/datasets/franka_cube_lift_smoke")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(vars(args)).app
import autosim_examples  # noqa: F401
from autosim import make_pipeline
out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
pipeline = make_pipeline(args.pipeline_id)
manifest = {"pipeline_id": args.pipeline_id, "runs": []}
for i in range(args.num_runs):
    o = pipeline.run()
    try:
        actions = torch.stack(o.generated_actions, dim=0).detach().cpu().numpy()  # [T,1,action_dim]
    except Exception as e:
        actions = np.asarray([a.detach().cpu().numpy() for a in o.generated_actions])
    p = out / f"run_{i+1:02d}_actions.npz"
    np.savez_compressed(p, actions=actions, success=bool(o.success))
    manifest["runs"].append({"run": i+1, "success": bool(o.success), "path": str(p),
                             "steps": int(actions.shape[0])})
    print(f"run {i+1}: success={o.success} steps={actions.shape[0]}", flush=True)
(out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Saved smoke trajectories to {out}")
app.close()
