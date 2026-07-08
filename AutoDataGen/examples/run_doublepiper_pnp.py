"""Script to run the DoublePiper kitchen PnP pipeline.

Uses a single AppLauncher created up-front and reuses it across all runs to
avoid the double-AppLauncher crash with lw_benchhub's export_env_for_envhub.
"""

import argparse
from pathlib import Path

from isaaclab.app import AppLauncher

# NOTE: conda 25's cuda-nvcc activate script references unbound NVCC_PREPEND_FLAGS;
# if this script is invoked with `set -u`, source the environment scripts with care.

parser = argparse.ArgumentParser(description="run DoublePiper kitchen PnP pipeline.")
parser.add_argument(
    "--pipeline_id",
    type=str,
    default="AutoSimPipeline-DoublePiperKitchenPnp-v0",
    help="Name of the autosim pipeline.",
)
parser.add_argument(
    "--config_path",
    type=str,
    required=True,
    help="Path to the lw_benchhub envhub YAML scene config.",
)
parser.add_argument(
    "--output_dir",
    type=str,
    default="/mnt/robot/stage4_flywheel/demos",
    help="Directory for head-view media artifacts.",
)
parser.add_argument(
    "--num_runs",
    type=int,
    default=1,
    help="Number of times to run the pipeline.",
)

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher_args = vars(args_cli)

# launch omniverse app
app_launcher = AppLauncher(app_launcher_args)
simulation_app = app_launcher.app

import sys
sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim")
sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim_examples")
import autosim_examples  # noqa: F401
from autosim import make_pipeline


def main():
    for i in range(args_cli.num_runs):
        print(f"====== run {i + 1}/{args_cli.num_runs} ======")
        pipeline = make_pipeline(
            args_cli.pipeline_id,
            config_path=args_cli.config_path,
            output_dir=args_cli.output_dir,
        )
        pipeline._app_launcher_ref = app_launcher
        pipeline._scene_label = Path(args_cli.config_path).stem
        pipeline._run_id = i + 1
        pipeline.run()


if __name__ == "__main__":
    main()
